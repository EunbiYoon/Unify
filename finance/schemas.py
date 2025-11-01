from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import Optional, Union, List, Dict, Any
from enum import Enum
from datetime import date, datetime
from ninja import Schema
from decimal import Decimal
from typing import List, Optional

# ===================================================================
# ✅ 값 넣기
# ===================================================================

# ✅ 월별 구조 정의
class MonthlyEntry(BaseModel):
    sales: int = 0
    gross_profit: int = 0
    flag: str = "active"


# ✅ 전체 월별 데이터를 위한 스키마
class MonthlyDataSchema(BaseModel):
    jan: MonthlyEntry = MonthlyEntry()
    feb: MonthlyEntry = MonthlyEntry()
    mar: MonthlyEntry = MonthlyEntry()
    apr: MonthlyEntry = MonthlyEntry()
    may: MonthlyEntry = MonthlyEntry()
    jun: MonthlyEntry = MonthlyEntry()
    jul: MonthlyEntry = MonthlyEntry()
    aug: MonthlyEntry = MonthlyEntry()
    sep: MonthlyEntry = MonthlyEntry()
    oct: MonthlyEntry = MonthlyEntry()
    nov: MonthlyEntry = MonthlyEntry()
    dec: MonthlyEntry = MonthlyEntry()

class User_Out(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

class Team_Out(Schema):
    team_name: str

class MergeTeam_Out(Schema):
    team_name: str
    code: str

# ===================================================================
# ✅ SAP Proceed -> same with Team Prediction except Memo
# ===================================================================
class SapProcessed_In(Schema):
    # 운영팀
    operation_team : str
    # 프로젝트 명 
    project_detail: str
    # 잡코드
    project_code: str
    # 광고주명
    client_name: Optional[str] = None
    # 광고주 코드
    ship_to_party: Optional[str] = None
    # 수익유형
    revenue_type: Optional[str] = None
    # 기획협업 본부
    headquarter: Optional[str]=None

class CctrProcessedOut(BaseModel):
    id: int
    team_name: str
    code: str
    model_config = ConfigDict(from_attributes=True)  # ✅ 이거 추가

class SapProcessed_Out(SapProcessed_In):
    id: int
    operation_team: Optional[CctrProcessedOut] = None
    batch_no: Optional[int] = None
    category: str
    div: Optional[str] = None
    group_name: Optional[str] = None
    year: int
    status: str
    term: str
    owner: str
    project_category: Optional[str] = None
    monthly_data: MonthlyDataSchema = Field(default_factory=MonthlyDataSchema)
    owner: User_Out
    sales_total: int
    gross_profit_total: int
    created_at: datetime
    updated_at: datetime

class SapProcessedResponse(BaseModel):
    success: bool
    message: str
    id: Optional[int]
    data: Optional[SapProcessed_Out]


# ===================================================================
# ✅ Team Prediction 
# ===================================================================

# # ✅ ManyToMany 직렬화용
# class MemoTag_Out(BaseModel):
#     id: int
#     name: str
#     created_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# # ✅ MemoTag 입력 스키마
# class MemoTag_In(BaseModel):
#     name: str

class TeamPrediction_In(SapProcessed_In):
    # 프로젝트 분류
    project_category: str
    # 상태
    status: str 
    # 협업 부서
    shared_team: Optional[str] = None
    # 메모
    memo: Optional[str] = None

class Pred_Out(BaseModel):
    id : int

class TeamPrediction_Out(TeamPrediction_In):
    id: int
    div: Optional[str] = None
    group_name: Optional[str] = None
    category: str
    year: int
    status: str
    term: str
    owner: str
    operation_team: Optional[Team_Out]=None
    shared_team: Optional[Team_Out]=None
    shared_dominate: bool | None
    dominant: Optional[Pred_Out]=None
    owner: User_Out
    monthly_data: MonthlyDataSchema = Field(default_factory=MonthlyDataSchema)
    sales_total: int
    gross_profit_total: int
    created_at: datetime
    updated_at: datetime

class MergeTeamPrediction_Out(TeamPrediction_In):
    id: int
    div: Optional[str] = None
    group_name: Optional[str] = None
    category: str
    year: int
    status: str
    term: str
    owner: str
    operation_team: Optional[MergeTeam_Out]=None
    shared_team: Optional[MergeTeam_Out]=None
    shared_dominate: bool | None
    dominant: Optional[Pred_Out]=None
    monthly_data: MonthlyDataSchema = Field(default_factory=MonthlyDataSchema)
    owner: User_Out
    sales_total: int
    gross_profit_total: int
    created_at: datetime
    updated_at: datetime

class MonthlyEntryPartial(BaseModel):
    sales: Optional[int] = None
    gross_profit: Optional[int] = None

class MonthlyUpdate(BaseModel):
    monthly_data: Dict[str, MonthlyEntryPartial]

    class Config:
        extra = "forbid"

class TeamPredictionResponse(BaseModel):
    success: bool
    message: str
    id: Optional[int]
    data: Optional[TeamPrediction_Out]

# ===================================================================
# ✅ Finance Schema
# ===================================================================
class Merge_Out(BaseModel):
    team_predictions: List[MergeTeamPrediction_Out]
    sap_processed: List[SapProcessed_Out]

class FilterTeam_Schema(BaseModel):
    filtered_team: Optional[List[str]] = None
# ===================================================================
# ✅ RAW data fron upload template
# ===================================================================

class SapRaw_In(Schema):
    item: Optional[str] = None
    version: Optional[str] = None
    cocd: Optional[str] = None
    consoli_company_t: Optional[str] = None
    busa: Optional[str] = None
    description: Optional[str] = None
    period: Optional[Union[str, int]] = None
    tr_prt: Optional[str] = None
    trading_partner_t: Optional[str] = None
    representative_custo: Optional[str] = None
    representative_custo_t: Optional[str] = None
    domestic_overseas_t: Optional[str] = None
    exsiting_new_t: Optional[str] = None
    compensation_type: Optional[str] = None
    compensation_type_t: Optional[str] = None
    hq_local_t: Optional[str] = None
    rhq_t: Optional[str] = None
    customer: Optional[str] = None
    custmer_t: Optional[str] = None
    product: Optional[str] = None
    product_number_t: Optional[str] = None
    soff: Optional[str] = None
    sales_office_t: Optional[str] = None
    ship_to: Optional[str] = None
    ship_to_party_t: Optional[str] = None
    bill_to: Optional[str] = None
    bill_to_party_t: Optional[str] = None
    trading_type: Optional[str] = None
    customer_group_2: Optional[str] = None
    matl_group: Optional[str] = None
    di_category: Optional[str] = None
    di_category_t: Optional[str] = None
    appropriate_project: Optional[str] = None
    wbs_element: Optional[str] = None
    project_t: Optional[str] = None
    ph01_2: Optional[str] = None
    prodhier01_2_t: Optional[str] = None
    billing_amt_hq: Optional[Decimal] = None
    t_sales: Optional[Decimal] = None
    t_cogs: Optional[Decimal] = None
    t_revenue: Optional[Decimal] = None
    t_labor_cost: Optional[Decimal] = None
    t_expense: Optional[Decimal] = None
    t_non_operating: Optional[Decimal] = None
    t_net_income_before_tax: Optional[Decimal] = None

# ✅ CCTR 입력 스키마
class CctrRaw_In(Schema):
    company: str
    ba: str
    cost_center: str
    name_20: Optional[str] = None
    name_40: Optional[str] = None
    type_t: Optional[str] = None
    allocation_standard: Optional[str] = None
    cost_center_category: Optional[str] = None
    sales_office_cd: Optional[str] = None


# ✅ Gate 입력 스키마 (모델과 동일하게 전부 문자열로 변경)
class GateRaw_In(Schema):
    job: Optional[str] = None
    compensation_type: Optional[str] = None
    job_name: Optional[str] = None
    project: Optional[str] = None
    job_type_group: Optional[str] = None
    job_type: Optional[str] = None
    ad_team: Optional[str] = None
    advertiser_id: Optional[str] = None
    advertiser_name: Optional[str] = None
    status: Optional[str] = None
    job_category: Optional[str] = None
    compensation_type_1: Optional[str] = None
    existing_new: Optional[str] = None
    production_type: Optional[str] = None
    advertiser_manager: Optional[str] = None
    product_brand: Optional[str] = None
    contract_type: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    advertiser_ot_date: Optional[str] = None
    ad_team_manager: Optional[str] = None
    production_team: Optional[str] = None
    production_team_cd: Optional[str] = None
    code_approver: Optional[str] = None
    settlement_team: Optional[str] = None
    virtual_settlement_dept: Optional[str] = None
    settlement_manager: Optional[str] = None
    pm_team: Optional[str] = None
    pm_manager: Optional[str] = None
    billing: Optional[str] = None
    plan_time: Optional[float] = None      # ✅ 숫자 그대로 둠
    contract_time: Optional[float] = None  # ✅ 숫자 그대로 둠
    staff_count: Optional[int] = None      # ✅ 숫자 그대로 둠
    created_date: Optional[str] = None
    created_by: Optional[str] = None
    main_staff_ae: Optional[str] = None
    active_executor: Optional[str] = None
    active_date: Optional[str] = None
    job_deadline: Optional[str] = None
    contract_job: Optional[str] = None
    ref_project: Optional[str] = None
    log_project_key: Optional[str] = None
    rfp_q_no: Optional[str] = None
    bml_type: Optional[str] = None
    legal_contract_no: Optional[str] = None
    connector: Optional[str] = None
    connection_date: Optional[str] = None
    billing_spot_trade: Optional[str] = None
    description: Optional[str] = None
    ra_key: Optional[str] = None
    ba_code: Optional[str] = None
    business_area: Optional[str] = None

# ===================================================================
# ✅ 파일 업로드
# ===================================================================
class FilePathsIn(BaseModel):
    sap_path: str
    cctr_path: str
    gate_path: str

class ProcessResult(BaseModel):
    success: bool | None = None
    message: str | None = None
    rows_saved: int | None = None
    batch_no: int | None = None

class ProcessAllResponse(BaseModel):
    success: bool
    message: str
    results: dict[str, ProcessResult]

class UploadTempResult(BaseModel):
    success: bool
    is_valid: bool
    message: str
    temp_file_path: str

class FinalizeUploadRequest(BaseModel):
    file_path: str

# ===================================================================
# ✅ 이메일 스키마 
# ===================================================================

class ApprovalEmailRequest(BaseModel):
    project_id: int
    recipients: List[EmailStr]  # 이메일 리스트 검증


# ===================================================================
# ✅ 마감 스키마 
# ===================================================================
class PredictionCloseIn(Schema):
    year: int
    month: int