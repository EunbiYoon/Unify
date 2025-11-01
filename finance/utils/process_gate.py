#!/usr/bin/env python3
import os
import sys
import re
import logging
from typing import Union

import django
from django.db import transaction
from django.db.models import Q, Model
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
from finance.models import GateRaw, GateProcessed  # noqa: E402
from finance.utils.process_dbid import reset_pk_sequence_safely  # 경로 구조에 맞게 조정

# =========================
# 로거
# =========================
logger = logging.getLogger(__name__)

# =========================
# 유틸
# =========================
BATCH_RE = re.compile(r"(\d{14})")  # 예: ..._20250804194333.xlsx

def _extract_batch_no(arg: Union[str, int]) -> int:
    """경로 문자열/숫자 모두에서 14자리 배치번호 추출"""
    if isinstance(arg, int):
        return arg
    if isinstance(arg, str):
        m = BATCH_RE.search(arg)
        if m:
            return int(m.group(1))
        if arg.isdigit():
            return int(arg)
    raise ValueError(f"유효한 batch_no를 찾을 수 없습니다: {arg!r}")

def normalize_batch_no_for_model(batch_no: int):
    """
    GateProcessed.batch_no 필드 타입에 맞게 정규화
    - IntegerField → int
    - CharField/TextField → str
    """
    field = GateProcessed._meta.get_field("batch_no")
    if isinstance(field, models.IntegerField):
        return int(batch_no)
    return str(batch_no).strip()

# =========================
# 메인 진입 함수: 뷰/내부에서 직접 호출
# =========================
def process_gate(arg: Union[str, int]) -> dict:
    """
    GateRaw(batch_no) → GateProcessed 적재

    반환 딕셔너리 스키마:
      - success: bool
      - message: str
      - rows_total: int     # 원천 갯수
      - rows_saved: int     # 실제 저장 갯수
      - deleted: int        # 기존 동일 batch_no 삭제 갯수
      - batch_no: int       # 원본 배치 번호(정수)
      - errors: list[dict]  # 실패 레코드 정보
    """
    errors = []
    try:
        raw_batch_no = _extract_batch_no(arg)
        logger.info("[Gate] ✅ 입력 batch_no(raw)=%s", raw_batch_no)

        bn_for_model = normalize_batch_no_for_model(raw_batch_no)
        logger.info("[Gate] 🔧 저장/조회 batch_no(normalized)=%r (type=%s)",
                    bn_for_model, type(bn_for_model).__name__)

        # 혼용 대비(int/str) 조회
        gate_raw_qs = GateRaw.objects.filter(
            Q(batch_no=raw_batch_no) | Q(batch_no=str(raw_batch_no))
        )
        source_count = gate_raw_qs.count()
        if source_count == 0:
            msg = f"[Gate] 소스 없음 | batch_no={raw_batch_no}"
            logger.warning(msg)
            return {
                "success": True,
                "message": msg,
                "rows_total": 0,
                "rows_saved": 0,
                "deleted": 0,
                "batch_no": raw_batch_no,
                "errors": [],
            }

        records = []
        seen = set()
        # 동일 배치 선삭제 (혼용 대비)
        deleted, _ = GateProcessed.objects.filter(
            Q(batch_no=raw_batch_no) |
            Q(batch_no=str(raw_batch_no)) |
            Q(batch_no__iexact=str(raw_batch_no))
        ).delete()
        logger.info("[Gate] 🧹 기존 GateProcessed 삭제: %s건 (batch_no=%s)", deleted, raw_batch_no)

        # PK 시퀀스 정리
        reset_pk_sequence_safely(GateProcessed, alias="default")

        # Dedup + 적재 준비
        for obj in gate_raw_qs.select_related(None):
            job = (obj.job or "").strip()
            job_name = (obj.job_name or "").strip()
            ra_key = (obj.ra_key or "").strip()

            key = (job, job_name, ra_key)
            if key in seen:
                continue
            seen.add(key)

            records.append(
                GateProcessed(
                    job=job,
                    job_name=job_name,
                    ra_key=ra_key,
                    batch_no=bn_for_model,  # 필드 타입에 맞춰 저장
                )
            )

        saved = 0
        if records:
            try:
                GateProcessed.objects.bulk_create(records, ignore_conflicts=False)
                saved = len(records)
                logger.info("[Gate] 📊 원천=%s | ✅ 저장=%s (batch_no=%s)", source_count, saved, raw_batch_no)
            except Exception as e:
                # bulk 실패 시 단건 저장으로 폴백
                logger.exception("[Gate] bulk_create 실패, 단건 저장으로 전환: %s", e)
                for inst in records:
                    sid = transaction.savepoint()
                    try:
                        inst.save(force_insert=True)
                        saved += 1
                        transaction.savepoint_commit(sid)
                    except Exception as e2:
                        transaction.savepoint_rollback(sid)
                        errors.append({
                            "job": inst.job,
                            "job_name": inst.job_name,
                            "ra_key": inst.ra_key,
                            "error": e2.__class__.__name__,
                            "detail": str(e2),
                        })
                if errors:
                    logger.warning("[Gate] 단건 저장 중 일부 실패: %d건", len(errors))
        else:
            logger.info("[Gate] ℹ️ 저장할 레코드가 없습니다.")
            deleted = deleted if 'deleted' in locals() else 0

        msg_ok = f"[Gate] Done | batch_no={raw_batch_no} | total={source_count} saved={saved} deleted={deleted}"
        msg_warn = msg_ok + f" (with {len(errors)} errors)"
        return {
            "success": len(errors) == 0,
            "message": msg_ok if len(errors) == 0 else msg_warn,
            "rows_total": source_count,
            "rows_saved": saved,
            "deleted": deleted,
            "batch_no": raw_batch_no,
            "errors": errors,
        }

    except Exception as e:
        logger.exception("[Gate] Top-level failure: %s", e)
        # 실패해도 항상 매핑 리턴
        return {
            "success": False,
            "message": f"[Gate] Failed: {e}",
            "rows_total": 0,
            "rows_saved": 0,
            "deleted": 0,
            "batch_no": _extract_batch_no(arg) if isinstance(arg, (str, int)) else None,
            "errors": [{"error": e.__class__.__name__, "detail": str(e)}],
        }

# 스크립트가 직접 실행된 경우 테스트 실행
if __name__ == "__main__":
    process_gate("tmp/gate_20250902132321.xlsx")  # 지정된 엑셀 파일로 테스트 실행
