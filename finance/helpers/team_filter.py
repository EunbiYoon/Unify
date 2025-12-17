from django.db.models import (
    Q, Case, When, Value, IntegerField, QuerySet, Max
)
from copy import deepcopy
import logging

from finance.schemas import TeamPrediction_Out, SapProcessed_Out
from ninja.errors import HttpError

logger = logging.getLogger(__name__)


# =========================================================
# 공통: 사용자 권한 기반 팀 필터
# =========================================================
def _common_filter(model, qs, user):
    """
    반환값:
    - admin: QuerySet[Team]
    - 그 외: List[str] (team_name 리스트)
    """
    team_names = []

    user_role = getattr(user, "role", None)
    role_name = getattr(user_role, "role_name", "")
    user_team = getattr(user, "team", None)
    user_group = getattr(user, "group", None)
    user_division = getattr(user, "division", None)

    # 🤍 어드민
    if role_name in ["site-admin", "finance-admin"] or user.is_superuser:
        return qs

    # 🟡 팀장
    if role_name == "team-leader" and user_team:
        team_names = [user_team.team_name]

    # 🔵 그룹장
    elif role_name == "group-leader" and user_group:
        team_names = list(
            model.objects
            .filter(group_parent=user_group)
            .values_list("team_name", flat=True)
        )

    # 🟣 디비전장
    elif role_name == "division-leader" and user_division:
        team_names = list(
            model.objects
            .filter(division_parent=user_division)
            .values_list("team_name", flat=True)
        )

    logger.info("🟢 필터할 팀 이름 리스트: %s", team_names)
    return team_names


# =========================================================
# TeamPrediction 규칙 Q 생성
# =========================================================
def _pred_team(Team, TeamPrediction, request):
    filtered_team = _common_filter(
        model=Team,
        qs=Team.objects.all(),
        user=request.user
    )

    # 팀 id 정규화
    if isinstance(filtered_team, QuerySet):
        team_ids = list(filtered_team.values_list("id", flat=True))
    else:
        if filtered_team and isinstance(filtered_team[0], str):
            team_ids = list(
                Team.objects
                .filter(team_name__in=filtered_team)
                .values_list("id", flat=True)
            )
        else:
            team_ids = [t.id for t in filtered_team] if filtered_team else []

    if not team_ids:
        return Q(pk__isnull=True)  # 항상 false

    rule_q = (
        Q(shared_team__isnull=False) & (
            Q(operation_team_id__in=team_ids, shared_dominate=True) |
            Q(shared_team_id__in=team_ids,   shared_dominate=False)
        )
    ) | (
        Q(shared_team__isnull=True) & Q(operation_team_id__in=team_ids)
    )

    return rule_q


# =========================================================
# SQLite/Postgres 공통: SAP 최신 배치 id 목록 만들기
# =========================================================
def _latest_sap_ids(SapProcessed, team_ids=None, year=None):
    """
    (operation_team_id, project_code, year) 별로 category=SAP 최신 batch_no의 id들을 뽑는다.
    SQLite/PG 모두 안정적으로 동작하도록 2단계로 처리:
    1) 그룹별 max(batch_no) 집계
    2) 그 max(batch_no)에 해당하는 row 중 id max로 최종 선택
    """
    base = SapProcessed.objects.filter(category__iexact="SAP")
    if team_ids is not None:
        base = base.filter(operation_team_id__in=team_ids)
    if year is not None:
        base = base.filter(year=year)

    # 1) 그룹별 max(batch_no)
    groups = (
        base.values("operation_team_id", "project_code", "year")
        .annotate(max_batch=Max("batch_no"))
    )

    if not groups:
        return []

    # 2) 각 그룹의 max_batch에 해당하는 row들 중 가장 큰 id 선택
    #    (DB마다 tie-break 다를 수 있어서 id max로 통일)
    latest_ids = []
    for g in groups:
        row = (
            base.filter(
                operation_team_id=g["operation_team_id"],
                project_code=g["project_code"],
                year=g["year"],
                batch_no=g["max_batch"],
            )
            .order_by("-id")
            .values_list("id", flat=True)
            .first()
        )
        if row:
            latest_ids.append(row)

    return latest_ids


# =========================================================
# SapProcessed 메인 필터
# =========================================================
def _process_team(Team, SapProcessed, request, SapProcessed_Out):
    if not request.user.is_authenticated:
        raise HttpError(401, "로그인이 필요합니다.")

    role_name = getattr(getattr(request.user, "role", None), "role_name", "")

    # ✅ site-admin / superuser: 필터 없이 전부 출력 (요구사항)
    if role_name == "site-admin" or request.user.is_superuser:
        qs = (
            SapProcessed.objects
            .select_related("operation_team")
            .order_by("-created_at")
        )
        logger.warning("🔥 ADMIN BYPASS: 전체 반환 count=%s", qs.count())
        return qs

    # ✅ finance-admin: (Adjust 전체 + SAP 최신만) 유지하고 싶으면 아래 사용
    #    아니면 site-admin처럼 전체로 바꿔도 됨
    if role_name == "finance-admin":
        latest_ids = _latest_sap_ids(SapProcessed)
        qs = (
            SapProcessed.objects
            .select_related("operation_team")
            .filter(Q(category__iexact="Adjust") | Q(id__in=latest_ids))
            .annotate(
                _prio=Case(
                    When(category__iexact="Adjust", then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("_prio", "operation_team_id", "-created_at")
        )
        logger.info("🔵 finance-admin 결과 수: %s", qs.count())
        return qs

    # =====================================================
    # 일반 사용자
    # =====================================================
    filtered_team = _common_filter(
        model=Team,
        qs=Team.objects.all(),
        user=request.user
    )

    # 팀 id 정규화
    if isinstance(filtered_team, QuerySet):
        team_ids = list(filtered_team.values_list("id", flat=True))
    else:
        if filtered_team and isinstance(filtered_team[0], str):
            team_ids = list(
                Team.objects
                .filter(team_name__in=filtered_team)
                .values_list("id", flat=True)
            )
        else:
            team_ids = [t.id for t in filtered_team] if filtered_team else []

    if not team_ids:
        logger.warning("⚠️ team_ids empty -> [] 반환")
        return []

    # SAP 최신 id (해당 팀 범위 내)
    latest_ids = _latest_sap_ids(SapProcessed, team_ids=team_ids)

    qs = (
        SapProcessed.objects
        .select_related("operation_team")
        .filter(operation_team_id__in=team_ids)
        .filter(Q(category__iexact="Adjust") | Q(id__in=latest_ids))
        .annotate(
            _prio=Case(
                When(category__iexact="Adjust", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("_prio", "operation_team_id", "-created_at")
    )

    logger.info("🔵 user 결과 수: %s", qs.count())

    # =====================================================
    # flag=closed 덮어쓰기 (응답용)
    # =====================================================
    out = []
    for obj in qs:
        original_md = obj.monthly_data
        md = original_md.model_dump() if hasattr(original_md, "model_dump") else original_md
        md_copy = deepcopy(md)

        for v in md_copy.values():
            if isinstance(v, dict):
                v["flag"] = "closed"

        obj.monthly_data = md_copy
        out.append(SapProcessed_Out.model_validate(obj, from_attributes=True))
        obj.monthly_data = original_md

    return out


# =========================================================
# TeamPrediction + SapProcessed 병합 조회
# =========================================================
def _merge_team(
    Team, TeamPrediction, SapProcessed,
    year, division, group, team,
    team_name_combined, request
):
    team_name_combined = None
    if division and group and team:
        team_name_combined = f"SS-{division}-{group}-{team}".strip()

    # -------------------------
    # TeamPrediction
    # -------------------------
    rule_q = Q()
    if team_name_combined:
        rule_q = (
            Q(shared_team__isnull=False) & (
                Q(operation_team__team_name=team_name_combined, shared_dominate=True) |
                Q(shared_team__team_name=team_name_combined,   shared_dominate=False)
            )
        ) | (
            Q(shared_team__isnull=True) & Q(operation_team__team_name=team_name_combined)
        )

    tp_filters = Q(status="Progress")

    if team_name_combined:
        tp_filters &= (
            Q(operation_team__team_name=team_name_combined) |
            Q(shared_team__team_name=team_name_combined)
        )
    if division:
        tp_filters &= Q(operation_team__division_parent__division_name__icontains=division)
    if group:
        tp_filters &= Q(operation_team__group_parent__group_name__icontains=group)
    if year:
        tp_filters &= Q(year=year)

    final_q = tp_filters & rule_q if team_name_combined else tp_filters

    tp_qs = (
        TeamPrediction.objects
        .select_related("operation_team", "shared_team")
        .filter(final_q)
        .order_by("-created_at")
        .distinct()
    )

    # -------------------------
    # SapProcessed (Adjust 전체 + SAP 최신만)
    # -------------------------
    sp_filters = Q()
    if team_name_combined:
        sp_filters &= Q(operation_team__team_name=team_name_combined)
    if division:
        sp_filters &= Q(operation_team__division_parent__division_name__icontains=division)
    if group:
        sp_filters &= Q(operation_team__group_parent__group_name__icontains=group)
    if year:
        sp_filters &= Q(year=year)

    latest_ids = _latest_sap_ids(SapProcessed, year=year)

    sp_qs = (
        SapProcessed.objects
        .select_related("operation_team")
        .filter(sp_filters)
        .filter(Q(category__iexact="Adjust") | Q(id__in=latest_ids))
        .annotate(
            _prio=Case(
                When(category__iexact="Adjust", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("_prio", "operation_team__team_name", "-created_at")
    )

    return tp_qs, sp_qs
