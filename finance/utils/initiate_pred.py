import pandas as pd
import re
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from finance.models import TeamPrediction, PredictionClose
from account.models import Team
from datetime import datetime
from ninja.errors import HttpError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]

# 🔹 숫자 필드 정리 함수
def clean_numeric(v):
    if pd.isna(v):
        return None
    try:
        return int(round(float(Decimal(str(v)))))
    except (InvalidOperation, ValueError, TypeError):
        return None

# 🔹 문자열 필드 정리 함수
def clean_string(v):
    if pd.isna(v) or v is None:
        return None
    if isinstance(v, (int, float)):
        return None
    s = str(v).strip()
    return None if s in ["", "nan", "NaN", "0.0", "0", "-", "None"] else s

# 🔹 최신 PredictionClose 기준 flag 생성
def get_month_flags_by_closing():
    latest = PredictionClose.objects.order_by("-year", "-month").first()
    if not latest:
        raise ValueError("month_closing 데이터가 없습니다.")
    closing_month = int(latest.month)  # 1~12
    post_flag = "active" if str(latest.action).lower() == "active" else "closed"

    flags = {}
    for idx, key in enumerate(MONTH_KEYS, start=1):
        if idx <= closing_month:
            flags[key] = "hidden"
        else:
            flags[key] = post_flag
    return flags

# 🔹 한개도 없으면 한개 생성
def ensure_initial_month_closing_active(user=None):
    # 순환 import 방지
    from finance.models import PredictionClose
    if PredictionClose.objects.exists():
        return None  # 이미 있으면 아무 것도 안 함
    target = date.today() - relativedelta(months=2)
    obj = PredictionClose.objects.create(
        year=target.year,
        month=target.month,
        action="active",
        closed_by=(user if user and getattr(user, "is_authenticated", False) else None),
        # PredictionClose.timestamp가 auto_now_add가 아니면 유지
        timestamp=timezone.now(),
    )
    return obj

# 🔹 메인 로직: 업로드된 파일 처리
def process_uploaded_pred_file(file):
    try:
        # ✅ admin 유저 로드
        User = get_user_model()
        try:
            admin_user = User.objects.get(username="admin")
        except User.DoesNotExist:
            return {"success": False, "message": "admin 유저가 존재하지 않습니다."}

        # 마감 비어있으면 하나 생성
        if not PredictionClose.objects.exists():
            ensure_initial_month_closing_active(admin_user)
        
        # 엑셀 파일 로드
        xlsx = pd.ExcelFile(file.file)
        skiprows_for_target = 5
        target_sheets = ['sheet1']

        # 파일 이름에서 T코드 추출 (T코드가 없는 경우 UNKNOWN)
        match = re.search(r'T\d{2}', file.name)
        excel_version = match.group() if match else 'UNKNOWN'

        all_data = []

        # 시트별로 데이터 처리
        for sheet in xlsx.sheet_names:
            if sheet.lower() in target_sheets:
                df_raw = pd.read_excel(xlsx, sheet_name=sheet, skiprows=skiprows_for_target, header=None)
                df_raw.replace(['-', '제외', '', ' '], pd.NA, inplace=True)

                # 각 행에 대해 데이터 처리
                for _, row in df_raw.iterrows():
                    job_code_raw = clean_string(row[6])
                    job_code_cleaned = job_code_raw if job_code_raw else "Will"

                    operation_team_name = clean_string(row[3])
                    if not operation_team_name:
                        return {"success": False, "message": "operation_team_name이 비어있습니다."}

                    try:
                        operation_team = Team.objects.get(team_name=operation_team_name)
                    except Team.DoesNotExist:
                        return {"success": False, "message": f"Team '{operation_team_name}'가 존재하지 않습니다."}

                    all_data.append({
                        "category": clean_string(row[0]),
                        "div": clean_string(row[1]),
                        "group_name": clean_string(row[2]),
                        "operation_team": operation_team,
                        "ship_to_party": clean_string(row[4]),
                        "client_name": clean_string(row[5]),
                        "job_code": job_code_cleaned,
                        "project_detail": clean_string(row[7]),
                        "revenue_type": clean_string(row[8]),
                        "memo": clean_string(row[9]),
                        "headquarter": clean_string(row[10]),
                        "sales": [clean_numeric(row[i]) for i in range(11, 23)],
                        "gross": [clean_numeric(row[i]) for i in range(23, 35)],
                    })

        now_time = timezone.now()

        # ✅ Term 계산
        current_month = datetime.now().month
        MONTH_MAP = {10: "A", 11: "B", 12: "C"}
        term = "T0" + MONTH_MAP.get(current_month, str(current_month))

        # ✅ 최신 PredictionClose 기준 플래그
        month_flags = get_month_flags_by_closing()

        for data in all_data:
            monthly_data = {}
            for i, m in enumerate(MONTH_KEYS):
                monthly_data[m] = {
                    "sales": data["sales"][i] or 0,
                    "gross_profit": data["gross"][i] or 0,
                    "flag": month_flags[m],  # ✅ 플래그는 PredictionClose 기준
                }

            TeamPrediction.objects.create(
                term=term,
                category=data["category"] or "Unknown",
                div=data["div"],
                group_name=data["group_name"],
                operation_team=data["operation_team"],
                ship_to_party=data["ship_to_party"],
                client_name=data["client_name"],
                project_code=data["job_code"],
                project_detail=data["project_detail"],
                memo=data["memo"],
                revenue_type=data["revenue_type"],
                headquarter=data["headquarter"],
                monthly_data=monthly_data,
                created_at=now_time,
                updated_at=now_time
            )

        return {"success": True, "rows_saved": len(all_data)}

    except Exception as e:
        # 기타 예외는 400으로 통일
        raise HttpError(400, f"업로드 처리 중 오류: {e}")
