from django.contrib import admin
from django import forms            # ✅ 추가
from django.utils.safestring import mark_safe
import json                         # ✅ 추가

from .models import (
    TeamPrediction, TeamPredictionHistory,
    SapRaw, SapProcessed, CctrRaw, CctrProcessed,
    GateRaw, GateProcessed, RaKey, PredictionClose, ProcessClose
)

MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]  # ✅

def _normalize_month_order(md):
    """dict/list/None → {jan..dec} 순서 dict"""
    if not md:
        base = {}
    elif isinstance(md, list):
        base = {row.get("month"): row for row in md if isinstance(row, dict) and "month" in row}
    elif isinstance(md, dict):
        base = md
    else:
        base = {}
    return {m: (base.get(m) or {}) for m in MONTH_KEYS}

def _default_monthly_dict():
    return {m: {"sales": 0.0, "gross_profit": 0.0, "flag": "closed"} for m in MONTH_KEYS}

# -----------------------
# 공용: monthly_data 단일 필드만 편집 (Textarea)
# -----------------------
class MonthlyDataSingleFieldForm(forms.ModelForm):
    # 모델의 JSONField를 텍스트로 보여주고/받기
    monthly_data = forms.CharField(
        label="monthly_data (edit as JSON, jan→dec)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 18, "style": "font-family:monospace;"}),
        help_text="예) {'jan': {'sales':0,'gross_profit':0,'flag':'closed'}, ..., 'dec': {...}}"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = getattr(self, "instance", None)
        if inst and getattr(inst, "pk", None):
            ordered = _normalize_month_order(getattr(inst, "monthly_data", None))
        else:
            ordered = _default_monthly_dict()
        # 초기 표시를 항상 jan→dec 정렬 JSON 문자열로
        self.initial["monthly_data"] = json.dumps(ordered, ensure_ascii=False, indent=2)

    def clean_monthly_data(self):
        raw = self.cleaned_data.get("monthly_data", "").strip()
        if not raw:
            # 비우면 기본 스켈레톤
            data = _default_monthly_dict()
        else:
            try:
                data = json.loads(raw)
            except Exception as e:
                raise forms.ValidationError(f"유효한 JSON이 아닙니다: {e}")
        data = _normalize_month_order(data)

        # 값 검증/캐스팅
        for m in MONTH_KEYS:
            cell = data.get(m) or {}
            try:
                cell["sales"] = float(cell.get("sales", 0) or 0)
            except Exception:
                raise forms.ValidationError(f"{m}.sales 는 숫자여야 합니다.")
            try:
                cell["gross_profit"] = float(cell.get("gross_profit", 0) or 0)
            except Exception:
                raise forms.ValidationError(f"{m}.gross_profit 는 숫자여야 합니다.")
            flag = cell.get("flag", "closed")
            cell["flag"] = flag if flag is not None else "closed"
            data[m] = cell
        return data

# -----------------------
# 등록만
# -----------------------
admin.site.register(SapRaw)
admin.site.register(CctrRaw)
admin.site.register(CctrProcessed)
admin.site.register(GateRaw)
admin.site.register(GateProcessed)
admin.site.register(RaKey)
admin.site.register(PredictionClose)
admin.site.register(ProcessClose)

# -----------------------
# TeamPrediction
# -----------------------
class TeamPredictionAdminForm(MonthlyDataSingleFieldForm):
    class Meta:
        model = TeamPrediction
        fields = "__all__"

@admin.register(TeamPrediction)
class TeamPredictionAdmin(admin.ModelAdmin):
    form = TeamPredictionAdminForm  # ✅ 단일 필드 폼 적용
    list_display = (
        "id", "operation_team","shared_team", "project_code",
        "status","project_category",
        "sales_total", "gross_profit_total"
    )
    search_fields = ("project_code", "project_detail", "group_name", "client_name")
    list_filter = ("status", "term", "project_category", "operation_team", "shared_team")
    readonly_fields = ("id","sales_total", "gross_profit_total", "created_at", "updated_at")
    ordering = ("-id",)

    fieldsets = (
        ("📁 기본 정보", {
            "fields": ("id","year","term", "category","project_code", "project_detail", "project_category", "status","revenue_type","memo")
        }),
        ("👥 고객/조직", {
            "fields": ("div", "group_name", "operation_team",  "shared_team", "shared_dominate","dominant","ship_to_party", "client_name", "headquarter")
        }),
        ("📊 매출 데이터", {
            # ✅ monthly_data 한 필드만 (편집 가능)
            "fields": ("monthly_data", "sales_total", "gross_profit_total")
        }),
        ("🕐 메타 정보", {
            "fields": ("owner", "created_at", "updated_at")
        }),
    )

# -----------------------
# SapProcessed
# -----------------------
class SapProcessedAdminForm(MonthlyDataSingleFieldForm):
    class Meta:
        model = SapProcessed
        fields = "__all__"

@admin.register(SapProcessed)
class SapProcessedAdmin(admin.ModelAdmin):
    form = SapProcessedAdminForm  # ✅ 단일 필드 폼 적용
    list_display = (
        "id", "batch_no","project_code", "project_detail",
        "category", "group_name","operation_team__code",
        "sales_total", "gross_profit_total"
    )
    search_fields = ("project_code", "project_detail", "group_name", "client_name")
    list_filter = ("id", "batch_no","project_code", "project_detail","category")
    readonly_fields = ("id","sales_total", "gross_profit_total", "created_at", "updated_at")
    ordering = ("-updated_at",)

    fieldsets = (
        ("📁 기본 정보", {
            "fields": ("id","batch_no","year","term", "category","operation_team","project_code", "project_detail", "project_category", "revenue_type","status")
        }),
        ("👥 고객/조직", {
            "fields": ("div", "group_name", "ship_to_party", "client_name", "headquarter")
        }),
        ("📊 매출 데이터", {
            # ✅ monthly_data 한 필드만 (편집 가능)
            "fields": ("monthly_data", "sales_total", "gross_profit_total")
        }),
        ("🕐 메타 정보", {
            "fields": ("owner", "created_at", "updated_at")
        }),
    )

# -----------------------
# History
# -----------------------
@admin.register(TeamPredictionHistory)
class TeamPredictionHistoryAdmin(admin.ModelAdmin):
    list_display = ("id","team_prediction_display","action","changed_by","changed_at","changed_fields_display")

    def team_prediction_display(self, obj):
        return f"ID {obj.team_prediction_id}" if obj.team_prediction_id else "Deleted"
    team_prediction_display.short_description = "TeamPrediction"

    def changed_fields_display(self, obj):
        return ", ".join(obj.changed_fields.keys()) if obj.changed_fields else "-"
    changed_fields_display.short_description = "Changed Fields"
