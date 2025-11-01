#!/usr/bin/env python3
import os
import sys
import re
from typing import Union

import django
from django.db import transaction
from django.db.models import Q, Model
from django.db import models
import pandas as pd
from datetime import datetime

# =========================
# Django 초기화
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


# =========================
# 모델 import
# =========================
from finance.models import SapRaw, ProcessClose
import pandas as pd
import numpy as np
from datetime import datetime
from django.db.models import Max
from django.contrib.auth import get_user_model

User = get_user_model()

def main(close_user):
    # 사용자 객체 얻기
    try:
        user = User.objects.get(username=close_user)
    except User.DoesNotExist:
        raise ValueError(f"User '{user}'가 존재하지 않습니다.")

    # 최신 batch_no
    latest_batch = SapRaw.objects.exclude(batch_no__isnull=True).aggregate(m=Max("batch_no"))["m"]

    # 최신 배치에서 가장 큰 period 값
    latest_period = SapRaw.objects.filter(batch_no=latest_batch).aggregate(m=Max("period"))["m"]

    # 연도는 항상 앞 4자리
    year = int(latest_period[:4])

    # 나머지는 월
    month = int(latest_period[4:])

    # ✅ 저장
    ProcessClose.objects.create(
        year=year,
        month=month,
        closed_by=user,
        timestamp=datetime.now(),
    )
    

if __name__ == "__main__":
    main(close_user="admin")  