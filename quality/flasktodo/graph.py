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
    base = month_start(today)
    months = [add_months(base, -2), add_months(base, -1), base]  # 2M,1M,0M

    # 월별 총량 비율(너가 원하는 느낌으로 조절)
    # 너무 작위적이면 0.25/0.35/0.40 같이 완만하게
    ratios = np.array([0.28, 0.33, 0.39])
    totals = (ratios * total).astype(int)
    totals[-1] = total - totals[:-1].sum()

    rows = []

    for m, month_total in zip(months, totals):
        end = last_day(m)

        # 일별 가중치: 완만한 랜덤(합 1)
        # Dirichlet은 "자연스러운 분배" 만들기 좋음
        w = np.random.dirichlet(alpha=np.ones(end) * 2.5)  # alpha↑ = 더 매끈
        daily = np.round(w * month_total).astype(int)

        # 반올림 오차 보정
        diff = month_total - daily.sum()
        if diff != 0:
            idx = np.random.randint(0, end)
            daily[idx] += diff

        for day in range(1, end + 1):
            d = date(m.year, m.month, day)
            if d > today:
                break

            cnt = int(daily[day - 1])

            # (선택) 요일 효과: 주말 조금 줄고, 월요일 약간 증가 같은 느낌
            # 너무 티나면 주석 처리해도 됨
            wd = d.weekday()  # Mon=0 ... Sun=6
            if wd == 0:            # 월요일
                cnt = int(cnt * 1.08)
            elif wd >= 5:          # 토/일
                cnt = int(cnt * 0.92)

            for _ in range(cnt):
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
