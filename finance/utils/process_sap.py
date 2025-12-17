#!/usr/bin/env python3
import os
import sys
import re
import logging
from datetime import datetime
from typing import Union

import django
import pandas as pd
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.db import models

# =========================
# Django 초기화
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# =========================
# 모델 import
# =========================
from finance.models import (
    SapRaw, SapProcessed,
    GateProcessed,
    Team,
    RaKey,
    PredictionClose,
)
from finance.utils.process_dbid import reset_pk_sequence_safely
from finance.utils import sap_pivot
from finance.utils import sap_close

logger = logging.getLogger(__name__)

BATCH_RE = re.compile(r"(\d{14})")
MONTH_KEYS = ["jan", "feb", "mar", "apr", "may", "jun",
              "jul", "aug", "sep", "oct", "nov", "dec"]


def _extract_batch_no(arg: Union[str, int]) -> int:
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
    f = model._meta.get_field("batch_no")
    return int(batch_no) if isinstance(f, models.IntegerField) else str(batch_no).strip()


def _closing_flags(post_flag: str = "closed") -> dict | None:
    latest = PredictionClose.objects.order_by("-year", "-month").first()
    if not latest:
        return None
    closing_month = int(latest.month)
    flags = {}
    for idx, key in enumerate(MONTH_KEYS, start=1):
        flags[key] = {"flag": "hidden" if idx <= closing_month else post_flag}
    return flags


def process_sap(gate_arg: Union[str, int], sap_arg: Union[str, int], username: str) -> dict:
    """
    SapRaw(sap_batch) → SapProcessed 적재 (GateProcessed(gate_batch)로 ra_key 매핑)
    ✅ 월별 데이터(monthly_data)는 sap_pivot.main() 결과에서 "job_code"로만 조회
    """
    errors = []

    gate_batch_raw = _extract_batch_no(gate_arg)
    sap_batch_raw = _extract_batch_no(sap_arg)

    User = get_user_model()
    owner = User.objects.get(username=username)

    logger.info("[SAP] gate_batch=%r, sap_batch=%r, owner=%s", gate_batch_raw, sap_batch_raw, username)

    if not RaKey.objects.exists():
        raise RuntimeError("[SAP] RaKey 데이터가 없습니다. 먼저 RaKey 업로드가 필요합니다.")

    # SapRaw 로드
    sap_q = Q(batch_no=sap_batch_raw) | Q(batch_no=str(sap_batch_raw)) | Q(batch_no__iexact=str(sap_batch_raw))
    sap_raw_qs = SapRaw.objects.filter(sap_q)
    sap_raw_df = pd.DataFrame(list(sap_raw_qs.values()))
    if sap_raw_df.empty:
        logger.warning("[SAP] SapRaw 없음 | sap_batch=%r", sap_batch_raw)
        return {
            "success": True,
            "message": f"[SAP] SapRaw 없음 | sap_batch={sap_batch_raw}",
            "rows_total": 0,
            "rows_saved": 0,
            "rows_deleted": 0,
            "batch_no": sap_batch_raw,
            "miss_team": 0,
            "miss_gate": 0,
            "miss_monthly": 0,
            "errors": [],
        }
    logger.info("[SAP] SapRaw 로드: %s건", len(sap_raw_df))

    # ✅ 월별 맵: 잡코드만 key
    monthly_map = sap_pivot.main()  # {job_code: {jan:{...},...}}
    if not monthly_map:
        logger.warning("[SAP] monthly_map 비어있음 (sap_pivot.main 결과 없음)")

    # GateProcessed 로드
    gate_q = Q(batch_no=gate_batch_raw) | Q(batch_no=str(gate_batch_raw)) | Q(batch_no__iexact=str(gate_batch_raw))
    gate_df = pd.DataFrame(list(GateProcessed.objects.filter(gate_q).values("job", "job_name", "ra_key")))
    if gate_df.empty:
        logger.warning("[SAP] GateProcessed 없음 | gate_batch=%r", gate_batch_raw)
        return {
            "success": True,
            "message": f"[SAP] GateProcessed 없음 | gate_batch={gate_batch_raw}",
            "rows_total": len(sap_raw_df),
            "rows_saved": 0,
            "rows_deleted": 0,
            "batch_no": sap_batch_raw,
            "miss_team": 0,
            "miss_gate": len(sap_raw_df),
            "miss_monthly": 0,
            "errors": [{"type": "miss_gate", "count": len(sap_raw_df), "message": "Gate 매핑 누락"}],
        }
    logger.info("[SAP] GateProcessed 로드: %s건", len(gate_df))

    # job_code -> ra_key
    job_to_ra = {}
    for _, r in gate_df.iterrows():
        job = str(r.get("job") or "").strip()
        rk = str(r.get("ra_key") or "").strip()
        if job and rk and job not in job_to_ra:
            job_to_ra[job] = rk

    # ra_key -> description
    rakey_map = {
        str(r["code"]).strip(): r["description"]
        for r in RaKey.objects.all().values("code", "description")
    }

    # Team code -> id 매핑(선택적으로 사용: soff 기반 팀매핑 하는 경우)
    team_df = pd.DataFrame(list(Team.objects.all().values("id", "code", "team_name")))
    team_by_code = {}
    if not team_df.empty:
        tmp = team_df.copy()
        tmp["code"] = tmp["code"].astype(str).str.strip()
        tmp = tmp.sort_values("id").drop_duplicates(subset=["code"], keep="last")
        team_by_code = {r["code"]: r["id"] for _, r in tmp.iterrows()}

    # term 계산
    current_month = datetime.now().month
    MONTH_MAP_TERM = {10: "A", 11: "B", 12: "C"}
    term = "T0" + MONTH_MAP_TERM.get(current_month, str(current_month))

    cols = set(sap_raw_df.columns)

    # close flag 맵 (원하면 monthly_data에 적용 가능)
    closing_flag_map = _closing_flags("closed")

    rows = []
    miss_team = 0
    miss_gate = 0
    miss_monthly = 0

    for i in range(len(sap_raw_df)):
        soff = str(sap_raw_df.at[i, "soff"]).strip() if "soff" in cols else ""
        operation_team = None
        div = None
        group_name = None

        # 팀 매핑 로직은 유지(원하면), 하지만 monthly pivot은 job_code만 사용
        # operation_team 매핑 기준이 soff/code일 수 있어 기존 로직 유지
        team_id = team_by_code.get(soff)
        if team_id:
            operation_team = Team.objects.filter(id=team_id).first()
        else:
            miss_team += 1

        ship_to_party = sap_raw_df.at[i, "ship_to"] if "ship_to" in cols else None
        client_name = sap_raw_df.at[i, "ship_to_party_t"] if "ship_to_party_t" in cols else None

        job_code = str(sap_raw_df.at[i, "appropriate_project"]).strip() if "appropriate_project" in cols else ""
        project_detail = str(sap_raw_df.at[i, "project_t"]).strip() if "project_t" in cols else ""

        ra_key = job_to_ra.get(job_code)
        if not ra_key:
            miss_gate += 1
        revenue_type = rakey_map.get(str(ra_key).strip()) if ra_key else None

        # ✅ monthly_data: job_code로만 가져오기
        monthly_data = monthly_map.get(job_code)
        if not monthly_data:
            miss_monthly += 1
            monthly_data = {m: {"sales": 0, "gross_profit": 0, "flag": "closed"} for m in MONTH_KEYS}

        # (선택) close flag 적용하고 싶으면 여기서 덮어쓰기
        if closing_flag_map:
            for m in MONTH_KEYS:
                monthly_data[m]["flag"] = closing_flag_map[m]["flag"]

        rows.append({
            "term": term,
            "category": "결산",
            "div": div,
            "group_name": group_name,
            "operation_team": operation_team,
            "ship_to_party": ship_to_party,
            "client_name": client_name,
            "project_code": job_code,
            "project_detail": project_detail,
            "revenue_type": revenue_type,
            "headquarter": None,
            "monthly_data": monthly_data,
        })

    if miss_team > 0:
        errors.append({"type": "miss_team", "count": miss_team, "message": "팀 코드(soff→team) 매핑 누락"})
    if miss_gate > 0:
        errors.append({"type": "miss_gate", "count": miss_gate, "message": "Gate 매핑(잡코드→ra_key) 누락"})
    if miss_monthly > 0:
        errors.append({"type": "miss_monthly", "count": miss_monthly, "message": "월별 데이터(monthly_map) 누락"})

    # 기존 동일 batch 삭제 + pk 정리
    save_batch = normalize_batch_for_model(SapProcessed, sap_batch_raw)
    SapProcessed.objects.filter(Q(batch_no=sap_batch_raw) | Q(batch_no=str(sap_batch_raw)) | Q(batch_no__iexact=str(sap_batch_raw))).delete()
    reset_pk_sequence_safely(SapProcessed, alias="default")

    # 저장(중복 제거: operation_team + project_code 기준 유지)
    seen = set()
    to_save = []
    for r in rows:
        key = ((r["operation_team"].id if r["operation_team"] else None), r["project_code"])
        if key in seen:
            continue
        seen.add(key)

        to_save.append(SapProcessed(
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
        ))

    saved = SapProcessed.objects.bulk_create(to_save, batch_size=200)
    saved_count = len(saved)

    success = len(errors) == 0
    msg_ok = f"[SAP] 완료 | sap_batch={sap_batch_raw} | 저장={saved_count}"
    msg_warn = msg_ok + f" (with {len(errors)} errors)"

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
