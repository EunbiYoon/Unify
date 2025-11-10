# Standard Library
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

# Django
from django.db import models, transaction, connection
from django.db.models import Q, Case, When, Value, IntegerField, Subquery, OuterRef, Max, QuerySet
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, render
# from django.utils import timezone
# from django.utils.timezone import now
from django.core.mail import EmailMessage
from django.core.files.storage import default_storage
from django.forms.models import model_to_dict
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.db.models import Case, When, Value, IntegerField
from django.http import FileResponse, Http404
from django.conf import settings

# Third-party
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from ninja import Router, File, Query
from ninja.errors import HttpError
from ninja.files import UploadedFile
from pydantic import BaseModel
from io import BytesIO
from django.db.models import QuerySet
from dateutil.relativedelta import relativedelta
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import re
import calendar

# Internal modules (views, utils, models, schemas)
from .schemas import (
    SapProcessed_In, SapProcessed_Out, SapProcessedResponse,
    TeamPrediction_Out, TeamPrediction_In, TeamPredictionResponse, MonthlyUpdate,
    SapRaw_In, CctrRaw_In, GateRaw_In, ApprovalEmailRequest,
    UploadTempResult, FilePathsIn, ProcessResult, ProcessAllResponse,
    FinalizeUploadRequest, Merge_Out, FilterTeam_Schema, PredictionCloseIn,
    MergeTeamPrediction_Out
)

from finance.models import (
    TeamPrediction, TeamPredictionHistory,
    SapRaw, CctrRaw, GateRaw, RaKey, SapProcessed, CctrProcessed, GateProcessed, PredictionClose, ProcessClose
)
from account.models import Division, Group, Team

from .helpers import (
    month_update, month_update_detail, reg_express, account_error, team_filter, month_create, team_error, save_instance, close_refresh, file_maker,
    flag_month,
)

from .utils import (
    initiate_pred
)

from .utils.column_maps import SAP_COL_MAP, CCTR_COL_MAP, GATE_COL_MAP
from .utils.upload_validation import validate_and_save_template
from .utils.initiate_rakey import initiate_rakey
# from .utils.send_email import send_project_sharing_email
from .utils.process_cctr import process_cctr
from .utils.process_gate import process_gate
from .utils.process_sap import process_sap

from finance.utils.finalize_upload import finalize_upload
from .signals import get_default_user
from ninja.security import django_auth

# Routers
home_router = Router(tags=["Home Page"])
pred_router = Router(tags=["[Project Page] Team Prediction Initialize + CRUD"],auth=django_auth)
job_router = Router(tags=["[Project Page] Project Job"])
sap_router = Router(tags=["[Project Page] SAP Raw & Transformation"])
cctr_router = Router(tags=["[Project Page] CCTR Raw & Transformation"])
gate_router = Router(tags=["[Project Page] GATE 3.0 Raw & Transformation"])
rakey_router = Router(tags=["[2nd Plan] RA Key CRUD"])
process_router = Router(tags=["[Project Page] Mapping SAP + CCTR + GATE + RAKey and Data Processing"])
merge_router = Router(tags=["[Report Page] Merge to Finance = TeamPrediction + SapProcessed"])
close_router = Router(tags=["[Project Page] Close Monthly Data"])
# email_router = Router(tags=["[2nd Plan] Email Send"])
db_router = Router(tags=["[Dev] DB -> Excel Transform"])

# Logger
import logging
logger = logging.getLogger(__name__)

# Month helpers
MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
MONTH_LABELS = {
    "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr", "may": "May", "jun": "Jun",
    "jul": "Jul", "aug": "Aug", "sep": "Sep", "oct": "Oct", "nov": "Nov", "dec": "Dec"
}

@home_router.get("", include_in_schema=False)
def finance_home(request):
    return render(request, 'finance_home.html')

# ===================================================================
# 🥳 Sample upload for Team Prediction (DEV / DB migration)
# ===================================================================
@pred_router.post("/upload-sample")
def upload_TeamPrediction_data(request, file: UploadedFile = File(...)):
    """DEV only: Upload TeamPrediction Excel and insert initial data. Test file: sample/pred_july_sample.xlsx"""
    account_error._superuser_error(request)
    result = initiate_pred.process_uploaded_pred_file(file)
    return JsonResponse(result)

# ===================================================================
# 🥳 Read predictions
# ===================================================================
@pred_router.get("/all/me", response=List[TeamPrediction_Out])
def find_my_team_predictions(request):
    """Fetch TeamPrediction data for the current user (both operation_team and shared_team rules)."""
    #account_error._login_error(request)

    # 1) Refresh flags to the latest state
    close_refresh._pred_close(TeamPrediction)

    # 2) Filter by team FK rules (operation_team / shared_team)
    rule_q = team_filter._pred_team(Team, TeamPrediction, request)
    qs = (
        TeamPrediction.objects
        .select_related("operation_team", "shared_team")
        .filter(rule_q)
        .distinct()
        .order_by("operation_team","-created_at")
    )
    logger.info("🔵 Filtered result count: %s", qs.count())
    return [TeamPrediction_Out.model_validate(obj, from_attributes=True) for obj in qs]

# ===================================================================
# 🥳 Create prediction
# ===================================================================
@pred_router.post("/new", response=TeamPredictionResponse)
def create_TeamPrediction(request, data: TeamPrediction_In):
    """Create a TeamPrediction record."""
    account_error._login_error(request)

    # 1) Validate operation/shared teams
    shared_dominate = None
    operation_team_instance, shared_team_instance = team_error._pred_team(data, Team, shared_dominate)

    # 2) Create monthly_data and origin instance
    origin_monthly_data = month_create._create_origin_monthly_data(request)
    origin_instance = save_instance._pred_origin(
        request, data, TeamPrediction,
        operation_team_instance, shared_team_instance,
        origin_monthly_data, None
    )
    if shared_team_instance:
        shared_monthly_data = month_create._create_shared_monthly_data(request)
        print(shared_monthly_data)
        _ = save_instance._pred_shared(
            request, data, TeamPrediction,
            operation_team_instance, shared_team_instance,
            shared_monthly_data, origin_instance
        )

    return TeamPredictionResponse(
        success=True,
        message=f"✅ Created TeamPrediction with ID {origin_instance.id}",
        id=origin_instance.id,
        data=TeamPrediction_Out.model_validate(origin_instance, from_attributes=True),
    )

# ===================================================================
# 🥳 Fetch single prediction
# ===================================================================
@pred_router.get("/detail/{id}", response=TeamPredictionResponse)
def get_TeamPrediction(request, id: int):
    """Fetch a single TeamPrediction by ID."""
    instance = get_object_or_404(TeamPrediction, id=id)
    return TeamPredictionResponse(
        success=True,
        message=f"✅ Fetched TeamPrediction with ID {instance.id}",
        id=instance.id,
        data=TeamPrediction_Out.model_validate(instance, from_attributes=True)
    )

# ===================================================================
# 🥳 Update prediction (with dependent handling)
# ===================================================================
@pred_router.put("/detail/{id}", response=TeamPredictionResponse)
def update_TeamPrediction(request, id: int, data: TeamPrediction_In):
    """Update TeamPrediction (handles dependent shared instances)."""
    account_error._login_error(request)

    # 1) Validate operation/shared teams based on current dominance
    sort_shared_dominate = TeamPrediction.objects.get(id=id).shared_dominate
    operation_team_instance, shared_team_instance = team_error._pred_team(data, Team, sort_shared_dominate)

    # 2) Update origin instance (monthly_data handled inside)
    origin_instance = save_instance._pred_origin(
        request, data, TeamPrediction,
        operation_team_instance, shared_team_instance,
        None, id
    )

    # 3) If category changed to non-sharing but dependent shared instance exists, delete it
    if data.project_category != "Sharing":
        qs = TeamPrediction.objects.filter(dominant=origin_instance, shared_dominate=False)
        if qs.exists():
            logger.info(f"Converted to non-sharing project → deleting dependent TeamPrediction(s): qs : {qs}")
            deleted_count, _ = qs.delete()
            logger.info(f"Deleted dependent TeamPrediction count: {deleted_count}")

    # 4) If shared team exists, update/create shared instance with negated monthly deltas
    if shared_team_instance:
        origin_monthly_data = origin_instance.monthly_data
        shared_monthly_data = month_update._update_shared_monthly_data(origin_monthly_data)
        _ = save_instance._pred_shared(
            request, data, TeamPrediction,
            operation_team_instance, shared_team_instance,
            shared_monthly_data, origin_instance
        )

    return TeamPredictionResponse(
        success=True,
        message=f"✅ Updated TeamPrediction with ID {origin_instance.id}",
        id=origin_instance.id,
        data=TeamPrediction_Out.model_validate(origin_instance, from_attributes=True)
    )

# ===================================================================
# 🥳 Update monthly_data like an Excel editor
# ===================================================================
@pred_router.put("/detail/monthly/{id}", response=TeamPredictionResponse)
def update_team_prediction_monthly_data(request, id: int, data: MonthlyUpdate):
    account_error._login_error(request)
    instance = get_object_or_404(TeamPrediction, id=id)

    # 1) Apply delta to base/origin instance
    base_before = instance.monthly_data or {}
    base_after  = reg_express._deep_merge_dict(base_before, data.monthly_data)
    instance.monthly_data = base_after
    instance._request_user = request.user
    instance.save()
    logger.info("✅ [shared_dominate=True] origin updated : %s", instance.id)

    # 2) If shared exists, update dependent shared instance by applying negative deltas
    if instance.shared_team:
        shared_obj = get_object_or_404(TeamPrediction, shared_dominate=False, dominant=instance)
        logger.info(f"✅ [shared_dominate=False] shared_obj: {shared_obj}")

        if shared_obj:
            month_update_detail._month_negately_data(data, shared_obj)
            shared_obj._request_user = request.user
            shared_obj.save()
            logger.info("🔁 shared updated: %s", shared_obj.id)
        else:
            logger.info("⚪ shared not found → skip")

    return TeamPredictionResponse(
        success=True,
        message=f"✅ Updated monthly_data for TeamPrediction ID {instance.id}",
        id=instance.id,
        data=TeamPrediction_Out.model_validate(instance, from_attributes=True),
    )

# ===================================================================
# 🥳 Data for create popup (org tree + choices)
# ===================================================================
@pred_router.get("/pop-up")
def get_division_group_team_tree_api(request):
    """Return Division → Group → Team tree and selection lists (including RAKey descriptions)."""
    results = []

    # Division → Group → Team
    divisions = Division.objects.prefetch_related("groups__teams_in_group")
    for division in divisions:
        div_name = division.division_name.split("-")[-1]
        division_data = {
            "division_name": div_name,
            "groups": []
        }

        for group in division.groups.all():
            group_name_clean = reg_express._strip_prefix(group.group_name, division.division_name)
            teams = [
                reg_express._strip_prefix(team.team_name, group.group_name)
                for team in group.teams_in_group.all()
            ]

            division_data["groups"].append({
                "group_name": group_name_clean,
                "teams": teams
            })

        results.append(division_data)

    # status/category choices
    status_choices = [choice[0] for choice in TeamPrediction._meta.get_field("status").choices]
    category_choices = [choice[0] for choice in TeamPrediction._meta.get_field("project_category").choices]

    # RAKey descriptions
    rakey_list = list(RaKey.objects.values_list("description", flat=True))

    return {
        "organization": results,
        "status_choices": status_choices,
        "category_choices": category_choices,
        "rakey_list": rakey_list
    }

# ===================================================================
# 🥳 Reset all TeamPrediction data
# ===================================================================
@pred_router.delete("/reset/records")
def delete_all_team_predictions(request):
    """Danger: delete all TeamPrediction rows and reset DB identity sequence."""
    account_error._superuser_error(request)

    if not request.user.is_superuser:
        raise HttpError(403, "Only admins can initialize this resource.")

    TeamPrediction.objects.all().delete()

    table_name = TeamPrediction._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")

    return {"success": True, "message": f"✅ Deleted all data and reset identity for table {table_name}"}

# ===================================================================
# 🥳 SAP template download
# ===================================================================
@sap_router.get("/download-template")
def download_sap_template(request):
    """Download Excel template for SAP upload."""
    file_path = os.path.join(settings.MEDIA_ROOT, "sql/sap_uploadTemplate.xlsx")
    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename="sap_uploadTemplate.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ===================================================================
# 🥳 SAP template upload (temp)
# ===================================================================
@sap_router.post("/upload-template-temp", response=UploadTempResult)
def upload_sap_template_temp(request, file: UploadedFile = File(...)):
    """Validate SAP template and save temp file path."""
    result = validate_and_save_template(file.file, SAP_COL_MAP, "sap")
    if not result["is_valid"]:
        raise HttpError(400, result["message"])
    return {
        "success": result["success"],
        "is_valid": result["is_valid"],
        "message": result["message"],
        "temp_file_path": result["temp_file_path"]
    }

# ===================================================================
# 🥳 CCTR template download
# ===================================================================
@cctr_router.get("/download-template")
def download_cctr_template(request):
    """Download Excel template for CCTR upload."""
    file_path = os.path.join(settings.MEDIA_ROOT, "sql/cctr_uploadTemplate.xlsx")
    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename="cctr_uploadTemplate.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ===================================================================
# 🥳 CCTR template upload (temp)
# ===================================================================
@cctr_router.post("/upload-template-temp", response=UploadTempResult)
def upload_cctr_template_temp(request, file: UploadedFile = File(...)):
    """Validate CCTR template and save temp file path."""
    result = validate_and_save_template(file.file, CCTR_COL_MAP, "cctr")
    if not result["is_valid"]:
        raise HttpError(400, result["message"])
    return {
        "success": result["success"],
        "is_valid": result["is_valid"],
        "message": result["message"],
        "temp_file_path": result["temp_file_path"]
    }

# ===================================================================
# 🥳 GATE template download
# ===================================================================
@gate_router.get("/download-template")
def download_gate_template(request):
    """Download Excel template for GATE 3.0 upload."""
    file_path = os.path.join(settings.MEDIA_ROOT, "sql/gate_uploadTemplate.xlsx")
    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename="gate_uploadTemplate.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ===================================================================
# 🥳 GATE template upload (temp)
# ===================================================================
@gate_router.post("/upload-template-temp", response=UploadTempResult)
def upload_gate_template_temp(request, file: UploadedFile = File(...)):
    """Validate GATE template and save temp file path."""
    result = validate_and_save_template(file.file, GATE_COL_MAP, "gate")
    if not result["is_valid"]:
        raise HttpError(400, result["message"])
    return {
        "success": result["success"],
        "is_valid": result["is_valid"],
        "message": result["message"],
        "temp_file_path": result["temp_file_path"]
    }

# ===================================================================
# 🥳 RAKey CRUD
# ===================================================================
@rakey_router.post("/initiate")
def initiate_rakey_endpoint(request):
    try:
        summary = initiate_rakey()
        return {"success": True, "message": "✅ RAKey initialization completed", "summary": summary}
    except Exception as e:
        logger.exception("[RAKey] init failed")
        raise HttpError(500, f"⚠ RAKey initialization failed: {e}")

@rakey_router.get("/all/")
def list_rakey(request):
    """List all RAKey rows."""
    return list(RaKey.objects.all().values())

@rakey_router.get("/detail/{code}")
def get_rakey(request, code: str):
    """Fetch a single RAKey by code."""
    rakey = get_object_or_404(RaKey, code=code)
    return {"code": rakey.code, "description": rakey.description}

@rakey_router.post("/new/")
def create_rakey(request, code: str, description: str):
    """Create a new RAKey."""
    RaKey.objects.create(code=code, description=description)
    return {"success": True, "message": f"RAKey {code} created"}

@rakey_router.put("/update/{code}")
def update_rakey(request, code: str, description: str):
    """Update a RAKey."""
    rakey = get_object_or_404(RaKey, code=code)
    rakey.description = description
    rakey.save()
    return {"success": True, "message": f"RAKey {code} updated"}

@rakey_router.delete("/delete/{code}")
def delete_rakey(request, code: str):
    """Delete a RAKey."""
    rakey = get_object_or_404(RaKey, code=code)
    rakey.delete()
    return {"success": True, "message": f"RAKey {code} deleted"}

# ===================================================================
# 🥳 Run full processing (SAP/CCTR/GATE → raw → processed)
# ===================================================================
@process_router.post("/sap-cctr-gate-rakey/", response=ProcessAllResponse)
def run_all_processes(request, data: FilePathsIn):
    """
    Example request:
    {
        "sap_path": "tmp/sap_xxxxx.xlsx",
        "cctr_path": "tmp/cctr_xxxxx.xlsx",
        "gate_path": "tmp/gate_xxxxx.xlsx"
    }
    """
    account_error._login_error(request)

    # Check RAKey availability
    if not RaKey.objects.exists():
        raise HttpError(400, "❌ No RAKey data found. Please initialize RAKey first.")

    try:
        # Extract batch_no from filenames
        sap_batch = reg_express.extract_batch_no_from_path(data.sap_path)
        cctr_batch = reg_express.extract_batch_no_from_path(data.cctr_path)
        gate_batch = reg_express.extract_batch_no_from_path(data.gate_path)

        # Excel → RAW DB (each wrapped with try/except)
        try:
            logger.info("✅✅ cctr_raw start ✅✅")
            cctr_raw_result = finalize_upload(data.cctr_path, CCTR_COL_MAP, CctrRaw, CctrRaw_In, "cctr", cctr_batch)
            logger.info("✅✅ cctr_raw end ✅✅")
        except Exception as e:
            logger.exception("❌ Error while processing cctr_raw")
            raise HttpError(500, f"❌ Error while processing cctr_raw: {str(e)}")

        try:
            logger.info("✅✅ gate_raw start ✅✅")
            gate_raw_result = finalize_upload(data.gate_path, GATE_COL_MAP, GateRaw, GateRaw_In, "gate", gate_batch)
            logger.info("✅✅ gate_raw end ✅✅")
        except Exception as e:
            logger.exception("❌ Error while processing gate_raw")
            raise HttpError(500, f"❌ Error while processing gate_raw: {str(e)}")

        try:
            logger.info("✅✅ sap_raw start ✅✅")
            sap_raw_result = finalize_upload(data.sap_path,  SAP_COL_MAP,  SapRaw,  SapRaw_In,  "sap",  sap_batch)
            logger.info("✅✅ sap_raw end ✅✅")
        except Exception as e:
            logger.exception("❌ Error while processing sap_raw")
            raise HttpError(500, f"❌ Error while processing sap_raw: {str(e)}")

        logger.info("✅✅ All raw data saved ✅✅")

        # Post-processing (each with batch info if needed)
        try:
            logger.info("✅✅ cctr_processed start ✅✅")
            cctr_processed_result = process_cctr(data.cctr_path)
            logger.info("✅✅ cctr_processed end ✅✅")

            logger.info("✅✅ gate_processed start ✅✅")
            gate_processed_result = process_gate(data.gate_path)
            logger.info("✅✅ gate_processed end ✅✅")

            logger.info("✅✅ sap_processed start ✅✅")
            user_name = request.user.username
            sap_processed_result = process_sap(data.gate_path, data.sap_path, user_name)
            logger.info("✅✅ sap_processed end ✅✅")

            logger.info("✅✅ All processed data saved ✅✅")

        except Exception as e:
            logger.exception("❌ Error during post-processing")
            raise HttpError(500, f"❌ Error during post-processing: {str(e)}")

        return ProcessAllResponse(
            success=True,
            message="✅ Completed all processes sequentially: cctr → gate → sap / raw → processed",
            results={
                "cctr_raw": ProcessResult(**cctr_raw_result),
                "gate_raw": ProcessResult(**gate_raw_result),
                "sap_raw":  ProcessResult(**sap_raw_result),
                "cctr_processed": ProcessResult(**cctr_processed_result),
                "gate_processed": ProcessResult(**gate_processed_result),
                "sap_processed":  ProcessResult(**sap_processed_result),
            },
        )

    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"❌ Unknown error during processing: {str(e)}")

# ===================================================================
# 🥳 Read processed data for current user
# ===================================================================
@process_router.get("/all/me", response=List[SapProcessed_Out])
def find_my_team_sap_processed(request):
    account_error._login_error(request)

    qs = team_filter._process_team(Team, SapProcessed, request, SapProcessed_Out)
    return [SapProcessed_Out.model_validate(obj, from_attributes=True) for obj in qs]

# ===================================================================
# 🥳 Create a manual adjustment (SapProcessed)
# ===================================================================
@process_router.post("/new", response=SapProcessedResponse)
def create_SapProcessed(request, data: SapProcessed_In):
    """
    Create SapProcessed (category='Adjustment'):
      - operation_team := data.operation_team (FK lookup)
      - monthly_data   := always active by flag rules
      - no run_activate_from_last_month_to_end (same flag rule as predictions)
    """
    account_error._login_error(request)

    operation_team_instance = get_object_or_404(Team, team_name=data.operation_team)
    batch_no = datetime.now().strftime("%Y%m%d%H%M%S")
    monthly_data = flag_month._process_active_flag()

    instance = SapProcessed.objects.create(
        batch_no=batch_no,
        **data.dict(exclude={"operation_team", "monthly_data"}),
        operation_team=operation_team_instance,
        monthly_data=monthly_data,
        category="Adjustment",
        owner=request.user,
    )

    return SapProcessedResponse(
        success=True,
        message=f"✅ Created SapProcessed with ID {instance.id} (batch_no={batch_no})",
        id=instance.id,
        data=SapProcessed_Out.model_validate(instance, from_attributes=True),
    )

# ===================================================================
# 🥳 Fetch single SapProcessed
# ===================================================================
@process_router.get("/detail/{id}", response=SapProcessedResponse)
def get_SapProcessed(request, id: int):
    """Fetch a single SapProcessed by ID."""
    instance = get_object_or_404(SapProcessed, id=id)
    return SapProcessedResponse(
        success=True,
        message=f"✅ Fetched SapProcessed with ID {instance.id}",
        id=instance.id,
        data=SapProcessed_Out.model_validate(instance, from_attributes=True)
    )

# ===================================================================
# 🥳 Update SapProcessed
# ===================================================================
@process_router.put("/detail/{id}", response=SapProcessedResponse)
def update_SapProcessed(request, id: int, data: SapProcessed_In):
    """Update SapProcessed fields (including operation_team by name)."""
    account_error._login_error(request)
    instance = get_object_or_404(SapProcessed, id=id)

    for attr, value in data.dict(exclude={"operation_team"}).items():
        setattr(instance, attr, value)

    if data.operation_team:
        instance.operation_team = get_object_or_404(Team, team_name=data.operation_team)

    instance.owner = request.user
    instance.save()

    return SapProcessedResponse(
        success=True,
        message=f"✅ Updated SapProcessed with ID {instance.id}",
        id=instance.id,
        data=SapProcessed_Out.model_validate(instance, from_attributes=True)
    )

# ===================================================================
# 🥳 Update monthly_data for SapProcessed
# ===================================================================
@process_router.put("/detail/{id}/monthly", response=SapProcessedResponse)
def update_sap_processed_monthly_data(request, id: int, data: MonthlyUpdate):
    account_error._login_error(request)
    instance = get_object_or_404(SapProcessed, id=id)

    original = instance.monthly_data or {}
    merged = reg_express._deep_merge_dict(original, data.monthly_data)
    instance.monthly_data = merged
    instance._request_user = request.user
    instance.save()

    return SapProcessedResponse(
        success=True,
        message=f"✅ Updated monthly_data for SapProcessed ID {instance.id}",
        id=instance.id,
        data=SapProcessed_Out.model_validate(instance, from_attributes=True)
    )

# ===================================================================
# 🥳 Delete ALL raw/processed financial data (danger)
# ===================================================================
@process_router.delete("/all/reset/records")
def delete_all_financial_records(request):
    """Danger: delete all Raw/Processed tables and reset identity sequences (PostgreSQL)."""
    account_error._superuser_error(request)

    if not request.user.is_superuser:
        raise HttpError(403, "Only admins can initialize this resource.")

    models_to_reset = [
        SapRaw, SapProcessed,
        CctrRaw, CctrProcessed,
        GateRaw, GateProcessed
    ]

    with connection.cursor() as cursor:
        table_names = [model._meta.db_table for model in models_to_reset]
        table_list = ", ".join([f'"{t}"' for t in table_names])
        cursor.execute(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE;")

    return {
        "success": True,
        "message": "✅ Deleted all data and reset identity sequences (PostgreSQL)."
    }

# ===================================================================
# 🥳 Merge API (filtered lists)
# ===================================================================
@merge_router.get("/all/filter", response=Merge_Out)
def merge_filter_all(
    request,
    year: Optional[int] = None,
    division: Optional[str] = None,
    group: Optional[str] = None,
    team: Optional[str] = None,
):
    """
    Example:
      /all/filter?division=TDD&group=MTG&team=Team1&year=2025
    """
    team_name_combined = None
    if division and group and team:
        team_name_combined = f"PTK-{division}-{group}-{team}".strip()

    tp_qs, sp_qs = team_filter._merge_team(
        Team, TeamPrediction, SapProcessed,
        year, division, group, team, team_name_combined, request
    )

    return {
        "team_predictions": [
            MergeTeamPrediction_Out.model_validate(obj, from_attributes=True) for obj in tp_qs
        ],
        "sap_processed": [
            SapProcessed_Out.model_validate(obj, from_attributes=True) for obj in sp_qs
        ],
    }

# ===================================================================
# 🥳 Merge calculations (cards above)
# ===================================================================
@merge_router.get("/all/filter/calculate")
def calculate_all(
    request,
    year: Optional[int] = None,
    division: Optional[str] = None,
    group: Optional[str] = None,
    team: Optional[str] = None,
):
    """
    Returns three aggregated results at once:
     - this_month: actual vs expected for the current closing month
     - first_half: Jan–Jun mix (actual up to closing month, expected for the rest in H1)
     - full_year : Jan–Dec mix (actual up to closing month, expected after)
    """
    # 1) Latest closing info (within the specified year if provided)
    if not ProcessClose.objects.exists():
        raise HttpError(404, "❌ No closing information available.")
    else:
        latest_closing = ProcessClose.objects.order_by("-timestamp").first()
        year = latest_closing.year
        closed_month = latest_closing.month
        month_key = flag_month._month_key_from_int(closed_month)

    # 2) Get filtered data
    combined = merge_filter_all(request, year, division, group, team)
    process_list = combined["sap_processed"]        # actuals
    pred_list = combined["team_predictions"]        # predictions

    # this_month
    actual_sales = flag_month._get_sum(process_list, [month_key], "sales")
    actual_gross = flag_month._get_sum(process_list, [month_key], "gross_profit")
    expected_sales = flag_month._get_sum(pred_list, [month_key], "sales")
    expected_gross = flag_month._get_sum(pred_list, [month_key], "gross_profit")
    sales_diff, sales_pct = flag_month._fmt_diff(actual_sales, expected_sales)
    gross_diff, gross_pct = flag_month._fmt_diff(actual_gross, expected_gross)

    this_month = {
        "target_year": year,
        "target_month": closed_month,
        "sales": {
            "expected_sales": expected_sales,
            "actual_sales": actual_sales,
            "sales_diff": sales_diff,
            "sales_pct": sales_pct,
        },
        "gross": {
            "expected_gross": expected_gross,
            "actual_gross": actual_gross,
            "gross_diff": gross_diff,
            "gross_pct": gross_pct,
        },
    }

    # first_half (Jan–Jun)
    first_half_keys = MONTH_KEYS[:6]
    if closed_month < 6:
        process_months_h1 = first_half_keys[:closed_month]
        pred_months_h1 = first_half_keys[closed_month:]
        sales_h1 = (
            flag_month._get_sum(process_list, process_months_h1, "sales") +
            flag_month._get_sum(pred_list, pred_months_h1, "sales")
        )
        gross_h1 = (
            flag_month._get_sum(process_list, process_months_h1, "gross_profit") +
            flag_month._get_sum(pred_list, pred_months_h1, "gross_profit")
        )
    else:
        process_months_h1 = first_half_keys[:6]
        pred_months_h1 = []
        sales_h1 = flag_month._get_sum(process_list, first_half_keys, "sales")
        gross_h1 = flag_month._get_sum(process_list, first_half_keys, "gross_profit")

    first_half = {
        "sales": sales_h1,
        "gross": gross_h1,
        "process_months_h1": process_months_h1,
        "pred_months": pred_months_h1
    }

    # full_year
    process_months_fy = MONTH_KEYS[:closed_month]
    pred_months_fy = MONTH_KEYS[closed_month:] if closed_month < 12 else []

    sales_fy = (
        flag_month._get_sum(process_list, process_months_fy, "sales") +
        flag_month._get_sum(pred_list, pred_months_fy, "sales")
    )
    gross_fy = (
        flag_month._get_sum(process_list, process_months_fy, "gross_profit") +
        flag_month._get_sum(pred_list, pred_months_fy, "gross_profit")
    )

    full_year = {
        "sales": sales_fy,
        "gross": gross_fy,
        "process_months": process_months_fy,
        "pred_months": pred_months_fy,
    }

    return {
        "this_month": this_month,
        "first_half": first_half,
        "full_year": full_year,
    }

# ===================================================================
# 🥳 Export merged filtered data to Excel
# ===================================================================
@merge_router.get("/all/filter/export", auth=None)
def export_merge_filter_to_excel(
    request,
    year: Optional[int] = None,
    division: Optional[str] = None,
    group: Optional[str] = None,
    team: Optional[str] = None,
):
    """Export filtered data to Excel (filename: report_export_YYYYMMDD.xlsx)."""
    filtered_data = merge_filter_all(request, year, division, group, team)
    now_str = datetime.now().strftime("%Y%m%d")
    filtering_name = file_maker._make_name(division, group, team)
    filename = f"{year}-report-{filtering_name}_{now_str}.xlsx"
    return file_maker._generate_excel_response(filtered_data, filename=filename)

# ===================================================================
# 🥳 Close flags for predictions (mark as closed from last month to end)
# ===================================================================
@close_router.post("/new-closed")
def close_from_last_month_to_end(request):
    account_error._login_error(request)
    action_name = "closed"
    target_year_active, start_label, rec_year, rec_month, flag_meaning = flag_month._prediction_change_flag(
        TeamPrediction, PredictionClose, request, action_name
    )
    return {
        "success": True,
        "message": f"Completed active handling for {target_year_active} {start_label}–Dec (record: {rec_year}-{rec_month})",
        "flag_meaning": flag_meaning,
    }

# ===================================================================
# 🥳 Activate flags for predictions (mark as active from last month to end)
# ===================================================================
@close_router.post("/new-activated")
def activate_from_last_month_to_end(request):
    account_error._login_error(request)
    action_name = "active"
    target_year_active, start_label, rec_year, rec_month, flag_meaning = flag_month._prediction_change_flag(
        TeamPrediction, PredictionClose, request, action_name
    )
    return {
        "success": True,
        "message": f"Completed active handling for {target_year_active} {start_label}–Dec (record: {rec_year}-{rec_month})",
        "flag_meaning": flag_meaning,
    }

# ===================================================================
# 🥳 Recent closing status
# ===================================================================
@close_router.get("/recent-status")
def get_first_monthly_closing(request):
    account_error._login_error(request)

    closing = PredictionClose.objects.order_by("-id").first()
    if not closing:
        raise HttpError(404, "No PredictionClose data found.")

    return {
        "success": True,
        "message": "Loaded latest PredictionClose record",
        "data": {
            "id": closing.id,
            "year": closing.year,
            "month": closing.month,
            "closed_by": getattr(closing.closed_by, "username", None),
            "timestamp": closing.timestamp,
            "action": getattr(closing, "action", None),
        },
    }

# ===================================================================
# 🥳 Reset PredictionClose/ProcessClose
# ===================================================================
@close_router.delete("/reset/records")
def purge_monthly_closing(request):
    """
    Delete all PredictionClose and ProcessClose rows and reset identity (PostgreSQL).
    """
    account_error._superuser_error(request)

    prediction_table = PredictionClose._meta.db_table
    process_table = ProcessClose._meta.db_table

    before_prediction = PredictionClose.objects.count()
    before_process = ProcessClose.objects.count()

    with connection.cursor() as cursor:
        cursor.execute(f"TRUNCATE TABLE {prediction_table}, {process_table} RESTART IDENTITY CASCADE;")

    return {
        "success": True,
        "message": f"Deleted all rows and reset identity for PredictionClose({before_prediction}) and ProcessClose({before_process}).",
        "deleted_prediction": before_prediction,
        "deleted_process": before_process,
    }

# ===================================================================
# 🥳 DB → Excel export utility
# ===================================================================
@db_router.get("/excel")
def export_model_to_excel(
    request,
    app: str,                      # e.g., "finance"
    model: str,                    # e.g., "SapProcessed"
    fields: Optional[str] = None,  # e.g., "id,team_name,updated_at"
    using: str = "default",        # Django DB alias
    limit: Optional[int] = None,   # e.g., 10000
):
    # 1) Resolve model
    Model = apps.get_model(app_label=app, model_name=model)
    if Model is None:
        raise HttpError(404, f"Model not found: {app}.{model}")

    # 2) Field names to export
    if fields:
        field_names = [f.strip() for f in fields.split(",") if f.strip()]
    else:
        field_names = [
            f.name for f in Model._meta.get_fields()
            if getattr(f, "concrete", False) and not getattr(f, "many_to_many", False) and not getattr(f, "one_to_many", False)
        ]
        if not field_names:
            raise HttpError(400, "No concrete fields to export.")

    # 3) Query data
    qs = Model.objects.using(using).all()
    if limit and limit > 0:
        qs = qs[:limit]
    rows = list(qs.values(*field_names))
    df = pd.DataFrame(rows, columns=field_names)

    # 4) Same sheet and file name
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    sheet_and_file_name = f"{using}_{model}_{ts}"

    # 5) Save to Excel in-memory
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_and_file_name)
    buffer.seek(0)

    # 6) HTTP response
    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{sheet_and_file_name}.xlsx"'
    return resp
