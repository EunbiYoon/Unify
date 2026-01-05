from datetime import date, timedelta
import numpy as np
import pandas as pd
from random import randint, choice, seed


# ---------------- date utils ----------------
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


# ---------------- fast: day-count generation (no huge loops) ----------------
def generate_daily_counts(today, total_svc, month_ratios=(0.30, 0.33, 0.37), smooth=4.0):
    base = month_start(today)
    months = [add_months(base, -2), add_months(base, -1), base]  # 2M, 1M, 0M
    keys = [month_key(m) for m in months]
    ends = [last_day(m) for m in months]

    ratios = np.array(month_ratios, dtype=float)
    ratios = ratios / ratios.sum()
    totals = (ratios * int(total_svc)).astype(int)
    totals[-1] = int(total_svc) - totals[:-1].sum()

    daily = pd.DataFrame(index=range(1, 32), columns=keys, dtype=float)
    daily[:] = 0.0

    for k, end, tot in zip(keys, ends, totals):
        # 부드러운 일별 분배(실무 느낌)
        w = np.random.dirichlet(alpha=np.ones(end) * float(smooth))
        cnt = np.round(w * int(tot)).astype(int)

        # 반올림 오차 보정
        diff = int(tot - cnt.sum())
        if diff != 0:
            cnt[np.random.randint(0, end)] += diff

        daily.loc[1:end, k] = cnt.astype(float)
        daily.loc[end + 1:31, k] = np.nan

    # 이번달은 오늘 이후 제거
    daily.loc[today.day + 1:31, month_key(base)] = np.nan
    return daily


def build_svc_cumsum_from_daily(today, daily_counts):
    base = month_start(today)
    months = [add_months(base, -2), add_months(base, -1), base]
    keys = [month_key(m) for m in months]
    labels = [month_label(m) for m in months]

    svc = daily_counts.copy()
    svc = svc.reindex(columns=keys)
    svc = svc.cumsum()
    svc.columns = labels
    return svc


def build_sales_cumsum_like_svc(today, svc_cumsum, scale=4.0):
    # Sales를 SVC와 비슷한 흐름으로 만들되 스케일만 키움
    sales = svc_cumsum.copy()
    sales = sales * float(scale)
    return sales


# ---------------- event table: small but consistent ----------------
def make_svc_table(today, n_rows, month_bias=(0.15, 0.30, 0.55)):
    symptoms = ["DRAIN", "EXPLANATION", "INSTALLATION", "NOISE", "OTHER", "PCB"]
    details  = ["Defective", "NoPower", "NotWorking", "ErrorCode", "Loose"]
    parts    = ["PCB", "Motor", "Pump", "Valve", "Sensor"]

    base = month_start(today)
    m2, m1, m0 = add_months(base, -2), add_months(base, -1), base

    bucket = (
        [m2] * max(1, int(month_bias[0] * 100)) +
        [m1] * max(1, int(month_bias[1] * 100)) +
        [m0] * max(1, int(month_bias[2] * 100))
    )

    rows = []
    for _ in range(int(n_rows)):
        m = choice(bucket)
        end = last_day(m)
        dd = randint(1, end)
        d = date(m.year, m.month, dd)
        if d > today:
            d = today

        rows.append({
            "Symptom": choice(symptoms),
            "Details": choice(details),
            "Parts": choice(parts),
            "Repair_No": "RNN" + str(randint(10_000_000, 99_999_999)),
            "Serial_No": f"{randint(100,999)}TN{randint(10_000_000, 99_999_999)}",
            "Report_Date": d.strftime("%Y-%m-%d"),
        })

    svc_data = pd.DataFrame(rows)
    svc_data.index = range(1, len(svc_data) + 1)
    return svc_data


# ==========================
#   BUILD ALL EXPORTS
# ==========================
try:
    today = date.today()

    # 하루 단위 고정(재시작해도 같은 날이면 동일)
    s = today.toordinal()
    seed(s)
    np.random.seed(s % (2**32 - 1))

    # "실무처럼" 너무 과하지 않은 크기
    TOTAL_SVC = randint(3500, 5500)   # 그래프용 총량(집계)
    TABLE_ROWS = 1200                # HTML 테이블 행 수 (로딩속도용)

    # 1) 그래프용 SVC (빠름)
    daily_counts = generate_daily_counts(today, TOTAL_SVC, month_ratios=(0.30, 0.33, 0.37), smooth=4.2)
    YearSVCData = build_svc_cumsum_from_daily(today, daily_counts)

    legend2M, legend1M, legend0M = YearSVCData.columns.tolist()
    ABlabels = list(range(1, 32))

    Avalues2M = YearSVCData[legend2M].dropna().tolist()
    Avalues1M = YearSVCData[legend1M].dropna().tolist()
    Avalues0M = YearSVCData[legend0M].dropna().tolist()

    # 2) Sales (SVC 흐름 기반 + 스케일만 키움)
    SalesData = build_sales_cumsum_like_svc(today, YearSVCData, scale=4.0)

    Bvalues2M = SalesData[legend2M].dropna().tolist()
    Bvalues1M = SalesData[legend1M].dropna().tolist()
    Bvalues0M = SalesData[legend0M].dropna().tolist()

    # 3) 이벤트 테이블(svc_data) - 기존 코드 호환
    svc_data = make_svc_table(today, n_rows=TABLE_ROWS, month_bias=(0.15, 0.30, 0.55))

    # 너가 요구한 형태 그대로:
    svc_data.index = range(1, len(svc_data) + 1)
    svc_data.columns = ["Symptom","Details","Parts","Repair_No","Serial_No","Report_Date"]

    # 4) min_svc_data (legend0M == "YYYY.MM" 사용)
    min_svc_data = svc_data.loc[svc_data['Report_Date'].str.contains(legend0M.replace(".", "-"))]
    min_svc_data.index = range(1, len(min_svc_data) + 1)

    # 5) Pie labels/values
    Plabels = svc_data["Symptom"].value_counts(dropna=True).index.tolist()
    Pvalues = svc_data["Symptom"].value_counts(dropna=True).tolist()

    # 6) HTML (네가 쓰던 방식 그대로)
    svc_data_html = svc_data.to_html()
    svc_data_html = svc_data_html.replace('border="1" class="dataframe"', 'id="datatablesSimple"' )
    svc_data_html = svc_data_html.replace('<tr style="text-align: right;">','<tr>')
    svc_data_html = svc_data_html.replace('<th></th>','<th>No</th>')

    min_data_html = min_svc_data.to_html()
    min_data_html = min_data_html.replace('border="1" class="dataframe"', 'id="datatablesSimple"' )
    min_data_html = min_data_html.replace('<tr style="text-align: right;">','<tr>')
    min_data_html = min_data_html.replace('<th></th>','<th>No</th>')

    # 7) FDR/Target 스케일 (원한 수준)
    Today_SVC = int(daily_counts[month_key(month_start(today))].dropna().sum())
    Today_Sales = float(SalesData[legend0M].dropna().iloc[-1]) if len(SalesData[legend0M].dropna()) else 1.0

    # 어제는 살짝 낮게(실무 느낌)
    Yesterday_SVC = max(0, int(Today_SVC * 0.995))
    Yesterday_Sales = max(1.0, float(Today_Sales * 0.997))

    Today_FDR = round(Today_SVC * 100 / max(Today_Sales, 1.0), 2)
    Yesterday_FDR = round(Yesterday_SVC * 100 / max(Yesterday_Sales, 1.0), 2)

    Target = Today_FDR + randint(1, 10) / 100  # ✅ 요청 스케일

except Exception:
    # import 자체가 죽지 않도록 최소값 보장
    legend2M = legend1M = legend0M = month_label(date.today())
    ABlabels = list(range(1, 32))

    Avalues2M = Avalues1M = Avalues0M = []
    Bvalues2M = Bvalues1M = Bvalues0M = []

    Plabels = []
    Pvalues = []

    svc_data_html = "<table id='datatablesSimple'></table>"
    min_data_html = "<table id='datatablesSimple'></table>"

    Today_FDR = Yesterday_FDR = 0.0
    Target = 0.05


if __name__ == "__main__":
    print("legend:", legend2M, legend1M, legend0M)
    print("len A0:", len(Avalues0M), "len B0:", len(Bvalues0M))
    print("Plabels:", Plabels[:5])
    print("FDR:", Yesterday_FDR, "->", Today_FDR, "Target:", Target)
