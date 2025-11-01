from finance.models import (
    PredictionClose
)
import logging
logger = logging.getLogger(__name__)

MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]

def _create_origin_monthly_data(request) -> dict:
    """
    최신 PredictionClose 기준으로 monthly_data 생성
    - 1~closing_month: flag="hidden"
    - closing_month+1~12: action이 'active'면 flag='active', 아니면 flag='closed'
    """
    latest = PredictionClose.objects.order_by("-timestamp").first()
    
    ### 만약 데이터가 없으면 새로운 객체를 생성
    if latest is None:
        # 오늘 기준 -1개월
        base_date = date.today() - relativedelta(months=1)

        latest = PredictionClose.objects.create(
            year=int(base_date.year),
            month=int(base_date.month),
            closed_by=request.user,
            action="active",
            timestamp=date.today()
        )
    logger.info(f"✅latest_closed for creation : prediction_close id => {latest.id}")

    closing_month = int(latest.month)
    post_flag = str(latest.action).lower()
    logger.info(f"🔵flag of latest_closed for creation :{post_flag}")

    md = {}
    for idx, key in enumerate(MONTH_KEYS, start=1):
        if idx <= closing_month:
            flag = "hidden"
        else:
            flag = post_flag
        md[key] = {"sales": int(0), "gross_profit": int(0), "flag": flag}
    return md



def _create_shared_monthly_data(request) -> dict:
    """
    최신 PredictionClose 기준으로 monthly_data 생성
    - 1~closing_month: flag="hidden"
    - closing_month+1~12: action이 'active'면 flag='active', 아니면 flag='closed'
    """
    latest = PredictionClose.objects.order_by("-timestamp").first()
    logger.info(f"✅latest_closed for creation : prediction_close id => {latest.id}")
    if not latest:
        raise ValueError("month_closing 데이터가 없습니다.")

    closing_month = int(latest.month)  # 1~12

    md = {}
    for idx, key in enumerate(MONTH_KEYS, start=1):
        if idx <= closing_month:
            flag = "hidden"
        else:
            flag = "closed"
        md[key] = {"sales": int(0), "gross_profit": int(0), "flag": flag}
    return md

