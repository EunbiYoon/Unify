import re
import json
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]


def _normalize_monthly_data(md) -> dict:
    """monthly_data를 dict로 정규화 (BaseModel / bytes / str(JSON) 지원)"""
    try:
        if hasattr(md, "model_dump"):
            md = md.model_dump()
        if isinstance(md, (bytes, bytearray)):
            md = md.decode("utf-8", errors="ignore")
        if isinstance(md, str):
            md = json.loads(md)
    except Exception:
        logger.warning("[normalize] monthly_data 파싱 실패 → 빈 dict 사용")
        return {}
    return md if isinstance(md, dict) else {}


def _coerce_int(val):
    """정수로 강제 변환: '1,000' '1_000' '+10' 등 허용, 실패 시 None"""
    if val is None:
        return None
    try:
        if isinstance(val, str):
            s = val.strip().replace(",", "").replace("_", "")
            if re.fullmatch(r"[+-]?\d+", s):
                return int(s)
            return None
        return int(val)
    except Exception:
        return None


def _ensure_month_cell(md: dict, key: str) -> dict:
    """md[key]가 dict가 아니면 dict로 교체 후 반환"""
    cell = md.get(key)
    if not isinstance(cell, dict):
        cell = {}  # 원시값 보존 불필요하면 빈 dict로 초기화
        md[key] = cell
    return cell


def _negate_flags(month_str: str) -> str:
    """월 기준으로 flag 설정"""
    from finance.models import PredictionClose
    month_int = MONTH_KEYS.index(month_str.lower()) + 1
    pc = PredictionClose.objects.order_by("-id").first()
    closed_until = int(pc.month) if pc else 12
    return "closed" if month_int > closed_until else "hidden"


def _negate_numbers(monthly_data: dict) -> dict:
    """
    sales / gross_profit 값에 (-1) 곱하기
    - 월 셀이 dict가 아니어도 dict로 보정 후 처리
    - 숫자 문자열도 허용
    ⚠️ 이 함수는 호출할 때마다 부호가 뒤집힙니다(요청 사양대로 곱셈 적용).
    """
    md = deepcopy(monthly_data) if monthly_data else {}
    for m in list(md.keys()):
        key = str(m).lower()
        if key not in MONTH_KEYS:
            continue

        cell = _ensure_month_cell(md, key)

        s = _coerce_int(cell.get("sales"))
        if s is not None:
            cell["sales"] = s * -1
            logger.info(f"[negate] {key}.sales: {s} -> {cell['sales']}")

        g = _coerce_int(cell.get("gross_profit"))
        if g is not None:
            cell["gross_profit"] = g * -1
            logger.info(f"[negate] {key}.gross_profit: {g} -> {cell['gross_profit']}")
    return md


def _apply_flags(monthly_data: dict) -> dict:
    """
    sales 또는 gross_profit이 존재하는 월에 flag 반영
    """
    md = deepcopy(monthly_data) if monthly_data else {}
    for m in list(md.keys()):
        key = str(m).lower()
        if key not in MONTH_KEYS:
            continue
        cell = _ensure_month_cell(md, key)
        if ("sales" in cell and cell["sales"] is not None) or ("gross_profit" in cell and cell["gross_profit"] is not None):
            cell["flag"] = _negate_flags(key)
            logger.info(f"[flag] {key} -> {cell['flag']}")
    return md


def _update_shared_monthly_data(origin_monthly_data: dict) -> dict:
    """
    ✅ 최종 함수:
    1) dict로 정규화
    2) sales/gross_profit 값 -1 곱하기
    3) flag 반영
    """
    normalized = _normalize_monthly_data(origin_monthly_data)
    negated = _negate_numbers(normalized)
    with_flags = _apply_flags(negated)
    return with_flags
