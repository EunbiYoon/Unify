from django.db import models
from django.utils.timezone import now, localtime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.conf import settings
import re
from django.contrib.auth import get_user_model
from datetime import datetime
from pydantic import BaseModel
from datetime import date
from dateutil.relativedelta import relativedelta
from account.models import Division, Group, Team

def get_first_user():
    User = get_user_model()
    return User.objects.order_by("id").first()

class CctrProcessed(models.Model):  # ✅ 원가센터 처리본
    id = models.BigAutoField(primary_key=True)
    batch_no = models.BigIntegerField(db_index=True)
    code = models.CharField(max_length=4)

    division_parent = models.ForeignKey(
        Division, on_delete=models.CASCADE,
        related_name="cctr_in_division"
    )
    group_parent = models.ForeignKey(
        Group, on_delete=models.CASCADE,
        related_name="cctr_in_group"
    )

    team_name = models.CharField(max_length=20)

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cctr_processed"

    def __str__(self):
        return f"[{self.id}] {self.code} :: {self.team_name}"


# class MemoTag(models.Model):
#     id = models.BigAutoField(primary_key=True)  # ✅ 기본 키
#     """Memo 내용 기반 자동 생성 태그"""
#     name = models.CharField(max_length=100, unique=True)
#     owner = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="%(class)s_owner",
#         default=get_first_user  # ✅ default로 첫 번째 유저
#     )
#     created_at = models.DateTimeField(default=now)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "memo_tag"

#     def __str__(self):
#         return self.name

# ✅ 월별 기본 데이터 함수 (lambda → 함수)
def default_monthly_data():
    return {
        m: {"sales": 0, "gross_profit": 0, "flag": "active"}
        for m in [
            "jan", "feb", "mar", "apr", "may", "jun",
            "jul", "aug", "sep", "oct", "nov", "dec"
        ]
    }

def status_choice():
    STATUS_CHOICES = [
        ("Progress", "Progress"),
        ("Hold", "Hold"),
        ("Stop", "Stop"),
    ]
    return STATUS_CHOICES

def category_choice():
    CATEGORY_CHOICES=[
        ('General', 'General'),
        ('Sharing', 'Sharing'),
        ('Will', 'Will'),
        ('NoCode', 'NoCode')
    ]
    return CATEGORY_CHOICES

def get_last_month_year():
    last_month = date.today() - relativedelta(months=1)
    return last_month.year

def term_default():
    current_month = datetime.now().month
    MONTH_MAP = {10: "A", 11: "B", 12: "C"}
    term = "T0" + MONTH_MAP.get(current_month, str(current_month))
    return term

class FinanceCommonFields(models.Model):
    id = models.BigAutoField(primary_key=True)  # ✅ 기본 키
    status = models.CharField(
        max_length=20,
        choices=status_choice(),
        
        default="Progress"
    )
    year = models.IntegerField(default=get_last_month_year)
    term = models.CharField(default=term_default)
    div = models.CharField(max_length=255, null=True, blank=True)
    group_name = models.CharField(max_length=255, null=True, blank=True)
    ship_to_party = models.CharField(max_length=255, null=True, blank=True)
    client_name = models.CharField(max_length=255, null=True, blank=True)
    project_category = models.CharField(
        max_length=20,
        choices=category_choice(),
        default="General"
    )
    project_code = models.CharField(max_length=255)
    project_detail = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_owner",
        default=get_first_user  # ✅ default로 첫 번째 유저
    )

    revenue_type = models.CharField(max_length=255, null=True, blank=True)
    headquarter = models.CharField(max_length=255, null=True, blank=True)
    # ✅ 월별 데이터 (JSON)
    monthly_data = models.JSONField(default=default_monthly_data)

    # ✅ 총합 자동 계산 (DB 필드 아님)
    @property
    def sales_total(self):
        return sum(v.get("sales", 0) for v in self.monthly_data.values())

    @property
    def gross_profit_total(self):
        return sum(v.get("gross_profit", 0) for v in self.monthly_data.values())

    # ✅ operation_team에서 div, group_name 자동 설정
    def set_div_group_from_operation_team(self, operation_team: str):
        try:
            _, div_raw, group, *_ = operation_team.split("-")
            self.div = div_raw.upper()
            self.group_name = group
        except Exception:
            pass  # 잘못된 문자열이면 무시

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # ✅ DB에는 테이블이 생성되지 않음


class TeamPrediction(FinanceCommonFields):  # ✅ 예측 데이터
    category = models.CharField(max_length=255, default="예상")
    operation_team = models.ForeignKey(
        "account.Team",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="team_predictions",         # ← SapProcessed와 다르게
        related_query_name="team_prediction",    # ← SapProcessed와 다르게
    )
    shared_team = models.ForeignKey(
        "account.Team",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="shared_team_predictions",  # ← 이것도 고유하게
        related_query_name="shared_team_prediction",
    )
    memo = models.CharField(null=True, blank=True)
    # ✅ 지배/종속 구분
    shared_dominate = models.BooleanField(null=True, blank=True)
    # ✅ 지배 인스턴스를 가리키는 자가 참조 FK (종속만 채워짐)
    dominant = models.ForeignKey(
        "self", null=True, blank=True,
        related_name="dependents", on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        if self.operation_team and self.operation_team.team_name:
            parts = self.operation_team.team_name.split("-")
            if len(parts) >= 4:
                self.div = parts[1]
                self.group_name = parts[2]
        super().save(*args, **kwargs)

    class Meta:
        db_table = "team_prediction"


class TeamPredictionHistory(models.Model):  # ✅ TeamPrediction 이력 로그
    id = models.BigAutoField(primary_key=True)  # ✅ 기본 키
    team_prediction = models.ForeignKey("TeamPrediction", on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=[("created", "created"), ("updated", "updated"), ("deleted", "deleted")])
    changed_at = models.DateTimeField(default=now)

    previous_snapshot = models.JSONField(null=True, blank=True)
    new_snapshot = models.JSONField(null=True, blank=True)
    changed_fields = models.JSONField(null=True, blank=True)

    # ✅ 변경한 사용자
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_first_user),
        related_name="team_prediction_changes"
    )
    class Meta:
        db_table = "team_prediction_history"

class PredictionClose(models.Model):
    year = models.IntegerField()  # 예: 2025
    month = models.IntegerField()  # 예: 8 (1~12)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preidiction_closed_months"
    )
    action = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=now)  # 마감 시점

    class Meta:
        db_table = "prediction_close"

    def __str__(self):
        return f"{self.year}년 {self.month}월 마감"

class ProcessClose(models.Model):
    year = models.IntegerField()  # 예: 2025
    month = models.IntegerField()  # 예: 8 (1~12)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="process_closed_months"
    )
    timestamp = models.DateTimeField(default=now)  # 마감 시점

    class Meta:
        db_table = "process_close"

    def __str__(self):
        return f"{self.year}년 {self.month}월 마감"

class CctrRaw(models.Model):  # ✅ 원가센터 원본
    id = models.BigAutoField(primary_key=True)  # ✅ 기본 키
    batch_no = models.BigIntegerField(db_index=True)  # 또는 CharField도 가능
    company = models.CharField(max_length=10)
    ba = models.CharField(max_length=10)
    cost_center = models.CharField(max_length=20, blank=True)
    name_20 = models.CharField(max_length=20)
    name_40 = models.CharField(max_length=40)
    type_t = models.CharField(max_length=20)
    allocation_standard = models.CharField(max_length=50, blank=True, null=True)
    cost_center_category = models.CharField(max_length=5)
    sales_office_cd = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cctr_raw"

    def __str__(self):
        return f"[{self.id}] {self.sales_office_cd} - {self.name_20}"


class GateRaw(models.Model):  # ✅ GATE 원본
    id = models.BigAutoField(primary_key=True)  # ✅ 기본 키
    batch_no = models.BigIntegerField(db_index=True)  # 또는 CharField도 가능
    job = models.CharField(max_length=255, null=True, blank=True)
    compensation_type = models.CharField(max_length=255, null=True, blank=True)
    job_name = models.CharField(max_length=255, null=True, blank=True)
    project = models.CharField(max_length=255, null=True, blank=True)
    job_type_group = models.CharField(max_length=255, null=True, blank=True)
    job_type = models.CharField(max_length=255, null=True, blank=True)
    ad_team = models.CharField(max_length=255, null=True, blank=True)
    advertiser_id = models.CharField(max_length=255, null=True, blank=True)
    advertiser_name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    job_category = models.CharField(max_length=255, null=True, blank=True)
    compensation_type_1 = models.CharField(max_length=255, null=True, blank=True)
    existing_new = models.CharField(max_length=255, null=True, blank=True)
    production_type = models.CharField(max_length=255, null=True, blank=True)
    advertiser_manager = models.CharField(max_length=255, null=True, blank=True)
    product_brand = models.CharField(max_length=255, null=True, blank=True)
    contract_type = models.CharField(max_length=255, null=True, blank=True)
    period_start = models.CharField(max_length=255, null=True, blank=True)
    period_end = models.CharField(max_length=255, null=True, blank=True)
    advertiser_ot_date = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.CharField(max_length=255, null=True, blank=True)
    active_date = models.CharField(max_length=255, null=True, blank=True)
    job_deadline = models.CharField(max_length=255, null=True, blank=True)
    connection_date = models.CharField(max_length=255, null=True, blank=True)
    ad_team_manager = models.CharField(max_length=255, null=True, blank=True)
    production_team = models.CharField(max_length=255, null=True, blank=True)
    production_team_cd = models.CharField(max_length=255, null=True, blank=True)
    code_approver = models.CharField(max_length=255, null=True, blank=True)
    settlement_team = models.CharField(max_length=255, null=True, blank=True)
    virtual_settlement_dept = models.CharField(max_length=255, null=True, blank=True)
    settlement_manager = models.CharField(max_length=255, null=True, blank=True)
    pm_team = models.CharField(max_length=255, null=True, blank=True)
    pm_manager = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    main_staff_ae = models.CharField(max_length=255, null=True, blank=True)
    active_executor = models.CharField(max_length=255, null=True, blank=True)
    billing = models.CharField(max_length=255, null=True, blank=True)
    plan_time = models.CharField(max_length=255, null=True, blank=True)
    contract_time = models.CharField(max_length=255, null=True, blank=True)
    staff_count = models.CharField(max_length=255, null=True, blank=True)
    contract_job = models.CharField(max_length=255, null=True, blank=True)
    ref_project = models.CharField(max_length=255, null=True, blank=True)
    log_project_key = models.CharField(max_length=255, null=True, blank=True)
    rfp_q_no = models.CharField(max_length=255, null=True, blank=True)
    bml_type = models.CharField(max_length=255, null=True, blank=True)
    legal_contract_no = models.CharField(max_length=255, null=True, blank=True)
    connector = models.CharField(max_length=255, null=True, blank=True)
    billing_spot_trade = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    ra_key = models.CharField(max_length=255, null=True, blank=True)
    ba_code = models.CharField(max_length=255, null=True, blank=True)
    business_area = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gate_raw"

    def __str__(self):
        return f"[{self.id}] {self.batch_no} - {self.project}"




class GateProcessed(models.Model):  # ✅ GATE 처리본
    id = models.BigAutoField(primary_key=True)  # ✅ 기본 키
    batch_no = models.BigIntegerField(db_index=True)  # 또는 CharField도 가능
    job = models.CharField(max_length=255, null=True, blank=True)
    job_name = models.CharField(max_length=255, null=True, blank=True)
    ra_key = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gate_processed"

    def __str__(self):
        return f"[{self.id}] {self.batch_no} - {self.job_name} ({self.ra_key})"

class RaKey(models.Model):  # ✅ RA Key 관리
    id = models.BigAutoField(primary_key=True)  # ✅ 기본 키
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ra_key"

    def __str__(self):
        return f"{self.code} - {self.description}"


class SapRaw(models.Model):  # ✅ 원본 SAP 데이터
    id = models.BigAutoField(primary_key=True)  # ✅ 기본 키
    batch_no = models.BigIntegerField(db_index=True)  # 또는 CharField도 가능
    item = models.CharField(max_length=255, null=True, blank=True)
    version = models.CharField(max_length=255, null=True, blank=True)
    cocd = models.CharField(max_length=255, null=True, blank=True)
    consoli_company_t = models.CharField(max_length=255, null=True, blank=True)
    busa = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    period = models.CharField(max_length=255, null=True, blank=True)
    tr_prt = models.CharField(max_length=255, null=True, blank=True)
    trading_partner_t = models.CharField(max_length=255, null=True, blank=True)
    representative_custo = models.CharField(max_length=255, null=True, blank=True)
    representative_custo_t = models.CharField(max_length=255, null=True, blank=True)
    domestic_overseas_t = models.CharField(max_length=255, null=True, blank=True)
    exsiting_new_t = models.CharField(max_length=255, null=True, blank=True)
    compensation_type = models.CharField(max_length=255, null=True, blank=True)
    compensation_type_t = models.CharField(max_length=255, null=True, blank=True)
    hq_local_t = models.CharField(max_length=255, null=True, blank=True)
    rhq_t = models.CharField(max_length=255, null=True, blank=True)
    customer = models.CharField(max_length=255, null=True, blank=True)
    custmer_t = models.CharField(max_length=255, null=True, blank=True)
    product = models.CharField(max_length=255, null=True, blank=True)
    product_number_t = models.CharField(max_length=255, null=True, blank=True)
    soff = models.CharField(max_length=255, null=True, blank=True)
    sales_office_t = models.CharField(max_length=255, null=True, blank=True)
    ship_to = models.CharField(max_length=255, null=True, blank=True)
    ship_to_party_t = models.CharField(max_length=255, null=True, blank=True)
    bill_to = models.CharField(max_length=255, null=True, blank=True)
    bill_to_party_t = models.CharField(max_length=255, null=True, blank=True)
    trading_type = models.CharField(max_length=255, null=True, blank=True)
    customer_group_2 = models.CharField(max_length=255, null=True, blank=True)
    matl_group = models.CharField(max_length=255, null=True, blank=True)
    di_category = models.CharField(max_length=255, null=True, blank=True)
    di_category_t = models.CharField(max_length=255, null=True, blank=True)
    appropriate_project = models.CharField(max_length=255, null=True, blank=True)
    wbs_element = models.CharField(max_length=255, null=True, blank=True)
    project_t = models.CharField(max_length=255, null=True, blank=True)
    ph01_2 = models.CharField(max_length=255, null=True, blank=True)
    prodhier01_2_t = models.CharField(max_length=255, null=True, blank=True)

    billing_amt_hq = models.BigIntegerField(null=True, blank=True)
    t_sales = models.BigIntegerField(null=True, blank=True)
    t_cogs = models.BigIntegerField(null=True, blank=True)
    t_revenue = models.BigIntegerField(null=True, blank=True)
    t_labor_cost = models.BigIntegerField(null=True, blank=True)
    t_expense = models.BigIntegerField(null=True, blank=True)
    t_non_operating = models.BigIntegerField(null=True, blank=True)
    t_net_income_before_tax = models.BigIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sap_raw"
    def __str__(self):
        return f"[{self.id}] {self.batch_no} - {self.appropriate_project}"

class SapProcessed(FinanceCommonFields):
    batch_no = models.BigIntegerField(db_index=True)
    category = models.CharField(max_length=255, default="결산")
    operation_team = models.ForeignKey(
        "account.Team",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sap_processed_set",        # ← 고유
        related_query_name="sap_processed",      # ← 고유
    )
    div = models.CharField(max_length=50, null=True, blank=True)
    group_name = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "sap_processed"

    def save(self, *args, **kwargs):
        if self.operation_team and self.operation_team.team_name:
            parts = self.operation_team.team_name.split("-")
            if len(parts) >= 4:
                self.div = parts[1]
                self.group_name = parts[2]
        super().save(*args, **kwargs)
