# 맨 위 import 근처에 추가
import re
from typing import Union
import os
import sys
import django
from django.db import transaction, connection

# ✅ 1) Django 초기화
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# ✅ 2) 모델 import
from finance.models import CctrRaw, CctrProcessed
from account.models import Division, Group, Team  # Team: team_name, code, group_parent, division_parent, batch_no
from django.db import connections
from django.apps import apps
import logging
logger = logging.getLogger(__name__)

from finance.utils.process_dbid import reset_pk_sequence_safely

# ✅ 추가: 배치넘버 추출 헬퍼 (예: ..._20250804194333.xlsx 에서 14자리 추출)
BATCH_RE = re.compile(r'(\d{14})')

# ---------- 유틸 ----------
def normalize_team_name(raw: str) -> str:
    if not raw:
        return ""
    return "-".join(raw.strip().split())

def upsert_team(team_name: str, code_str: str, div_instance, group_instance, team_cache, batch_no: int):
    """
    Team 업서트:
      1) team_name으로 검색 → 없으면 code로 역검색 -> 없으면 생성
    - 이름/코드/부모 연결 변경이 발생한 경우에만 batch_no 갱신
    - 반환: (team_obj, changed_flag)
    """
    changed = False
    # 1) team_name or code 역검색 -> 해당하는 인스턴스 생성 
    team = Team.objects.filter(team_name=team_name).first()
    if team is None and code_str:
        team = Team.objects.filter(code=code_str).first()
    if team is None:
        # ✅ 생성 시엔 batch_no 포함
        team = Team.objects.create(
            team_name=team_name,
            code=code_str,
            division_parent=div_instance,
            group_parent=group_instance,
            batch_no=batch_no,
        )
        changed = True
    # else:
    #     fields_to_update = []
    #     if team.team_name != team_name and team_name:
    #         team.team_name = team_name
    #         fields_to_update.append("team_name")
    #     if code_str and team.code != code_str:
    #         team.code = code_str
    #         fields_to_update.append("code")
    #     if team.division_parent_id != (div_instance.id if div_instance else None):
    #         team.division_parent = div_instance
    #         fields_to_update.append("division_parent")
    #     if team.group_parent_id != (group_instance.id if group_instance else None):
    #         team.group_parent = group_instance
    #         fields_to_update.append("group_parent")

    #     # ✅ 실제 업데이트가 발생한 경우에만 batch_no 갱신 (+ 새 배치가 더 최신이면 갱신)
    #     if fields_to_update:
    #         try:
    #             cur_bn = int(team.batch_no) if team.batch_no is not None else None
    #             new_bn = int(batch_no) if batch_no is not None else None
    #         except (TypeError, ValueError):
    #             cur_bn, new_bn = team.batch_no, batch_no  # 포맷 이슈 시 보수적으로 유지

    #         if new_bn is not None and (cur_bn is None or new_bn > cur_bn):
    #             team.batch_no = batch_no
    #             fields_to_update.append("batch_no")

    #         team.save(update_fields=fields_to_update)
    #         changed = True

    return team, changed


def _extract_batch_no(arg: Union[str, int]) -> int:
    if isinstance(arg, int):
        return arg
    if isinstance(arg, str):
        m = BATCH_RE.search(arg)
        if m:
            return int(m.group(1))
    raise ValueError(f"유효한 batch_no를 찾을 수 없습니다: {arg!r}")


def ensure_division_group(team_name: str):
    """
    team_name 예: 'PTK-TDD-MTG-Team1'
      - Division: 앞 2 파트 (예: 'PTK-TDD', 파트가 2개 미만이면 None 허용)
      - Group   : 앞 3 파트 (예: 'PTK-TDD-MTG', 파트가 3개 미만이면 None 허용)
    """
    # parts 만들 때부터 정규화: 하이픈/엔대시/엠대시 전부 구분자, 공백 제거, 빈 조각 제거
    parts = [p.strip() for p in re.split(r"[-–—]+", team_name) if p and p.strip()]
    div_instance = None
    group_instance = None

    if len(parts) >= 2:
        division_name = "-".join(parts[:2])
        div_instance, _ = Division.objects.get_or_create(division_name=division_name)

    if len(parts) >= 3:
        third = parts[2]
        # 영문자만 남기고 비교(괄호/숫자/공백 제거) → 'Team5(C)' -> 'Team'
        third_alpha = re.sub(r"[^A-Za-z]", "", third).lower()
        if "team" in third_alpha:
            # ✅ "PTK-CMG-Team5(C)" 같은 케이스는 여기로 들어와서 스킵
            pass
        else:
            group_name = "-".join(parts[:3])
            group_instance, _created = Group.objects.get_or_create(
                group_name=group_name,
                defaults={"division_parent": div_instance},
            )
            if group_instance and group_instance.division_parent != div_instance:
                group_instance.division_parent = div_instance
                group_instance.save(update_fields=["division_parent"])
    return div_instance, group_instance


def process_cctr(arg: Union[str, int]) -> dict:
    """뷰/내부에서 직접 호출: 경로(str) 또는 정수 batch_no 둘 다 허용"""
    batch_no = _extract_batch_no(arg)
    logger.info("✅ 전달받은 batch_no: %s", batch_no)

    # ↓↓↓ 기존 __main__ 로직을 여기로 이동 (sys.exit 사용 금지)
    # --- 여기부터 기존 로직 붙여넣기 ---
    cctr_filtered = (
        CctrRaw.objects.filter(batch_no=batch_no)
        .exclude(sales_office_cd__isnull=True)
        .exclude(sales_office_cd="")
        .exclude(name_20__iregex=r'\(\s*(?:c|closed|tbc)\s*\)')
    )

    source_count = cctr_filtered.count()
    if source_count == 0:
        logger.warning("[CCTR] 해당 배치 번호에 유효한 CctrRaw 데이터가 없습니다. batch_no=%s", batch_no)
        return {"source_count": 0, "saved": 0, "deleted": 0, "batch_no": batch_no}

    records = []
    team_cache = {}
    deleted = 0

    seen = set()  # (code, team_name, batch_no) 로 권장
    for obj in cctr_filtered.select_related(None):
        raw_team_name = getattr(obj, "name_20", "") or ""
        team_name = normalize_team_name(raw_team_name)
        if not team_name:
            logger.warning("[CCTR] 팀 이름이 비어 스킵: id=%s", getattr(obj, "id", None))
            continue

        code = (obj.sales_office_cd or "").strip()
        try:
            div_instance, group_instance = ensure_division_group(team_name)
            # FK null 방어(필요시)
            if div_instance is None or group_instance is None:
                logger.error("[CCTR] 부모 FK 누락 스킵 | team_name=%s div=%s group=%s",
                                team_name, div_instance, group_instance)
                continue

            team_instance, _changed = upsert_team(
                team_name, code, div_instance, group_instance, team_cache, batch_no
            )

            key = (code, team_instance.team_name, batch_no)  # ✅ 배치 포함
            if key in seen:
                continue
            seen.add(key)

            records.append(
                CctrProcessed(
                    code=code,
                    team_name=team_instance.team_name,
                    batch_no=batch_no,
                    division_parent=div_instance,
                    group_parent=group_instance,
                )
            )
        except Exception:
            logger.exception("[CCTR] 레코드 처리 실패 | raw_id=%s team='%s' code='%s'",
                                getattr(obj, "id", None), team_name, code)
            continue

    deleted, _ = CctrProcessed.objects.filter(batch_no=batch_no).delete()
    logger.info("[CCTR] 🧹 기존 CctrProcessed 삭제: %s건 (batch_no=%s)", deleted, batch_no)

    reset_pk_sequence_safely(CctrProcessed, alias="default")

    saved = 0
    if records:
        CctrProcessed.objects.bulk_create(records, ignore_conflicts=False)
        saved = len(records)
        logger.info("[CCTR] 📊원천: %s | ✅저장: %s (batch_no=%s)", source_count, saved, batch_no)
    else:
        logger.info("[CCTR] 저장할 레코드가 없습니다. (batch_no=%s)", batch_no)

    return {"source_count": source_count, "saved": saved, "deleted": deleted, "batch_no": batch_no}


# 스크립트가 직접 실행된 경우 테스트 실행
if __name__ == "__main__":
    process_cctr("tmp/cctr_20250908083453.xlsx")  # 지정된 엑셀 파일로 테스트 실행
