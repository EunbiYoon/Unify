#!/usr/bin/env python3
import os
import sys
import re
import json
import logging
from datetime import date
from typing import Optional, Tuple

import django
import pandas as pd
import numpy as np
from django.db.models import Max

# =========================
# Django 초기화 (스크립트 단독 실행 대비)
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from finance.models import SapRaw, SapProcessed  # noqa: E402

logger = logging.getLogger(__name__)

MONTH_KEYS = ["jan", "feb", "mar", "apr", "may", "jun",
              "jul", "aug", "sep", "oct", "nov", "dec"]


def month_key(period) -> str:
    """
    period: '2025001' ~ '2025012' 같은 값
    -> jan ~ dec 로 변환
    """
    period_pure = re.sub(r"\D", "", str(period))
    if len(period_pure) < 6:
        return "jan"  # fallback
    mm = int(period_pure[-2:])
    mm = max(1, min(12, mm))
    return MONTH_KEYS[mm - 1]


def as_dict(x):
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            return {}
    return x or {}


def _ensure_12months(df: pd.DataFrame) -> pd.DataFrame:
    """피벗 결과가 특정 월 컬럼이 빠질 수 있으니 12개월 컬럼 보장."""
    for m in MONTH_KEYS:
        if m not in df.columns:
            df[m] = 0
    return df.reindex(columns=MONTH_KEYS).fillna(0)


def build_pivot_from_model(model_name: str) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    ✅ 잡코드만 기준으로 피벗:
      - SapRaw      : index = appropriate_project
      - SapProcessed: index = project_code (operation_team 무시)
    return: (sales_pivot, gp_pivot) both columns = jan..dec
    """
    if model_name == "SapRaw":
        agg = SapRaw.objects.exclude(batch_no__isnull=True).aggregate(latest=Max("batch_no"))
        latest_batch = agg["latest"]
        if latest_batch is None:
            logger.info("⚠️ SapRaw batch_no 없음")
            return None

        qs = (SapRaw.objects
              .filter(batch_no=latest_batch)
              .values("appropriate_project", "period", "t_sales", "t_revenue"))
        df = pd.DataFrame.from_records(qs)
        if df.empty:
            logger.info("⚠️ SapRaw에 데이터가 없습니다.")
            return None

        # 잡코드만
        df["job_code"] = df["appropriate_project"].astype(str).str.strip()
        df["m"] = df["period"].apply(month_key)

        sales = (df.pivot_table(index="job_code", columns="m", values="t_sales",
                                fill_value=0, aggfunc="sum"))
        gp = (df.pivot_table(index="job_code", columns="m", values="t_revenue",
                             fill_value=0, aggfunc="sum"))

        sales = _ensure_12months(sales)
        gp = _ensure_12months(gp)

        # 숫자 정리
        try:
            sales = sales.astype("int64")
        except Exception:
            pass
        try:
            gp = gp.astype("int64")
        except Exception:
            pass

        return sales, gp

    if model_name == "SapProcessed":
        qs = SapProcessed.objects.values("project_code", "monthly_data")
        df = pd.DataFrame.from_records(qs)
        if df.empty:
            logger.info("⚠️ SapProcessed에 데이터가 없습니다.")
            return None

        df["project_code"] = df["project_code"].astype(str).str.strip()
        md_series = df["monthly_data"].apply(as_dict)

        # monthly_data -> (sales, gp) 12개월 컬럼으로 펼치기
        sales_cols = md_series.apply(
            lambda md: {m: (md.get(m, {}) or {}).get("sales", 0) for m in MONTH_KEYS}
        ).apply(pd.Series)
        gp_cols = md_series.apply(
            lambda md: {m: (md.get(m, {}) or {}).get("gross_profit", 0) for m in MONTH_KEYS}
        ).apply(pd.Series)

        sales_cols["project_code"] = df["project_code"]
        gp_cols["project_code"] = df["project_code"]

        # ✅ 같은 project_code가 여러 row(팀이 다르거나 중복) 있으면 '합계'로 하나로 만들기
        sales = sales_cols.groupby("project_code")[MONTH_KEYS].sum()
        gp = gp_cols.groupby("project_code")[MONTH_KEYS].sum()

        sales = _ensure_12months(sales)
        gp = _ensure_12months(gp)

        # 숫자 정리
        sales = sales.apply(pd.to_numeric, errors="coerce").fillna(0)
        gp = gp.apply(pd.to_numeric, errors="coerce").fillna(0)

        try:
            sales = sales.astype("int64")
        except Exception:
            pass
        try:
            gp = gp.astype("int64")
        except Exception:
            pass

        return sales, gp

    raise ValueError(f"Unknown model_name: {model_name}")


def merge_two_pivots(raw_df: pd.DataFrame, processed_df: pd.DataFrame, dtype="int64") -> pd.DataFrame:
    """
    raw_df 우선 + processed_df에서 raw에 없는 project_code만 추가
    """
    processed_unique = processed_df[~processed_df.index.isin(raw_df.index)]
    out = pd.concat([raw_df, processed_unique], axis=0).fillna(0)
    out = _ensure_12months(out)

    try:
        out = out.astype(dtype)
    except Exception:
        pass
    return out


def to_monthly_dict_all(
    sales_df: pd.DataFrame,
    gp_df: Optional[pd.DataFrame] = None,
    default_flag: str = "closed",
) -> dict:
    sales = _ensure_12months(sales_df)
    gp = _ensure_12months(gp_df) if gp_df is not None else sales

    def to_py(v):
        if v is None:
            return 0
        try:
            v = v.item() if hasattr(v, "item") else v
        except Exception:
            pass
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            vv = float(v)
            return int(vv) if vv.is_integer() else vv
        if isinstance(v, float) and v.is_integer():
            return int(v)
        return v

    out = {}
    for job_code in sales.index:
        out[str(job_code)] = {
            m: {
                "sales": to_py(sales.at[job_code, m]),
                "gross_profit": to_py(gp.at[job_code, m]),
                "flag": default_flag,
            }
            for m in MONTH_KEYS
        }
    return out


def main() -> dict:
    """
    ✅ 항상 "잡코드만" 기준으로 monthly_map을 반환:
      { "K1S24I79012": { "jan": {...}, ... "dec": {...} }, ... }
    """
    raw_pair = build_pivot_from_model("SapRaw")
    if raw_pair is None:
        return {}

    raw_sales, raw_gp = raw_pair

    if not SapProcessed.objects.exists():
        final_sales, final_gp = raw_sales, raw_gp
    else:
        proc_pair = build_pivot_from_model("SapProcessed")
        if proc_pair is None:
            final_sales, final_gp = raw_sales, raw_gp
        else:
            proc_sales, proc_gp = proc_pair
            final_sales = merge_two_pivots(raw_sales, proc_sales)
            final_gp = merge_two_pivots(raw_gp, proc_gp)

    monthly_data = to_monthly_dict_all(final_sales, final_gp, default_flag="closed")
    return monthly_data


if __name__ == "__main__":
    md = main()
    print(list(md.keys())[:5])
