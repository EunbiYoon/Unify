import pandas as pd
from django.core.files.storage import default_storage
from django.db import transaction
import os
import sys
import django

# ✅ 1) Django 초기화
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# 3) 이제 import
from finance.utils.process_dbid import reset_pk_sequence_safely

def finalize_upload(file_path: str, col_map: dict, model, schema_in, prefix: str, batch_no: int):
    """
    - 같은 batch_no 기존 데이터 선삭제
    - PK 시퀀스 리셋 (테이블 비었을 때만 1부터 시작하도록 안전 처리)
    - 신규 데이터 일괄 저장
    """
    try:
        # 1) 파일 읽기 + 컬럼 매핑
        with default_storage.open(file_path, "rb") as f:
            df = pd.read_excel(f)
        df = df.rename(columns=col_map)

        # 2) 트랜잭션
        # 2-1) 같은 배치 선삭제
        deleted, _ = model.objects.filter(batch_no=batch_no).delete()

        # 2-2) (선택) 테이블이 비었다면 PK 시퀀스 리셋
        #  - 테이블 전체 비었을 때만 리셋하고,
        #  - 일부만 지워진 상태면 리셋하지 않음(무결성 보호)
        if model.objects.count() == 0:
            reset_pk_sequence_safely(model, alias="default")

        # 2-3) 행 변환 + 적재
        objects = []
        fields = schema_in.model_fields.keys()
        for _, row in df.iterrows():
            row_data = {
                field: (str(row.get(field)) if pd.notna(row.get(field)) else None)
                for field in fields
            }
            data = schema_in(**row_data)
            obj = model(**data.dict())
            obj.batch_no = batch_no
            objects.append(obj)

        model.objects.bulk_create(objects)

        return {
            "success": True,
            "message": f"🧹 기존 {deleted}건 삭제 후, ✅ 총 {len(objects)}건 업로드 완료 (Batch #{batch_no})",
            "rows_saved": len(objects),
            "rows_deleted": deleted,
            "batch_no": batch_no,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 업로드 실패: {e}",
        }
