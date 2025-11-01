#!/usr/bin/env python3
import os
import sys
import re
import logging
from typing import Union
from datetime import datetime

import django
import pandas as pd
from django.contrib.auth import get_user_model
from django.db import transaction, connection, models
from django.db.models import Q

# =========================
# Django 초기화
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# =========================
# 모델/유틸 import
# =========================
from finance.models import SapRaw, GateProcessed, RaKey, SapProcessed, PredictionClose  # ← PredictionClose 포함
from account.models import Team  
from finance.utils.sap_pivot import MONTH_KEYS  
from finance.utils import sap_pivot
from finance.utils import sap_close

# =========================
# 로깅
# =========================
import logging
logger = logging.getLogger(__name__)

# =========================
# 헬퍼
# =========================
BATCH_RE = re.compile(r"(\d{14})")  # 예: ..._20250804194333.xlsx

def _extract_batch_no(arg: Union[str, int]) -> int:
    """
    경로 문자열/숫자에서 배치넘버(14자리) 추출. 숫자만 온 경우도 허용.
    """
    if isinstance(arg, int):
        return arg
    if isinstance(arg, str):
        m = BATCH_RE.search(arg)
        if m:
            return int(m.group(1))
        if arg.isdigit():
            return int(arg)
    raise ValueError(f"유효한 batch_no를 찾을 수 없습니다: {arg!r}")

        
def normalize_batch_for_model(model, batch_no):
    """
    모델의 batch_no 필드 타입에 맞춰 저장형을 정규화
    - IntegerField → int
    - Char/Text    → str
    """
    f = model._meta.get_field("batch_no")
    return int(batch_no) if isinstance(f, models.IntegerField) else str(batch_no).strip()

def _closing_flags(post_flag: str = "closed") -> dict | None:
    """
    PredictionClose 최신값 기준 flag 맵 생성
    - 1~마감월: hidden
    - (마감월+1)~12월: post_flag ('closed' 권장)
    PredictionClose 없으면 None 반환
    """
    latest = PredictionClose.objects.order_by("-year", "-month").first()
    if not latest:
        return None
    closing_month = int(latest.month)
    flags = {}
    for idx, key in enumerate(MONTH_KEYS, start=1):
        flags[key] = {"flag": "hidden" if idx <= closing_month else post_flag}
    return flags

# =========================
# 메인 진입 함수 (뷰/내부에서 직접 호출)
# =========================
def process_sap(gate_arg: Union[str, int], sap_arg: Union[str, int], username: str) -> dict:
    """
    SapRaw(sap_batch) → SapProcessed 적재 (GateProcessed(gate_batch)와 조인)
    - gate_arg, sap_arg: 경로 문자열 또는 정수 batch_no
    - username         : SapProcessed.owner 로 저장할 사용자
    return: {
      'success': bool,
      'message': str,
      'rows_total': int,
      'rows_saved': int,
      'rows_deleted': int,
      'batch_no': int,
      'miss_team': int,
      'miss_gate': int,
      'miss_monthly': int,
      'errors': list[dict]
    }
    예외는 호출부에서 잡아서 처리하도록 그대로 전파한다.
    """
    errors = []

    # 1) 배치 파싱
    gate_batch_raw = _extract_batch_no(gate_arg)
    sap_batch_raw  = _extract_batch_no(sap_arg)

    # 2) 소유자 확인
    User = get_user_model()
    owner = User.objects.get(username=username)  # 없으면 DoesNotExist 발생 (뷰에서 잡으세요)

    logger.info("[SAP] gate_batch=%r, sap_batch=%r, owner=%s", gate_batch_raw, sap_batch_raw, username)

    # 3) 필수 마스터 체크
    if not RaKey.objects.exists():
        raise RuntimeError("[SAP] RaKey 데이터가 없습니다. 먼저 RaKey 업로드가 필요합니다.")

    # 4) SapRaw 로드 (sap_batch: int/str/iexact 모두 시도)
    sap_q = Q(batch_no=sap_batch_raw) | Q(batch_no=str(sap_batch_raw)) | Q(batch_no__iexact=str(sap_batch_raw))
    sap_raw_qs = SapRaw.objects.filter(sap_q)
    sap_raw_df = pd.DataFrame(list(sap_raw_qs.values()))
    if sap_raw_df.empty:
        logger.warning("[SAP] SapRaw 없음 | sap_batch=%r", sap_batch_raw)
        return {
            "success": True,
            "message": f"[SAP] SapRaw 없음 | sap_batch={sap_batch_raw}",
            "rows_total": 0, "rows_saved": 0,
            "rows_deleted": 0,
            "batch_no": sap_batch_raw,
            "miss_team": 0,
            "miss_gate": 0,
            "miss_monthly": 0,
            "errors": [],
        }
    logger.info("[SAP] SapRaw 로드: %s건", len(sap_raw_df))

    # 5) 월별 JSON 맵 생성 (12개월 모두 채움, flag 규칙 포함)
    monthly_map = sap_pivot.main()
    
    # 6) GateProcessed 로드 (gate_batch: 혼용 대비)
    gate_q = Q(batch_no=gate_batch_raw) | Q(batch_no=str(gate_batch_raw)) | Q(batch_no__iexact=str(gate_batch_raw))
    gate_df = pd.DataFrame(list(GateProcessed.objects.filter(gate_q).values("job", "job_name", "ra_key")))
    if gate_df.empty:
        logger.warning("[SAP] GateProcessed 없음 | gate_batch=%r", gate_batch_raw)
        return {
            "success": True,
            "message": f"[SAP] GateProcessed 없음 | gate_batch={gate_batch_raw}",
            "rows_total": len(sap_raw_df), "rows_saved": 0,
            "rows_deleted": 0,
            "batch_no": sap_batch_raw,
            "miss_team": 0,
            "miss_gate": len(sap_raw_df),
            "miss_monthly": 0,
            "errors": [{"type": "miss_gate", "count": len(sap_raw_df), "message": "Gate 매핑 누락"}],
        }
    logger.info("[SAP] GateProcessed 로드: %s건", len(gate_df))

    # 7) Gate: job_code → ra_key 매핑
    job_to_ra = {}
    for _, r in gate_df.iterrows():
        job = str(r.get("job") or "").strip()
        rk  = str(r.get("ra_key") or "").strip()
        if job and rk and job not in job_to_ra:
            job_to_ra[job] = rk

    # 8) RAKey 코드 → 설명
    rakey_map = {
        str(r["code"]).strip(): r["description"]
        for r in RaKey.objects.all().values("code", "description")
    }

    # 9) Team code → id (최신)
    team_df = pd.DataFrame(list(Team.objects.all().values("id", "code", "team_name")))
    team_by_code = {}
    if not team_df.empty:
        tmp = team_df.copy()
        tmp["code"] = tmp["code"].astype(str).str.strip()
        tmp = tmp.sort_values("id").drop_duplicates(subset=["code"], keep="last")
        team_by_code = {r["code"]: r["id"] for _, r in tmp.iterrows()}

    # 10) term 계산
    current_month = datetime.now().month
    MONTH_MAP_TERM = {10: "A", 11: "B", 12: "C"}
    term = "T0" + MONTH_MAP_TERM.get(current_month, str(current_month))

    # 11) 레코드 변환
    rows = []
    miss_team = miss_gate = miss_monthly = 0
    cols = set(sap_raw_df.columns)

    # ✅ PredictionClose 기반 flag 맵
    closing_flag_map = _closing_flags("closed")

    for i in range(len(sap_raw_df)):
        soff = str(sap_raw_df.at[i, "soff"]).strip() if "soff" in cols else ""
        operation_team = None
        div = None
        group_name = None

        if soff and soff in team_by_code:
            t = Team.objects.only("id", "team_name").filter(id=team_by_code[soff]).first()
            if t:
                operation_team = t
                parts = (t.team_name or "").split("-")
                div = parts[1] if len(parts) > 1 else None
                group_name = parts[2] if len(parts) > 2 else None
        else:
            miss_team += 1

        ship_to_party  = sap_raw_df.at[i, "ship_to"] if "ship_to" in cols else None
        client_name    = sap_raw_df.at[i, "ship_to_party_t"] if "ship_to_party_t" in cols else None
        soff           = sap_raw_df.at[i, "soff"] if "soff" in cols else None
        job_code       = str(sap_raw_df.at[i, "appropriate_project"]).strip() if "appropriate_project" in cols else ""
        project_detail = str(sap_raw_df.at[i, "project_t"]).strip() if "project_t" in cols else ""

        ra_key = job_to_ra.get(job_code)
        if not ra_key:
            miss_gate += 1
        revenue_type = rakey_map.get(str(ra_key).strip()) if ra_key else None

        # ── 월 데이터 가져오기
        soff_jobcode = str(soff) + "-" + str(job_code)
        monthly_data = monthly_map.get(soff_jobcode)

        rows.append({
            "term": term, "category": "결산", "div": div, "group_name": group_name,
            "operation_team": operation_team, "ship_to_party": ship_to_party,
            "client_name": client_name, "project_code": job_code,
            "project_detail": project_detail, "revenue_type": revenue_type,
            "headquarter": None, "monthly_data": monthly_data,
        })

    # 누락 오류 기록
    if miss_team > 0:
        errors.append({"type": "miss_team", "count": miss_team, "message": "팀 코드 누락"})
    if miss_gate > 0:
        errors.append({"type": "miss_gate", "count": miss_gate, "message": "Gate 매핑 누락"})
    if miss_monthly > 0:
        errors.append({"type": "miss_monthly", "count": miss_monthly, "message": "월별 데이터 누락"})

    # 12) batch_no -> integer
    save_batch = normalize_batch_for_model(SapProcessed, sap_batch_raw)

    # 13) 저장
    seen = set()
    to_save = []
    for r in rows:
        key = (
            (r["operation_team"].id if r["operation_team"] else None),
            r["project_code"],
        )
        if key in seen:
            continue
        seen.add(key)
        sp = SapProcessed(
            batch_no=save_batch,
            owner=owner,
            term=r["term"],
            category=r["category"],
            div=r["div"],
            group_name=r["group_name"],
            operation_team=r["operation_team"],
            ship_to_party=r["ship_to_party"],
            client_name=r["client_name"],
            project_code=r["project_code"],
            project_detail=r["project_detail"],
            revenue_type=r["revenue_type"],
            headquarter=r["headquarter"],
            monthly_data=r["monthly_data"],
        )
        to_save.append(sp)
    saved = SapProcessed.objects.bulk_create(to_save, batch_size=200)
    saved_count = len(saved)

    success = len(errors) == 0
    msg_ok = f"[SAP] 완료 | sap_batch={sap_batch_raw} | 저장={saved_count}"
    msg_warn = msg_ok + f" (with {len(errors)} errors)"

    # close month 기록
    sap_close.main(username)

    return {
        "success": success,
        "message": msg_ok if success else msg_warn,
        "rows_total": len(rows),
        "rows_saved": saved_count,
        "rows_deleted": 0,
        "batch_no": sap_batch_raw,
        "miss_team": miss_team,
        "miss_gate": miss_gate,
        "miss_monthly": miss_monthly,
        "errors": errors,
    }
