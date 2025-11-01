from pydantic import BaseModel
import os

# ===================================================================
# ✅ 
# ===================================================================
def _deep_merge_dict(original: dict, updates: dict) -> dict:
    for key, value in updates.items():
        if isinstance(value, BaseModel):
            value = value.dict(exclude_unset=True)  # ✅ 부분 필드만 추출
        if isinstance(value, dict) and isinstance(original.get(key), dict):
            original[key] = _deep_merge_dict(original.get(key, {}), value)
        else:
            original[key] = value
    return original

# ===================================================================
# ✅ popup 에 사용
# ===================================================================
def _strip_prefix(full_name: str, prefix: str) -> str:
    """접두어(prefix) 제거 함수"""
    if full_name.startswith(prefix + "-"):
        return full_name[len(prefix) + 1 :]
    return full_name


# ===================================================================
# ✅ 파일 경로에서 '파일명_배치번호.xlsx' 형태의 배치번호 추출
# ===================================================================
def extract_batch_no_from_path(file_path: str) -> int:
    """파일 경로에서 '파일명_배치번호.xlsx' 형태의 배치번호 추출"""
    base = os.path.basename(file_path)  # 예: cctr_20250729170248.xlsx
    try:
        name_part = os.path.splitext(base)[0]  # 확장자 제거 → 'cctr_20250729170248'
        batch_str = name_part.split("_")[1]    # '_' 기준으로 분리 → '20250729170248'
        return int(batch_str)
    except Exception:
        raise ValueError(f"❌ 유효한 파일명 형식이 아닙니다: {file_path}")

