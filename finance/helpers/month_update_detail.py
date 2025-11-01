# 표준 라이브러리
import os
import re
import json
import datetime
from io import BytesIO
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs
from collections import defaultdict
from typing import List, Optional, Literal
from datetime import datetime, date

# Django 라이브러리
from finance.models import (
    TeamPrediction, TeamPredictionHistory,
    SapRaw, CctrRaw, GateRaw, RaKey, SapProcessed, CctrProcessed, GateProcessed, PredictionClose, ProcessClose
)
# month
MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]

# 로거
import logging
logger = logging.getLogger(__name__)

################################ shared_intance -> 음수 처리 ################################
# 음수 처리
def _negate_numbers(data: dict) -> dict:
    for month in data:
        val = str(data[month])  # k1에 해당하는 값 전체를 문자열로 변환 (한번만)
        logger.info(f"Raw string val: {month}")
        sales_value = None
        gross_value = None
        sales_match = re.search(r"sales=(-?\d+)", val)
        if sales_match:
            sales_value = (-1) * int(sales_match.group(1))
        gross_match = re.search(r"gross_profit=(-?\d+)", val)
        if gross_match:
            gross_value = (-1) * int(gross_match.group(1))
    logger.info(f"{month}, {sales_value}, {gross_value}")
    return month, sales_value, gross_value

# 음수해당하는 플래그 처리
def _negate_flags(month_str: str) -> str:
    month_int = int(MONTH_KEYS.index(month_str.lower()) + 1)
    prediction_close = PredictionClose.objects.order_by("-id").first()
    prediction_close_month = int(prediction_close.month)
    logger.info(f"prediction+close_month:{month_int}/{prediction_close_month}")
    if month_int > prediction_close_month:
        direct_flag="closed"
    else:
        direct_flag="hidden"
    return direct_flag

# monthly_data 음수 처리하기 : data가 들어오면 shared_obj를 업데이트 함
def _month_negately_data(data: dict, shared_obj: dict):
    month_str, new_sales, new_gross = _negate_numbers(data.monthly_data)
    if new_sales:
        shared_obj.monthly_data[month_str]['sales'] = new_sales 
    if new_gross:
        shared_obj.monthly_data[month_str]['gross_profit'] = new_gross 
    # 플래그 hidden 할지, closed 할기
    if new_sales or new_gross:
        direct_flag = _negate_flags(month_str)
        shared_obj.monthly_data[month_str]['flag'] = direct_flag

