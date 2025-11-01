import os
import pandas as pd
from django.core.files.storage import default_storage
from django.utils.timezone import now

def validate_and_save_template(file, col_map: dict, prefix: str):
    """📌 엑셀 유효성 검사 및 임시 저장. 실패 시 임시파일 삭제."""
    # ✅ 파일명 생성
    timestamp = now().strftime("%Y%m%d%H%M%S")
    filename = f"{prefix}_{timestamp}.xlsx"
    temp_path = os.path.join("tmp", filename)
    saved_path = default_storage.save(temp_path, file)

    def fail(message: str) -> dict:
        """❌ 실패 시 파일 삭제하고 메시지 반환"""
        if default_storage.exists(saved_path):
            default_storage.delete(saved_path)
        return {
            "success": False,
            "is_valid": False,
            "message": message,
            "temp_file_path": None
        }

    try:
        df = pd.read_excel(default_storage.open(saved_path))

        # ✅ 누락된 컬럼 검사
        missing_cols = [col for col in col_map.keys() if col not in df.columns]
        if missing_cols:
            return fail(f"❌ 템플릿의 형태와 맞지 않습니다. 누락된 컬럼: {missing_cols}")

        # ✅ 빈 데이터 검사
        if df.empty:
            return fail("❌ 데이터가 비어 있습니다.")

    except Exception as e:
        return fail(f"❌ 엑셀 파싱 오류: {str(e)}")

    # ✅ 성공 반환
    return {
        "success": True,
        "is_valid": True,
        "message": "✅ 유효한 템플릿입니다.",
        "temp_file_path": saved_path
    }
