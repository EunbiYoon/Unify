from django.db import transaction
from finance.models import PredictionClose

MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]

def _month_key_from_int(m: int) -> str:
    return MONTH_KEYS[m - 1]

def _normalize_md(md) -> dict:
    """monthly_data가 dict가 아니어도 안전하게 dict로 변환"""
    if hasattr(md, "model_dump"):
        md = md.model_dump()
    if not isinstance(md, dict) or md is None:
        return {}
    return md

def _pred_close(TeamPrediction):
    latest = PredictionClose.objects.order_by("-timestamp").first()
    if not latest:
        return 0

    year = int(latest.year)
    closed_month = int(latest.month)
    action = (latest.action or "").strip().lower()  # 'active' / 'closed'

    qs = TeamPrediction.objects.filter(year=year)  # ← 여기선 전부 가져와도 됨

    updated = []
    with transaction.atomic():
        for obj in qs.select_for_update():
            md = _normalize_md(obj.monthly_data)

            # 1 ~ closed_month : hidden (공통)
            for m in range(1, closed_month + 1):
                k = _month_key_from_int(m)
                if k not in md or not isinstance(md.get(k), dict):
                    md[k] = {}
                md[k]["flag"] = "hidden"

            # closed_month+1 ~ 12 : 레코드 종류에 따라 분기
            # shared_dominate가 False면 무조건 'closed'
            # True 또는 None이면 action에 따라 'active'/'closed'
            post_flag_if_dominant = "active" if action == "active" else "closed"
            post_flag_if_shared   = "closed"
            is_shared = (obj.shared_dominate is False)

            for m in range(closed_month + 1, 13):
                k = _month_key_from_int(m)
                if k not in md or not isinstance(md.get(k), dict):
                    md[k] = {}
                md[k]["flag"] = post_flag_if_shared if is_shared else post_flag_if_dominant

            obj.monthly_data = md
            updated.append(obj)

        if updated:
            TeamPrediction.objects.bulk_update(updated, ["monthly_data"])

    return len(updated)
