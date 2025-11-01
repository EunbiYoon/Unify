# 표준 라이브러리
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

# Django 기본
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


# 내부 모듈 (view_XX, utils, models, schemas)
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
import calendar


# ✅ Router 선언
home_router = Router(tags=["Home Page"])
pred_router = Router(tags=["[Project Page] Team Prediction Initialize + CRUD"])
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

# 로거
import logging
logger = logging.getLogger(__name__)

# month
MONTH_KEYS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
MONTH_KOR = {
    "jan": "1월", "feb": "2월", "mar": "3월", "apr": "4월", "may": "5월", "jun": "6월",
    "jul": "7월", "aug": "8월", "sep": "9월", "oct": "10월", "nov": "11월", "dec": "12월"
}

@home_router.get("")
def finance_home(request):
    return render(request, 'finance_home.html')

# ===================================================================
# 🥳 예상 샘플 업로드
# ===================================================================
@pred_router.post("/upload-sample")
def upload_TeamPrediction_data(request, file: UploadedFile = File(...)):
    """📌 (DEV Only - DB Migration) TeamPrediction 엑셀 업로드 후 삽입, 초기 DB 셋팅, 테스트 파일 : sample/pred_july_sample.xlsx"""
    account_error._superuser_error(request)

    result = initiate_pred.process_uploaded_pred_file(file)
    return JsonResponse(result)

# ===================================================================
# 🥳 예상 데이터 보기
# ===================================================================
@pred_router.get("/all/me", response=List[TeamPrediction_Out])
def find_my_team_predictions(request):
    """📌 예상 데이터 보기 """
    account_error._login_error(request)

    # 1) flag 최신으로 업데이트
    close_refresh._pred_close(TeamPrediction)

    # 2) FK id로 필터 (operation_team/shared_team 둘 다)
    rule_q = team_filter._pred_team(Team, TeamPrediction, request)
    qs = (
            TeamPrediction.objects
            .select_related("operation_team", "shared_team")  # BooleanField는 select_related 대상 아님
            .filter(rule_q)
            .distinct()
            .order_by("operation_team","-created_at")
        )
    logger.info("🔵 필터된 결과 수: %s", qs.count())
    return [TeamPrediction_Out.model_validate(obj, from_attributes=True) for obj in qs]

# ===================================================================
# 🥳 예상 데이터 생성
# ===================================================================
@pred_router.post("/new", response=TeamPredictionResponse)
def create_TeamPrediction(request, data: TeamPrediction_In):
    """📌 예상 데이터 생성하기 """
    account_error._login_error(request)

    # 1) 운영팀이나 협업팀에 대한 에러 처리
    shared_dominate = None
    operation_team_instance, shared_team_instance = team_error._pred_team(data, Team, shared_dominate)

    # 2) monthly_data 생성하기 -> original_instance & shared_instance 저장
    origin_monthly_data = month_create._create_origin_monthly_data(request)
    origin_instance = save_instance._pred_origin(request, data, TeamPrediction, operation_team_instance, shared_team_instance, origin_monthly_data, None)
    if shared_team_instance:
        shared_monthly_data = month_create._create_shared_monthly_data(request)
        print(shared_monthly_data)
        shared_instance = save_instance._pred_shared(request, data, TeamPrediction, operation_team_instance, shared_team_instance, shared_monthly_data, origin_instance)

    # 3) 성공 메세지
    return TeamPredictionResponse(
        success=True,
        message=f"✅ Created TeamPrediction with ID {origin_instance.id}",
        id=origin_instance.id,
        data=TeamPrediction_Out.model_validate(origin_instance, from_attributes=True),
    )

# ===================================================================
# 🥳 예상 데이터 수정하기 위해 정보 가져오기
# ===================================================================
@pred_router.get("/detail/{id}", response=TeamPredictionResponse)
def get_TeamPrediction(request, id: int):
    """📌 TeamPrediction 단일 조회"""
    instance = get_object_or_404(TeamPrediction, id=id)
    return TeamPredictionResponse(
        success=True,
        message=f"✅ Fetched TeamPrediction with ID {instance.id}",
        id=instance.id,
        data=TeamPrediction_Out.model_validate(instance, from_attributes=True)
    )

# ===================================================================
# 🥳 예상 데이터 수정
# ===================================================================
@pred_router.put("/detail/{id}", response=TeamPredictionResponse)
def update_TeamPrediction(request, id: int, data: TeamPrediction_In):
    """
    📌 Update TeamPrediction (종속자 처리 과정)
    """
    account_error._login_error(request)

    # 1) 운영팀이나 협업팀에 대한 에러 처리
    sort_shared_dominate = TeamPrediction.objects.get(id=id).shared_dominate
    operation_team_instance, shared_team_instance = team_error._pred_team(data, Team, sort_shared_dominate)
            
    # 2) origin : monthly_data 생성하기 -> original_instance 저장
    origin_instance = save_instance._pred_origin(request, data, TeamPrediction, operation_team_instance, shared_team_instance, None, id)

    # 3) sharing프로젝트가 아닌데 shared_instance가 존재하면 없애 버리기
    if data.project_category != "Sharing":
        # 혹시나 dominate한게 존재하면 지우기
        qs = TeamPrediction.objects.filter(dominant=origin_instance,shared_dominate=False)
        if qs.exists():
            # ✅ 조건에 맞는 인스턴스 전부 삭제
            logger.info(f"실적분배 아닌 프로젝트로 변환되어 삭제된 TeamPrediction: qs : {qs}")
            deleted_count, _ = qs.delete()
            logger.info(f"실적분배 아닌 프로젝트로 변환되어 삭제된 TeamPrediction 개수: {deleted_count}")

    # 4) shared : monthly_data 생성하기 -> original_instance 저장
    if shared_team_instance:
        origin_monthly_data = origin_instance.monthly_data
        shared_monthly_data = month_update._update_shared_monthly_data(origin_monthly_data)
        shared_instance = save_instance._pred_shared(request, data, TeamPrediction, operation_team_instance, shared_team_instance, shared_monthly_data, origin_instance)

    return TeamPredictionResponse(
        success=True,
        message=f"✅ Updated TeamPrediction with ID {origin_instance.id}",
        id=origin_instance.id,
        data=TeamPrediction_Out.model_validate(origin_instance, from_attributes=True)
    )

# ===================================================================
# 🥳 Monthly_data 개별적으로 수정할 떄 / 프론트 엔드 엑셀 수정 기능 연동
# ===================================================================
@pred_router.put("/detail/monthly/{id}", response=TeamPredictionResponse)
def update_team_prediction_monthly_data(request, id: int, data: MonthlyUpdate):
    account_error._login_error(request)
    instance = get_object_or_404(TeamPrediction, id=id)

    # 1) 원본 인스턴스: 델타 그대로 반영
    base_before = instance.monthly_data or {}
    base_after  = reg_express._deep_merge_dict(base_before, data.monthly_data)  # ← sep.sales=1000, sep.gross_profit=1000 등
    instance.monthly_data = base_after
    instance._request_user = request.user
    instance.save()
    logger.info("✅ [shared_dominate=True] base updated : %s", instance.id)

    # 2) 공유 인스턴스: 존재할 때만(update-only) 정수만 -1 곱한 델타 반영
    if instance.shared_team:
        # 종속된 프로젝트 찾기
        shared_obj = get_object_or_404(TeamPrediction, shared_dominate=False, dominant=instance)
        logger.info(f"✅ [shared_dominate=False] shared_obj:{shared_obj}")

        if shared_obj:
            # 데이터 음수 처리하기
            month_update_detail._month_negately_data(data, shared_obj)
            shared_obj._request_user = request.user
            shared_obj.save()
            logger.info("🔁 shared updated: %s", shared_obj.id)
        else:
            logger.info("⚪ shared not found → skip (no create)")

    return TeamPredictionResponse(
        success=True,
        message=f"✅ Updated monthly_data for TeamPrediction ID {instance.id}",
        id=instance.id,
        data=TeamPrediction_Out.model_validate(instance, from_attributes=True),
    )

# ===================================================================
# 🥳 create할때 보여지는 것들
# ===================================================================
@pred_router.get("/pop-up")
def get_division_group_team_tree_api(request):
    """📌 전체 Division → Group → Team + 선택 목록 반환 (RAKey의 description 포함)"""
    results = []

    # ✅ Division → Group → Team
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

    # ✅ status_choice / category_choice
    status_choices = [choice[0] for choice in TeamPrediction._meta.get_field("status").choices]
    category_choices = [choice[0] for choice in TeamPrediction._meta.get_field("project_category").choices]

    # ✅ rakey descriptions만 추출
    rakey_list = list(RaKey.objects.values_list("description", flat=True))

    return {
        "organization": results,
        "status_choices": status_choices,
        "category_choices": category_choices,
        "rakey_list": rakey_list
    }

# ===================================================================
# 🥳 prediction 데이터 전부 리셋
# ===================================================================
@pred_router.delete("/reset/records")
def delete_all_team_predictions(request):
    """⚠️ 모든 TeamPrediction 삭제 + DB ID 리셋"""
    account_error._superuser_error(request)

    if not request.user.is_superuser:
        raise HttpError(403, "관리자만 초기화할 수 있습니다.")

    # ✅ 삭제
    TeamPrediction.objects.all().delete()

    # ✅ 테이블명 확인 후 시퀀스 삭제
    table_name = TeamPrediction._meta.db_table
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")

    return {"success": True, "message": f"✅ {table_name} 데이터 삭제 및 ID 리셋 완료"}






# ===================================================================
# 🥳 sap - template 다운로드
# ===================================================================
@sap_router.get("/download-template")
def download_sap_template(request):
    """📌 SAP 업로드용 템플릿 다운로드"""
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
# 🥳 sap - template 업로드
# ===================================================================
@sap_router.post("/upload-template-temp", response=UploadTempResult)
def upload_sap_template_temp(request, file: UploadedFile = File(...)):
    """📌 SAP 업로드 -> 파일 저장 위치 기록해야함"""
    result = validate_and_save_template(file.file, SAP_COL_MAP, "sap")
    if not result["is_valid"]:
        raise HttpError(400, result["message"])  # ❌ 실패 시 400 에러 반환
    return {
        "success": result["success"],
        "is_valid": result["is_valid"],
        "message": result["message"],
        "temp_file_path": result["temp_file_path"]
    }

# ===================================================================
# 🥳 cctr - template 다운로드
# ===================================================================
@cctr_router.get("/download-template")
def download_cctr_template(request):
    """📌 CCTR 업로드용 템플릿 다운로드"""
    file_path = os.path.join(settings.MEDIA_ROOT, "sql/cctr_uploadTemplate.xlsx")  # "spl" → "sql" 로 경로 확인 필요

    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename="cctr_uploadTemplate.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ===================================================================
# 🥳 cctr - template 업로드
# ===================================================================
@cctr_router.post("/upload-template-temp", response=UploadTempResult)
def upload_cctr_template_temp(request, file: UploadedFile = File(...)):
    """📌 CCTR 업로드 -> 파일 저장 위치 기록해야함"""

    result = validate_and_save_template(file.file, CCTR_COL_MAP, "cctr")

    if not result["is_valid"]:
        raise HttpError(400, result["message"])  # ❌ 실패 시 400 에러 반환

    return {
        "success": result["success"],
        "is_valid": result["is_valid"],
        "message": result["message"],
        "temp_file_path": result["temp_file_path"]
    }

# ===================================================================
# 🥳 gate - template 다운로드
# ===================================================================
@gate_router.get("/download-template")
def download_gate_template(request):
    """📌 Gate 3.0 업로드용 템플릿 다운로드"""
    file_path = os.path.join(settings.MEDIA_ROOT, "sql/gate_uploadTemplate.xlsx")  # "spl" -> "sql" 확인

    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename="gate_uploadTemplate.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ===================================================================
# 🥳 gate - template 업로드
# ===================================================================ㄴ
@gate_router.post("/upload-template-temp", response=UploadTempResult)
def upload_gate_template_temp(request, file: UploadedFile = File(...)):
    """📌 GATE 업로드 -> 파일 저장 위치 기록해야함"""
    result = validate_and_save_template(file.file, GATE_COL_MAP, "gate")
    if not result["is_valid"]:
        raise HttpError(400, result["message"])  # ❌ 실패 시 400 에러 반환
    return {
        "success": result["success"],
        "is_valid": result["is_valid"],
        "message": result["message"],
        "temp_file_path": result["temp_file_path"]
    }

# ===================================================================
# 🥳 rakey CRUD
# ===================================================================
@rakey_router.post("/initiate")
def initiate_rakey_endpoint(request):
    try:
        summary = initiate_rakey()  # 서브프로세스 없이 같은 프로세스에서 실행
        return {"success": True, "message": "✅ RAKey 초기화 완료", "summary": summary}
    except Exception as e:
        logger.exception("[RAKey] init 실패")
        raise HttpError(500, f"⚠ RAKey 초기화 실패: {e}")

@rakey_router.get("/all/")
def list_rakey(request):
    """📌 RAKey 전체 목록 조회"""
    return list(RaKey.objects.all().values())

@rakey_router.get("/detail/{code}")
def get_rakey(request, code: str):
    """📌 RAKey 단일 조회 / Rakey의 crud는 code로 했음 -> team prediction 과 동일하게 id로도 Crud 가능함"""
    rakey = get_object_or_404(RaKey, code=code)
    return {"code": rakey.code, "description": rakey.description}

@rakey_router.post("/new/")
def create_rakey(request, code: str, description: str):
    """📌 RAKey 새 항목 생성 / Rakey의 crud는 code로 했음 -> team prediction 과 동일하게 id로도 Crud 가능함"""
    RaKey.objects.create(code=code, description=description)
    return {"success": True, "message": f"RAKey {code} created"}

@rakey_router.put("/update/{code}")
def update_rakey(request, code: str, description: str):
    """📌 RAKey 수정 / Rakey의 crud는 code로 했음 -> team prediction 과 동일하게 id로도 Crud 가능함"""
    rakey = get_object_or_404(RaKey, code=code)
    rakey.description = description
    rakey.save()
    return {"success": True, "message": f"RAKey {code} updated"}

@rakey_router.delete("/delete/{code}")
def delete_rakey(request, code: str):
    """📌 RAKey 삭제 / Rakey의 crud는 code로 했음 -> team prediction 과 동일하게 id로도 Crud 가능함"""
    rakey = get_object_or_404(RaKey, code=code)
    rakey.delete()
    return {"success": True, "message": f"RAKey {code} deleted"}





# ===================================================================
# 🥳 process_rakey
# ===================================================================
@process_router.post("/sap-cctr-gate-rakey/", response=ProcessAllResponse)
def run_all_processes(request, data: FilePathsIn):
    """
    requets 예시 : {
        "sap_path": "tmp/sap_xxxxx.xlsx",
        "cctr_path": "tmp/cctr_xxxxx.xlsx",
        "gate_path": "tmp/gate_xxxxx.xlsx"
    }  # 파일이름은 tmp/{디비이름}_날짜.xlsx
    """
    account_error._login_error(request)

    # ✅ RaKey 데이터 여부 확인
    if not RaKey.objects.exists():
        raise HttpError(400, "❌ RaKey 데이터가 없습니다. 먼저 RaKey를 업로드하세요.")

    try:
        # ✅ 파일명에서 batch_no 추출
        sap_batch = reg_express.extract_batch_no_from_path(data.sap_path)
        cctr_batch = reg_express.extract_batch_no_from_path(data.cctr_path)
        gate_batch = reg_express.extract_batch_no_from_path(data.gate_path)

        # ✅ 엑셀 → RAW DB 저장 단계별 try-except
        try:
            logger.info("✅✅ cctr_raw start ✅✅")
            cctr_raw_result = finalize_upload(data.cctr_path, CCTR_COL_MAP, CctrRaw, CctrRaw_In, "cctr", cctr_batch)
            logger.info("✅✅ cctr_raw end ✅✅")
        except Exception as e:
            logger.exception("❌ cctr_raw 처리 중 오류 발생")
            raise HttpError(500, f"❌ cctr_raw 처리 중 오류 발생: {str(e)}")

        try:
            logger.info("✅✅ gate_raw start ✅✅")
            gate_raw_result = finalize_upload(data.gate_path, GATE_COL_MAP, GateRaw, GateRaw_In, "gate", gate_batch)
            logger.info("✅✅ gate_raw end ✅✅")
        except Exception as e:
            logger.exception("❌ gate_raw 처리 중 오류 발생")
            raise HttpError(500, f"❌ gate_raw 처리 중 오류 발생: {str(e)}")

        try:
            logger.info("✅✅ sap_raw start ✅✅")
            sap_raw_result = finalize_upload(data.sap_path,  SAP_COL_MAP,  SapRaw,  SapRaw_In,  "sap",  sap_batch)
            logger.info("✅✅ sap_raw end ✅✅")
        except Exception as e:
            logger.exception("❌ sap_raw 처리 중 오류 발생")
            raise HttpError(500, f"❌ sap_raw 처리 중 오류 발생: {str(e)}")

        logger.info("✅✅ all raw data is saved!!!  ✅✅")

        # ✅ 후처리 스크립트 실행 (각각 batch_no 전달)
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

            logger.info("✅✅ all processed data is saved!!!  ✅✅")

        except Exception as e:
            logger.exception("❌ 후처리 중 오류 발생")
            raise HttpError(500, f"❌ 후처리 중 오류 발생: {str(e)}")

        # ✅ 응답
        return ProcessAllResponse(
            success=True,
            message="✅ 모든 프로세스가 순차적으로 완료되었습니다 : cctr -> gate -> sap / raw -> processed",
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
        # 이미 HttpError로 던진 건 그대로 전달
        raise
    except Exception as e:
        # 여기서는 더 이상 어느 단계인지 알 수 없으므로 전체 에러로 처리
        raise HttpError(500, f"❌ 처리 중 알 수 없는 오류 발생: {str(e)}")





# ===================================================================
# 🥳 process 전체 데이터 
# ===================================================================
@process_router.get("/all/me", response=List[SapProcessed_Out])
def find_my_team_sap_processed(request):
    account_error._login_error(request)

    # ✅ 사용자 권한에 따른 대상 팀 필터링
    qs = team_filter._process_team(Team, SapProcessed, request, SapProcessed_Out)
    
    # ✅ finance-admin or site-admin 은 원본 그대로
    return [SapProcessed_Out.model_validate(obj, from_attributes=True) for obj in qs]


# ===================================================================
# 🥳 process 조정 데이터
# ===================================================================
@process_router.post("/new", response=SapProcessedResponse)
def create_SapProcessed(request, data: SapProcessed_In):
    """
    Create SapProcessed (category='조정'):
      - operation_team := data.operation_team (FK 조회)
      - monthly_data   := 항상 active
      - run_activate_from_last_month_to_end 호출 안 함 (pred와 동일 플래그 규칙)
    """
    account_error._login_error(request)

    # ✅ FK 조회로 operation_team 지정
    operation_team_instance = get_object_or_404(Team, team_name=data.operation_team)

    # 배치번호
    batch_no = datetime.now().strftime("%Y%m%d%H%M%S")

    # 규칙 기반 monthly_data
    monthly_data = flag_month._process_active_flag()

    instance = SapProcessed.objects.create(
        batch_no=batch_no,
        **data.dict(exclude={"operation_team", "monthly_data"}),
        operation_team=operation_team_instance,
        monthly_data=monthly_data,
        category="조정",
        owner=request.user,
    )

    return SapProcessedResponse(
        success=True,
        message=f"✅ Created SapProcessed with ID {instance.id} (batch_no={batch_no})",
        id=instance.id,
        data=SapProcessed_Out.model_validate(instance, from_attributes=True),
    )

# ===================================================================
# 🥳 단순 조회 -> 수정하기 위해
# ===================================================================
@process_router.get("/detail/{id}", response=SapProcessedResponse)
def get_SapProcessed(request, id: int):
    """📌 SapProcessed 단일 조회"""
    instance = get_object_or_404(SapProcessed, id=id)
    return SapProcessedResponse(
        success=True,
        message=f"✅ Fetched SapProcessed with ID {instance.id}",
        id=instance.id,
        data=SapProcessed_Out.model_validate(instance, from_attributes=True)
    )

# ===================================================================
# 🥳 sap 데이터 업데이트
# ===================================================================
@process_router.put("/detail/{id}", response=SapProcessedResponse)
def update_SapProcessed(request, id: int, data: SapProcessed_In):
    """📌 SapProcessed 업데이트"""
    account_error._login_error(request)
    instance = get_object_or_404(SapProcessed, id=id)

    # ✅ 일반 필드 설정 (operation_team 제외)
    for attr, value in data.dict(exclude={"operation_team"}).items():
        setattr(instance, attr, value)

    # ✅ 문자열로 전달된 team 이름으로 Team 조회
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
# 🥳 sap 데이터 엑셀 형식으로 하나하나 업데이트
# ===================================================================
@process_router.put("/detail/monthly/{id}", response=SapProcessedResponse)
def update_sap_processed_monthly_data(request, id: int, data: MonthlyUpdate):
    account_error._login_error(request)
    instance = get_object_or_404(SapProcessed, id=id)

    original = instance.monthly_data or {}
    merged = reg_express._deep_merge_dict(original, data.monthly_data)  # 병합
    instance.monthly_data = merged
    instance._request_user = request.user
    instance.save()

    return SapProcessedResponse(
        success=True,
        message=f"✅ Updated monthly_data for TeamPrediction ID {instance.id}",
        id=instance.id,
        data=SapProcessed_Out.model_validate(instance, from_attributes=True)
    )

# ===================================================================
# 🥳 process 전체 데이터 삭제
# ===================================================================
@process_router.delete("/all/reset/records")
def delete_all_financial_records(request):
    """⚠️ 모든 Raw/Processed 실적 데이터 삭제 + ID 시퀀스 초기화 (PostgreSQL 기준)"""
    account_error._superuser_error(request)
    
    if not request.user.is_superuser:
        raise HttpError(403, "관리자만 초기화할 수 있습니다.")

    # ✅ 리셋 대상 모델 리스트
    models_to_reset = [
        SapRaw, SapProcessed,
        CctrRaw, CctrProcessed,
        GateRaw, GateProcessed
    ]

    with connection.cursor() as cursor:
        table_names = [model._meta.db_table for model in models_to_reset]
        table_list = ", ".join([f'"{t}"' for t in table_names])  # double-quote 안전
        cursor.execute(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE;")

    return {
        "success": True,
        "message": "✅ 모든 데이터 삭제 및 ID 시퀀스 초기화 완료 (PostgreSQL)"
    }




# ===================================================================
# 🥳 merge 전체 데이터
# ===================================================================
@merge_router.get("/all/filter", response=Merge_Out)
def merge_filter_all(
    request,
    year: Optional[int] = None,
    division: Optional[str] = None,
    group: Optional[str] = None,
    team: Optional[str] = None,
):
    """📌 GET /all/filter?division=TDD&group=MTG&team=Team1&year=2025 이렇게 입력 받음"""
    # /all/filter?division=TDD&group=MTG&team=Team1&year=2025 ===> team 이름을 생성 
    team_name_combined = None
    if division and group and team:
        team_name_combined = f"PTK-{division}-{group}-{team}".strip()

    tp_qs, sp_qs = team_filter._merge_team(Team, TeamPrediction, SapProcessed, year, division, group, team, team_name_combined, request)

    return {
        "team_predictions": [
            MergeTeamPrediction_Out.model_validate(obj, from_attributes=True) for obj in tp_qs
        ],
        "sap_processed": [
            SapProcessed_Out.model_validate(obj, from_attributes=True) for obj in sp_qs
        ],
    }


# ===================================================================
# 🥳 merge 카드 위에 계산부분
# ===================================================================
@merge_router.get("/all/filter/calculate")
def calculate_all(
    request,
    year: Optional[int] = None,        # ✅ /all/filter와 동일하게 year도 필터에 포함
    division: Optional[str] = None,
    group: Optional[str] = None,
    team: Optional[str] = None,
):
    """
    세 가지 결과를 한 번에 반환:
     - this_month: 최근 마감 월 기준 예상 vs 실적
     - first_half: 상반기(1~6월) = 마감까지 실적 + 이후 예상
     - full_year : 연간(1~12월) = 마감까지 실적 + 이후 예상
    """

    # 1) 최근 마감 정보 (year 지정 시 그 연도 내에서 최신 마감월 사용)
    if not ProcessClose.objects.exists():
        raise HttpError(404, "❌ 마감 정보가 전혀 없습니다.")
    else:
        latest_closing = ProcessClose.objects.order_by("-timestamp").first()
        year = latest_closing.year  # 필터에도 쓰이도록 기본 연도 확정  
        closed_month = latest_closing.month
        month_key = flag_month._month_key_from_int(closed_month)

    # 2) 필터 데이터 조회 (연도 = 위에서 결정된 year)
    combined = merge_filter_all(request, year, division, group, team)
    process_list = combined["sap_processed"]       # category="결산" --> 과거 데이터
    pred_list = combined["team_predictions"]  # category="예상" ---> 미래 데이터

    # ─ this_month
    actual_sales = flag_month._get_sum(process_list, [month_key], "sales")
    actual_gross = flag_month._get_sum(process_list, [month_key], "gross_profit")
    expected_sales = flag_month._get_sum(pred_list, [month_key], "sales")
    expected_gross = flag_month._get_sum(pred_list, [month_key], "gross_profit")
    sales_diff, sales_pct = flag_month._fmt_diff(actual_sales, expected_sales)
    gross_diff, gross_pct = flag_month._fmt_diff(actual_gross, expected_gross)

    this_month = {
        "target_year":year,
        "target_month":closed_month,
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

    # ─ first_half
    first_half_keys = MONTH_KEYS[:6]
    # 6월 이전!
    if closed_month <6:
        # 실적: 1월~closed_month
        process_months_h1 = first_half_keys[:closed_month]
        # 예상: closed_month 이후 ~ 6월까지
        pred_months_h1 = first_half_keys[closed_month:]
        sales_h1 = (
            flag_month._get_sum(process_list, process_months_h1, "sales") +
            flag_month._get_sum(pred_list, pred_months_h1, "sales")
        )
        gross_h1 = (
            flag_month._get_sum(process_list, process_months_h1, "gross_profit") +
            flag_month._get_sum(pred_list, pred_months_h1,"gross_profit")
        )
    else:
        # 실적: 1월~closed_month
        process_months_h1 = first_half_keys[:6]
        # 예상: closed_month 이후 ~ 6월까지
        pred_months_h1 = []
        sales_h1 = (
            flag_month._get_sum(process_list, first_half_keys, "sales")
        )
        gross_h1 = (
            flag_month._get_sum(process_list, first_half_keys, "gross_profit")
        )

    first_half = {
        "sales": sales_h1,
        "gross": gross_h1,
        "process_months_h1":process_months_h1,
        "pred_months": pred_months_h1
    }

    # ─ full_year
    process_months_fy = MONTH_KEYS[:closed_month]
    pred_months_fy = MONTH_KEYS[closed_month:] if closed_month < 12 else []

    sales_fy = (
        flag_month._get_sum(process_list, process_months_fy, "sales") +
        flag_month._get_sum(process_list, pred_months_fy, "sales")
    )
    gross_fy = (
        flag_month._get_sum(process_list, process_months_fy, "gross_profit") +
        flag_month._get_sum(process_list, pred_months_fy, "gross_profit")
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
# 🥳 merge 엑셀 추출 
# ===================================================================
@merge_router.get("/all/filter/export", auth=None)
def export_merge_filter_to_excel(
    request,
    year: Optional[int] = None,  # ✅ 연도 필터 추가
    division: Optional[str] = None,
    group: Optional[str] = None,
    team: Optional[str] = None,
):
    """📌 필터링된 데이터를 Excel로 export (파일명: report_export_YYYYMMDD_HHMMSS.xlsx)"""

    # ✅ 기존 필터 함수 재사용
    filtered_data = merge_filter_all(request, year, division, group, team)

    # ✅ 파일명에 타임스탬프 포함
    now_str = datetime.now().strftime("%Y%m%d")
    filtering_name = file_maker._make_name(division, group, team)
    filename = f"{year}-report-{filtering_name}_{now_str}.xlsx"

    return file_maker._generate_excel_response(filtered_data, filename=filename)





# ===================================================================
# 🥳 close - PredictionClose 입력 마감
# ===================================================================
@close_router.post("/new-closed")
def close_from_last_month_to_end(request):
    account_error._login_error(request)
    action_name = "closed"
    target_year_active, start_label, rec_year, rec_month, flag_meaning = flag_month._prediction_change_flag(TeamPrediction, PredictionClose, request, action_name)
    
    return {
        "success": True,
        "message": f"{target_year_active}년 {start_label}~12월 active 처리 완료 (기록: {rec_year}-{rec_month})",
        "flag_meaning": flag_meaning,
    }

# ===================================================================
# 🥳 close - PredictionClose 입력 생성
# ===================================================================
@close_router.post("/new-activated")
def activate_from_last_month_to_end(request):
    account_error._login_error(request)
    action_name = "active"
    target_year_active, start_label, rec_year, rec_month, flag_meaning = flag_month._prediction_change_flag(TeamPrediction, PredictionClose, request, action_name)
    
    return {
        "success": True,
        "message": f"{target_year_active}년 {start_label}~12월 active 처리 완료 (기록: {rec_year}-{rec_month})",
        "flag_meaning": flag_meaning,
    }

# ===================================================================
# 🥳 close - 현재 상태
# ===================================================================
@close_router.get("/recent-status")
def get_first_monthly_closing(request):
    account_error._login_error(request)

    closing = PredictionClose.objects.order_by("-id").first()  # 최신 insert 기준
    if not closing:
        raise HttpError(404, "PredictionClose 데이터가 없습니다.")

    return {
        "success": True,
        "message": "PredictionClose 최신 마감 불러오기 완료",
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
# 🥳 close - 데이터 리셋
# ===================================================================
@close_router.delete("/reset/records")
def purge_monthly_closing(request):
    """
    PredictionClose + ProcessClose 테이블 전체 삭제 + PK(id) 시퀀스 리셋 (PostgreSQL 기준)
    """
    account_error._superuser_error(request)

    # 테이블 이름
    prediction_table = PredictionClose._meta.db_table
    process_table = ProcessClose._meta.db_table

    before_prediction = PredictionClose.objects.count()
    before_process = ProcessClose.objects.count()

    # ✅ PK 시퀀스 리셋 (PostgreSQL)
    with connection.cursor() as cursor:
        cursor.execute(f"TRUNCATE TABLE {prediction_table}, {process_table} RESTART IDENTITY CASCADE;")

    return {
        "success": True,
        "message": f"PredictionClose({before_prediction}) + ProcessClose({before_process}) 전체 삭제 및 ID 리셋 완료",
        "deleted_prediction": before_prediction,
        "deleted_process": before_process,
    }

# ===================================================================
# 🥳 DB -> excel
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
    # 1) 모델 찾기
    Model = apps.get_model(app_label=app, model_name=model)
    if Model is None:
        raise HttpError(404, f"Model not found: {app}.{model}")

    # 2) 필드 목록 결정
    if fields:
        field_names = [f.strip() for f in fields.split(",") if f.strip()]
    else:
        field_names = [
            f.name for f in Model._meta.get_fields()
            if getattr(f, "concrete", False) and not getattr(f, "many_to_many", False) and not getattr(f, "one_to_many", False)
        ]
        if not field_names:
            raise HttpError(400, "No concrete fields to export.")

    # 3) 데이터 조회
    qs = Model.objects.using(using).all()
    if limit and limit > 0:
        qs = qs[:limit]
    rows = list(qs.values(*field_names))
    df = pd.DataFrame(rows, columns=field_names)

    # 4) 파일명·시트명 동일하게 설정
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    sheet_and_file_name = f"{using}_{model}_{ts}"  # 원하는 형태로 변경 가능

    # 5) 엑셀 저장
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_and_file_name)
    buffer.seek(0)

    # 6) 응답 반환
    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{sheet_and_file_name}.xlsx"'
    return resp