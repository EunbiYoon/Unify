#!/usr/bin/env python3
import os
import sys
import logging
from typing import List, Dict, Optional

import django
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)

# ── Django 초기화 (CLI로 직접 실행할 때만 필요; 앱 내부 import 시에는 이미 설정됨)
def _ensure_django():
    if not settings.configured:
        PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        if PROJECT_ROOT not in sys.path:
            sys.path.append(PROJECT_ROOT)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
        django.setup()

# 기본 초기 데이터
DEFAULT_DATA: List[Dict[str, str]] = [
    {"code": "Y1B003", "description": "By day"},
    {"code": "Y1B005", "description": "Mark up"},
    {"code": "Y1B001", "description": "Media"},
]

def initiate_rakey(data: Optional[List[Dict[str, str]]] = None) -> Dict[str, int]:
    """
    RAKey 초기 데이터 삽입/업데이트.
    - 존재하지 않으면 생성
    - 존재하고 description이 다르면 업데이트
    - 같으면 스킵
    반환: {"created": int, "updated": int, "skipped": int}
    """
    from finance.models import RaKey  # django.setup 이후 import 안전

    rows = data or DEFAULT_DATA
    created = updated = skipped = 0


    for item in rows:
        code = (item.get("code") or "").strip()
        desc = (item.get("description") or "").strip()

        if not code:
            logger.warning("⚠️ code가 비어 스킵: %r", item)
            continue

        obj, was_created = RaKey.objects.get_or_create(
            code=code,
            defaults={"description": desc},
        )
        if was_created:
            created += 1
            logger.info("✅ Inserted: %s - %s", obj.code, obj.description)
        else:
            # description 변경 시에만 업데이트
            if desc and obj.description != desc:
                obj.description = desc
                obj.save(update_fields=["description"])
                updated += 1
                logger.info("🔄 Updated: %s - %s", obj.code, obj.description)
            else:
                skipped += 1
                logger.info("↩︎ Skipped (no change): %s", obj.code)

    summary = {"created": created, "updated": updated, "skipped": skipped}
    logger.info("📦 RAKey summary: %s", summary)
    return summary

