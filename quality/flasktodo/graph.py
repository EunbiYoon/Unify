from datetime import date, timedelta
import pandas as pd
import numpy as np
from random import randint, choice

def month_start(d):
    return date(d.year, d.month, 1)

def add_months(d, m):
    y = d.year + (d.month - 1 + m) // 12
    mm = (d.month - 1 + m) % 12 + 1
    return date(y, mm, 1)

def month_key(d):
    return f"{d.year}-{d.month:02d}"

def month_label(d):
    return f"{d.year}.{d.month:02d}"

def last_day(d):
    return (add_months(month_start(d), 1) - timedelta(days=1)).day


def generate_svc_data(today, total):
    symptoms = ["DRAIN","EXPLANATION","INSTALLATION","NOISE","OTHER","PCB"]
    rows = []
    for _ in range(total):
        m = randint(0, 2)
        d0 = add_months(month_start(today), -m)
        day = randint(1, last_day(d0))
        d = date(d0.year, d0.month, day)
        if d > today:
            continue
        rows.append({
            "Symptoms": choice(symptoms),
            "Report_Date": d.strftime("%Y-%m-%d")
        })
    return pd.DataFrame(rows)


def build_last3():
    today = date.today()
    svc_data = generate_svc_data(today, randint(3000, 6000))

    df = svc_data.copy()
    df["dt"] = pd.to_datetime(df["Report_Date"])
    df["day"] = df["dt"].dt.day
    df["key"] = df["dt"].dt.strftime("%Y-%m")

    base = month_start(today)
    months = [add_months(base, -2), add_months(base, -1), base]
    keys = [month_key(m) for m in months]
    labels = [month_label(m) for m in months]

    pivot = (
        pd.crosstab(df["day"], df["key"])
        .reindex(index=range(1, 32), fill_value=0)
        .reindex(columns=keys, fill_value=0)
        .astype(float)
    )

    for m in months:
        pivot.loc[last_day(m)+1:31, month_key(m)] = np.nan

    pivot.loc[today.day+1:31, month_key(base)] = np.nan
    pivot = pivot.cumsum()
    pivot.columns = labels

    return pivot, svc_data


# ===== 여기서 "전역 변수"로 노출 =====
_SVC, _svc_data = build_last3()

legend2M, legend1M, legend0M = _SVC.columns.tolist()
ABlabels = list(range(1, 32))

Avalues2M = _SVC[legend2M].dropna().tolist()
Avalues1M = _SVC[legend1M].dropna().tolist()
Avalues0M = _SVC[legend0M].dropna().tolist()

Bvalues2M = Avalues2M
Bvalues1M = Avalues1M
Bvalues0M = Avalues0M

Plabels = _svc_data["Symptoms"].value_counts().index.tolist()
Pvalues = _svc_data["Symptoms"].value_counts().tolist()

svc_data_html = _svc_data.to_html()
min_data_html = _svc_data[_svc_data["Report_Date"].str.contains(legend0M.replace(".", "-"))].to_html()
