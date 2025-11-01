
from django.db.models import Q, Case, When, Value, IntegerField, Subquery, OuterRef, Max, QuerySet
from copy import deepcopy
from finance.schemas import (
    TeamPrediction_Out
)

import logging
logger = logging.getLogger(__name__)


def _common_filter(model, qs, user):
    user_role = getattr(user, "role", None)
    role_name = getattr(user_role, "role_name", "")
    user_team = getattr(user, "team", None)
    user_group = getattr(user, "group", None)
    user_division = getattr(user, "division", None)

    # 🤍 어드민
    if role_name in ["site-admin", "finance-admin"] or user.is_superuser:
        return qs  # 전체 권한

    # 🟡 팀장
    elif role_name == "team-leader" and user_team:
        team_names = [user_team.team_name]

    # 🔵 그룹장
    elif role_name == "group-leader" and user_group:
        team_names = list(
            model.objects.filter(group_parent=user_group).values_list("team_name", flat=True)
        )

    # 🟣 디비전장
    elif role_name == "division-leader" and user_division:
        team_names = list(
            model.objects.filter(division_parent=user_division).values_list("team_name", flat=True)
        )

    logger.info("🟢 필터할 팀 이름 리스트: %s", team_names)
    return team_names


def _pred_team(Team, TeamPrediction, request):
    # 0) 사용자 권한 기반 팀 필터링
    filtered_team = _common_filter(
        model=Team, qs=Team.objects.all(), user=request.user
    )

    # 1) 팀 id 리스트로 정규화
    if isinstance(filtered_team, QuerySet):
        team_ids = list(filtered_team.values_list("id", flat=True))
        team_count = filtered_team.count()
    else:
        if filtered_team and isinstance(filtered_team[0], str):
            team_ids = list(
                Team.objects.filter(team_name__in=filtered_team)
                .values_list("id", flat=True)
            )
        else:
            team_ids = [t.id for t in filtered_team] if filtered_team else []
        team_count = len(team_ids)
    logger.info("✅ 대상 팀 수: %s", filtered_team)
    logger.info("✅ 대상 팀 수: %s", team_count)

    if not team_ids:
        return []

    # 2) 규칙 (shared_team 있는 경우를 먼저 배치)
    #   - shared_team 있음 + 내가 운영팀: shared_dominate=True
    #   - shared_team 있음 + 내가 협업팀: shared_dominate=False
    #   - shared_team 있음 + 내가 운영팀 & 협업팀: 둘다 보이기
    #   - shared_team 없음: 내가 운영팀이면 포함

    rule_q = (
        Q(shared_team__isnull=False) & (
            Q(operation_team_id__in=team_ids, shared_dominate=True) |
            Q(shared_team_id__in=team_ids,   shared_dominate=False)
        )
    ) | (
        Q(shared_team__isnull=True) & Q(operation_team_id__in=team_ids)
    )
    
    return rule_q


def _process_team(Team, SapProcessed, request, SapProcessed_Out):
    # ✅ operation_team, project_code별 최신 '결산' 배치 번호
    recent_batch_per_project = (
        SapProcessed.objects
        .filter(category__iexact="결산", operation_team=OuterRef("operation_team"), project_code=OuterRef("project_code"), year=OuterRef("year"))
        .order_by("-batch_no")
        .values("id")[:1] #배치가 같은 것중에서는 id가 높은것
    )

    if not request.user.is_authenticated:
        raise HttpError(401, "로그인이 필요합니다.")

    # 사용자롤
    role_name = getattr(getattr(request.user, "role", None), "role_name", "")
    if role_name in ("finance-admin", "site-admin"):
        # ✅ 팀 기준 SapProcessed 조회
        qs = (
            SapProcessed.objects
            .filter(
                Q(category__iexact="조정") |
                (Q(category__iexact="결산") & Q(id=recent_batch_per_project))
            )
            .annotate(
                _prio=Case(
                    When(category__iexact="조정", then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                )
            )
            .order_by("_prio", "operation_team", "-created_at")  # ✅ 조정 먼저, 그 다음 실적
        )
        logger.info("🔵 필터된 결과 수: %s", qs.count())
    else:
        # ✅ 사용자 권한에 따른 대상 팀 필터링
        filtered_team = _common_filter(
            model=Team, qs=Team.objects.all(), user=request.user
        )

        # ✅ 팀 id 리스트 정규화
        if isinstance(filtered_team, QuerySet):
            team_ids = list(filtered_team.values_list("id", flat=True))
            team_count = filtered_team.count()
        else:
            if filtered_team and isinstance(filtered_team[0], str):
                team_ids = list(
                    Team.objects.filter(team_name__in=filtered_team)
                    .values_list("id", flat=True)
                )
            else:
                team_ids = [t.id for t in filtered_team]  # list[Team]
            team_count = len(team_ids)

        logger.info("✅ 대상 팀 수: %s", team_count)
        if not team_ids:
            return []

        # ✅ 팀 기준 SapProcessed 조회
        qs = (
            SapProcessed.objects
            .select_related("operation_team")
            .filter(Q(operation_team_id__in=team_ids))
            .filter(
                Q(category__iexact="조정") |
                (Q(category__iexact="결산") & Q(id=recent_batch_per_project))
            )
            .annotate(
                _prio=Case(
                    When(category__iexact="조정", then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                )
            )
            .order_by("_prio", "operation_team", "-created_at")  # ✅ 조정 먼저, 그 다음 실적
        )
        logger.info("🔵 필터된 결과 수: %s", qs.count())

    # ✅ finance-admin or site-admin 이외 사용자에겐 응답에서만 flag=closed로 덮어쓰기 (DB 미변경)
    out = []

    if role_name not in ("finance-admin", "site-admin"):
        for obj in qs:
            original_md = obj.monthly_data
            md = original_md.model_dump() if hasattr(original_md, "model_dump") else original_md
            md_copy = deepcopy(md)

            for k, v in md_copy.items():
                if isinstance(v, dict):
                    v["flag"] = "closed"

            # 직렬화용으로만 바꿔치기 → save() 호출 없음 → DB 영향 없음
            obj.monthly_data = md_copy
            out.append(SapProcessed_Out.model_validate(obj, from_attributes=True))
            obj.monthly_data = original_md  # 원복
        return out
    return qs


def _merge_team(Team, TeamPrediction, SapProcessed, year, division, group, team, team_name_combined, request):
    # ------------------------
    # TeamPrediction 필터
    # ------------------------
    team_name_combined = None
    if division and group and team:
        team_name_combined = f"PTK-{division}-{group}-{team}".strip()

    # ------------------------
    # TeamPrediction 필터
    # ------------------------
    # 1) rule_q: 팀 ID + shared_dominate 규칙 기반 필터 (team_ids가 있는 경우만 적용)
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

    # 2) tp_filters: 조직/이름/연도/상태 등 일반 조건
    tp_filters = Q()
    if team_name_combined:
        tp_filters &= (
            Q(operation_team__team_name=team_name_combined) |
            Q(shared_team__team_name=team_name_combined)
        )
    if division:
        tp_filters &= (
            Q(operation_team__division_parent__division_name__icontains=division) |
            Q(shared_team__division_parent__division_name__icontains=division)
        )
    if group:
        tp_filters &= (
            Q(operation_team__group_parent__group_name__icontains=group) |
            Q(shared_team__group_parent__group_name__icontains=group)
        )
    if year:
        tp_filters &= Q(year=year)
    # 상태는 Progress 고정
    tp_filters &= Q(status="Progress")

    # 3) 최종 Q: team_ids가 있으면 rule_q까지 AND, 없으면 tp_filters만
    final_q = tp_filters & rule_q if team_name_combined else tp_filters

    # 4) 쿼리셋
    tp_qs = (
        TeamPrediction.objects
        .select_related("operation_team", "shared_team")
        .filter(final_q)
        .order_by("-created_at")   # created_at 최신 우선
        .distinct()                # 중복 제거(필요시 distinct 필드 지정 고려)
    )

    # ------------------------
    # SapProcessed 필터 (+ 조정 우선)
    # ------------------------
    # ✅ operation_team, project_code별 최신 '결산' 배치 번호
    recent_batch_per_project = (
        SapProcessed.objects
        .filter(category__iexact="결산", operation_team=OuterRef("operation_team"), project_code=OuterRef("project_code"), year=OuterRef("year"))
        .order_by("-batch_no")
        .values("id")[:1] #배치가 같은 것중에서는 id가 높은것
    )

    sp_filters = Q()
    if team_name_combined:
        sp_filters &= Q(operation_team__team_name=team_name_combined)
    if division:
        sp_filters &= Q(operation_team__division_parent__division_name__icontains=division)
    if group:
        sp_filters &= Q(operation_team__group_parent__group_name__icontains=group)
    if year:
        sp_filters &= Q(year=year)

    sp_qs = (
        SapProcessed.objects
        .select_related("operation_team")
        .filter(sp_filters)
        .filter(  # ✅ 조정 전체 + 결산은 최신 배치만
            Q(category__iexact="조정") |
            (Q(category__iexact="결산") & Q(id=Subquery(recent_batch_per_project)))
        )
        .annotate(
            _prio=Case(
                When(category__iexact="조정", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("_prio", "operation_team__team_name", "-created_at")
    )

    return tp_qs, sp_qs