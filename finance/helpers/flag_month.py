from datetime import datetime, date
from dateutil.relativedelta import relativedelta

MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]  # ✅


# ===================================================================
# ✅ 조정 데이터 플래그 처리
# ===================================================================
def _process_active_flag():
    monthly_data = {}
    for idx, key in enumerate(MONTH_KEYS, start=1):
        monthly_data[key] = {
            "sales": int(0),
            "gross_profit": int(0),
            "flag": "active"
        }
    return monthly_data


# ===================================================================
# ✅ 머지 데이터 - month_key
# ===================================================================
def _month_key_from_int(m: int) -> str:
    return MONTH_KEYS[m - 1]

# ===================================================================
# ✅ 머지 데이터 - 모두 총합
# ===================================================================
def _get_sum(data, months: list[str], field: str) -> int:
    return sum(
        obj.monthly_data.model_dump().get(k, {}).get(field, 0)
        for obj in data
        for k in months
    )

# ===================================================================
# ✅ 머지 데이터 - diff
# ===================================================================
def _fmt_diff(actual: int, expected: int):
    diff = int(actual - expected)
    pct = round((diff / expected) * 100, 1) if expected else 0.0
    return diff, pct

# ===================================================================
# ✅ close monthly data (PredictionClose: 단일 기록 create + timestamp=datetime.now)
# ===================================================================
# 의미 매핑
FLAG_MEANING = {"hidden":"정산 마감","active":"입력 가능","closed":"입력 불가능"}

# ── 기준 월 계산 ──
def _last_month_year_for_closed():
    """지난달 (year, month)"""
    dt = date.today()
    return dt.year, dt.month

def _last_month_year_for_hidden():
    """지난달보다 한 달 전 (year, month) = last_month - 1"""
    dt = date.today() - relativedelta(months=1)
    return dt.year, dt.month


# ── monthly_data 키 정규화 ──
def _coerce_to_name_key_monthly(md: dict) -> dict:
    out = {k: {"sales":0, "gross_profit":0, "flag":""} for k in MONTH_KEYS}
    if not md:
        return out

    num_to_name = {
        "01":"jan","02":"feb","03":"mar","04":"apr","05":"may","06":"jun",
        "07":"jul","08":"aug","09":"sep","10":"oct","11":"nov","12":"dec"
    }
    for mm, name in num_to_name.items():
        if name in md and isinstance(md[name], dict):
            out[name] = md[name]; continue
        if mm in md and isinstance(md[mm], dict):
            out[name] = md[mm]; continue
        alt1, alt2 = str(int(mm)), int(mm)  # '8', 8
        if alt1 in md and isinstance(md[alt1], dict):
            out[name] = md[alt1]; continue
        if alt2 in md and isinstance(md[alt2], dict):
            out[name] = md[alt2]; continue
    return out


# ── TeamPrediction 월 플래그 수정 (변경된 경우에만 저장) ──
def _update_flags(TeamPrediction, month_names, target_flag, target_year):
    """
    TeamPrediction(year=target_year) 대상 월들의 flag를 target_flag로 업데이트.
    필요 시 SapProcessed 등 다른 모델에도 동일 패턴으로 확장하세요.
    """
    sap_cnt = 0
    tp_cnt = 0

    for obj in TeamPrediction.objects.filter(year=target_year).exclude(shared_dominate=False).iterator():
        md = _coerce_to_name_key_monthly(obj.monthly_data)
        changed = False
        for m in month_names:
            if md[m]["flag"] != target_flag:
                md[m]["flag"] = target_flag
                changed = True
        if changed:
            obj.monthly_data = md
            obj.save(update_fields=["monthly_data"])
            tp_cnt += 1

    return sap_cnt, tp_cnt


# ── PredictionClose: 단일 기록(무조건 create) ──
def _insert_PredictionClose(PredictionClose, year: int, month_int: int, action_name: str, request):
    """
    (year, month_int) 단일 레코드를 무조건 생성.
    timestamp는 datetime.now()로 고정.
    (unique 제약을 이미 제거했다는 전제)
    """
    PredictionClose.objects.create(
        year=year,
        month=month_int,
        action=action_name,
        closed_by=request.user,
        timestamp=datetime.now(),  # ✅ 고정
    )


# 예상 - 입력마감/입력
def _prediction_change_flag(TeamPrediction, PredictionClose, request, action_name:str):
    # 1) 1월 ~ (지난달보다 한 달 전) → hidden 플래그 반영 (기록은 X)
    target_year_hidden, last_month_hidden = _last_month_year_for_hidden()
    months_hidden = MONTH_KEYS[: last_month_hidden]
    _update_flags(TeamPrediction, months_hidden, "hidden", target_year_hidden)

    # 2) 지난달 ~ 12월 → active 플래그 반영 (기록은 X)
    target_year_active, last_month_active = _last_month_year_for_closed()
    months_active = MONTH_KEYS[last_month_active - 1:]
    _update_flags(TeamPrediction, months_active, action_name, target_year_active)

    # ✅ 기록은 “last_month - 2” 딱 1건만 생성
    rec_year, rec_month = _last_month_year_for_hidden()
    _insert_PredictionClose(PredictionClose, rec_year, rec_month, action_name, request)

    start_label = f"{last_month_active}월"

    flag_meaning = FLAG_MEANING[action_name]
    return target_year_active, start_label, rec_year, rec_month, flag_meaning