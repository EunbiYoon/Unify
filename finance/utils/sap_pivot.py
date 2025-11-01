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
sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


# =========================
# 모델 import
# =========================
from finance.models import SapRaw, SapProcessed
import pandas as pd
import numpy as np
from datetime import date
from django.db.models import Max


# =========================
# 로거
# =========================
logger = logging.getLogger(__name__)
MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]

def month_key(period):
    # 숫자만 추출
    period_pure = re.sub(r"\D", "", str(period)) 
    
    # 지난달 연도 가져와서 연도가 일치하는 지확인
    today = date.today()
    last_year = today.year - 1 if today.month == 1 else today.year
    period_year = period_pure[:4]
    
    #  2025002 => feb로 바꾸기
    period_month=int(period_pure[-2:])
    return MONTH_KEYS[period_month-1]


def md_to_long(md: dict) -> pd.DataFrame:
    rows = [
        {
            "month": m,
            "sales":        (md.get(m, {}) or {}).get("sales", 0),
            "gross_profit": (md.get(m, {}) or {}).get("gross_profit", 0),
            "flag":         (md.get(m, {}) or {}).get("flag", None),
        }
        for m in MONTH_KEYS
    ]
    df = pd.DataFrame(rows)
    # optional: keep month order
    df["month"] = pd.Categorical(df["month"], categories=MONTH_KEYS, ordered=True)
    return df.sort_values("month").reset_index(drop=True)


def as_dict(x):
    if isinstance(x, dict): return x
    if isinstance(x, str):
        try: return json.loads(x)
        except Exception: return {}
    return x or {}

def build_pivot_from_model(model_name):
    if model_name == "SapRaw":
        # 1) 가장 최신의 배치넘버를 가지는 오브젝트 추출
        agg = SapRaw.objects.exclude(batch_no__isnull=True).aggregate(latest=Max("batch_no"))
        latest_batch = agg["latest"]
        raw_qs = SapRaw.objects.filter(batch_no=latest_batch) if latest_batch is not None else SapRaw.objects.none()

        # 2) QuerySet → DataFrame
        qs = SapRaw.objects.values("id","appropriate_project","soff","period", "t_sales", "t_revenue")
        df = pd.DataFrame.from_records(qs)
        if df.empty:
            logger.info("⚠️ SapRaw에 데이터가 없습니다.")
            return None

        # 3) 매출 피벗 & 매출총이익 피벗
        sales_pivot = pd.pivot_table(df,index=["soff", "appropriate_project"],columns="period",values="t_sales",fill_value=0, aggfunc='sum').astype("int64")
        gp_pivot = pd.pivot_table(df,index=["soff", "appropriate_project"],columns="period",values="t_revenue",fill_value=0, aggfunc='sum').astype("int64")

        # 4) (K1P24001018, LAYQ) -> K1P24001018_LAYQ
        sales_pivot.index = sales_pivot.index.map(lambda x: f'{x[0]}-{x[1]}')
        gp_pivot.index = gp_pivot.index.map(lambda x: f'{x[0]}-{x[1]}')

        # 5) 칼럼 값을 이제 2025001 ~ 2025012 => jan ~ dec로 바꾸기 
        sales_pivot.columns = [month_key(c) for c in sales_pivot.columns]
        gp_pivot.columns = [month_key(c) for c in gp_pivot.columns]
        return sales_pivot, gp_pivot

    elif model_name == "SapProcessed":
        # 1) QuerySet → DataFrame
        raw_qs = SapProcessed.objects.all()
        qs = SapProcessed.objects.values("id","project_code", "operation_team__code","monthly_data")
        df = pd.DataFrame.from_records(qs)
        if df.empty:
            logger.info("⚠️ SapProcessed에 데이터가 없습니다.")
            return None    
        
        # 2) monthly_data 에서 sales, gross_profit 데이터 분리해서 피벗 만들기
        sales_pivot=df[[f"sales_{m}" for m in MONTH_KEYS]] = (df["monthly_data"].apply(as_dict).apply(lambda md: {m: (md.get(m, {})).get("sales") for m in MONTH_KEYS}).apply(pd.Series))
        sales_pivot.index = df["project_code"].values
        sales_pivot.index.name = "project_code"
        sales_pivot.index = df["operation_team__code"] + "-" + df["project_code"]
        
        gp_pivot=df[[f"gross_profit_{m}" for m in MONTH_KEYS]] = (df["monthly_data"].apply(as_dict).apply(lambda md: {m: (md.get(m, {})).get("gross_profit") for m in MONTH_KEYS}).apply(pd.Series))
        gp_pivot.index = df["project_code"].values
        gp_pivot.index.name = "project_code"
        gp_pivot.index = df["operation_team__code"] + "-" + df["project_code"]
        return sales_pivot, gp_pivot


def check_duplicate_index(df, df_name):
    duplicated = df.index[df.index.duplicated()]
    if len(duplicated) > 0:
        logger.info(f"[WARNING] {df_name}에 중복된 인덱스가 있습니다:")
        logger.info(duplicated.unique())
    else:
        logger.info(f"[INFO] {df_name}에는 중복 인덱스가 없습니다.")


def merge_two_pivots(p1: pd.DataFrame, p2: pd.DataFrame, zero=0, dtype="int64") -> pd.DataFrame:
    # 공통 인덱스를 제외한 p2만 추출
    p2_unique = p2[~p2.index.isin(p1.index)]

    # p1과 p2_unique를 위로 붙이기 (p1 우선)
    result_df = pd.concat([p1, p2_unique], axis=0)

    # 결측치는 0으로 채우기
    result_df = result_df.fillna(zero)

    # 컬럼 순서: MONTH_KEYS 우선
    ordered_cols = [col for col in MONTH_KEYS if col in result_df.columns] + \
                   [col for col in result_df.columns if col not in MONTH_KEYS]
    result_df = result_df.reindex(columns=ordered_cols)

    # 정수형으로 변환 (가능하면)
    try:
        result_df = result_df.astype(dtype)
    except Exception:
        pass

    return result_df


# 리턴해주기 직전 최종의값 => json
def to_monthly_dict_all(sales_df: pd.DataFrame,
                        gp_df: pd.DataFrame | None = None,
                        default_flag: str = "closed") -> dict:
    # 월 컬럼만 추리고 NaN -> 0
    sales = sales_df.reindex(columns=MONTH_KEYS).fillna(0)
    gp    = gp_df.reindex(columns=MONTH_KEYS).fillna(0) if gp_df is not None else sales

    def to_py(v):
        # numpy/pandas 스칼라 -> 파이썬 네이티브
        # NaN 방지
        if v is None:
            return 0
        try:
            # numpy scalar면 item()으로 파이썬 스칼라 추출
            v = v.item() if hasattr(v, "item") else v
        except Exception:
            pass
        # pandas가 float로 준 0.0 등을 int로 정리 (정수로 떨어질 때만)
        try:
            if isinstance(v, float) and v.is_integer():
                return int(v)
        except Exception:
            pass
        # numpy 정수/실수 대응
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            return float(v)
        return v

    out = {}
    for idx in sales.index:
        out[idx] = {
            m: {
                "sales":        to_py(sales.at[idx, m]),
                "gross_profit": to_py(gp.at[idx, m]),
                "flag":         default_flag,
            }
            for m in MONTH_KEYS
        }
    return out


def main():
    # 초기 데이터라면 (아무것도 샙에 업로드 안되어 잇음)
    if not SapProcessed.objects.exists():
        raw_sales, raw_gp = build_pivot_from_model("SapRaw")
        monthly_data=to_monthly_dict_all(raw_sales, raw_gp)
        raw_sales.to_excel('raw_sales.xlsx')
        return monthly_data

    # 초기가 아닌 데이터라면
    else:
        processed_sales, processed_gp = build_pivot_from_model("SapProcessed")
        processed_sales.to_excel('sap_processed.xlsx')
        raw_sales, raw_gp = build_pivot_from_model("SapRaw")
        final_sales=merge_two_pivots(raw_sales, processed_sales)
        final_gp=merge_two_pivots(raw_gp, processed_gp)
        final_sales.to_excel('final_sales.xlsx')
        monthly_data=to_monthly_dict_all(final_sales, final_gp)
        return monthly_data

if __name__ == "__main__":
    main()