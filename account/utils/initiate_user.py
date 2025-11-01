# utils/initiate_user.py
import io
import os
import sys
import re
from typing import Optional, Dict, Any
from datetime import datetime

import django
import pandas as pd
from django.db import transaction, connection
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

# ─────────────────────────────
# Django setup (adjust settings path to your project)
# ─────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from account.models import Division, Group, Team, Role  # noqa

User = get_user_model()

REQUIRED_COLS = ["1DEPTH", "2DEPTH", "3DEPTH", "USER NAME", "ROLE"]
DEFAULT_PASSWORD = "ptkorea12!@"  # unified password for all created/updated users

# ────────── helpers ──────────
def _norm(x: Any) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    return None if s in ("", "-", "nan", "NaN") else s

def _depth_rank(row) -> int:
    """Pick the most specific row per user (team > group > division)."""
    if _norm(row.get("3DEPTH")):
        return 3
    if _norm(row.get("2DEPTH")):
        return 2
    if _norm(row.get("1DEPTH")):
        return 1
    return 0

def _fmt_div(d1: str) -> str:
    return f"PTK-{d1}"

def _fmt_grp(d1: str, d2: str) -> str:
    return f"PTK-{d1}-{d2}"

def _fmt_team(d1: str, d2: str, d3: str) -> str:
    return f"PTK-{d1}-{d2}-{d3}"

def next_available_pk(model) -> int:
    """
    Return the smallest missing positive id (gap first). If no gap, return max(id)+1.
    ⚠ Reusing deleted PKs can be risky (FK/audit). Use only if you're sure.
    """
    table = model._meta.db_table
    with connection.cursor() as cur:
        cur.execute(f"""
            WITH bounds AS (
              SELECT COALESCE(MIN(id), 1) AS min_id,
                     COALESCE(MAX(id), 0) AS max_id
              FROM {table}
            ),
            seq AS (
              SELECT generate_series(1, (SELECT max_id FROM bounds)) AS id
            )
            SELECT seq.id
            FROM seq
            LEFT JOIN {table} t ON t.id = seq.id
            WHERE t.id IS NULL
            ORDER BY seq.id
            LIMIT 1;
        """)
        row = cur.fetchone()

    if row and row[0] is not None:
        return int(row[0])

    last = model.objects.order_by("-id").values_list("id", flat=True).first() or 0
    return last + 1

# ────────── core ──────────
def initiate_bulk_user(file) -> Dict[str, Any]:
    """
    Process an uploaded Excel (UploadedFile / file-like) to upsert CustomUser only.
    - DOES NOT persist the file; reads from memory.
    - Auto-creates Division/Group/Team/Role if missing (get_or_create).
    - owner is set to 'admin' user if present (since view cannot pass request.user).
    - All users passwords are set to DEFAULT_PASSWORD (overwrites existing).
    - NEW:
      1) Assign PK(id) using smallest available id (gap first), else max(id)+1.
      2) Insert users in the same order as the Excel rows.
    """
    # if role is empty then create role first
    ROLE_PRIORITY = {
        "team-leader": 1,
        "group-leader": 2,
        "division-leader": 3,
        "site-admin": 4,
        "finance-admin": 5
    }
    has_priority = any(f.name == "priority" for f in Role._meta.get_fields())

    if not Role.objects.exists():
        for role_name, pr in ROLE_PRIORITY.items():
            defaults = {}
            if has_priority:
                defaults["priority"] = pr
            Role.objects.get_or_create(role_name=role_name, defaults=defaults)

    # Resolve owner: use 'admin' user if exists
    owner = None
    try:
        owner = User.objects.get(username="admin")
    except User.DoesNotExist:
        owner = None

    # Read uploaded file into memory
    if hasattr(file, "chunks"):
        data_bytes = b"".join(file.chunks())
    else:
        data_bytes = file.read()
    bio = io.BytesIO(data_bytes)

    # Load Excel (first sheet by default)
    xlsx = pd.ExcelFile(bio)
    df = pd.read_excel(xlsx, sheet_name=0)

    # Validate required columns
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        return {"success": False, "message": f"엑셀에 필요한 컬럼이 없습니다: {missing}"}

    # Keep original row order
    df["__order"] = range(len(df))  # 0..N-1
    df["_rank"] = df.apply(_depth_rank, axis=1)

    # Deduplicate by USER NAME:
    # - Prefer deeper hierarchy (_rank desc)
    # - If rank ties, prefer earlier in Excel (__order asc)
    # Then restore original Excel order for creation (__order asc)
    df = (
        df.sort_values(["USER NAME", "_rank", "__order"], ascending=[True, False, True])
          .drop_duplicates(subset=["USER NAME"], keep="first")
          .sort_values(["__order"])
          .reset_index(drop=True)
    )

    created_user = 0
    updated_user = 0
    processed = []
    hashed_default = make_password(DEFAULT_PASSWORD)

    for _, row in df.iterrows():
        d1 = _norm(row["1DEPTH"])
        d2 = _norm(row["2DEPTH"])
        d3 = _norm(row["3DEPTH"])
        uname = _norm(row["USER NAME"])
        rname = _norm(row["ROLE"])

        if not uname:
            continue

        # Role (create if missing)
        role_obj = None
        if rname:
            role_obj, _ = Role.objects.get_or_create(
                role_name=rname,
                defaults={
                    "id": next_available_pk(Role),
                    **({"owner": owner} if owner else {}),
                },
            )

        # Division (create if missing)
        division_obj = None
        if d1:
            div_name = _fmt_div(d1)
            division_obj, _ = Division.objects.get_or_create(
                division_name=div_name,
                defaults={
                    "id": next_available_pk(Division),
                    **({"owner": owner} if owner else {}),
                },
            )

        # Group (create if missing) - requires division_parent
        group_obj = None
        if d2:
            if not division_obj:
                return {"success": False, "message": f"Group을 지정하려면 Division도 필요 (user={uname})"}
            grp_name = _fmt_grp(d1, d2)
            group_obj, _ = Group.objects.get_or_create(
                group_name=grp_name,
                defaults={
                    "id": next_available_pk(Group),
                    "division_parent": division_obj,
                    **({"owner": owner} if owner else {}),
                },
            )

        # Team (create if missing) - requires division_parent, group_parent, code, batch_no
        team_obj = None
        if d3:
            if not group_obj:
                return {"success": False, "message": f"Team을 지정하려면 Group도 필요 (user={uname})"}
            team_name = _fmt_team(d1, d2, d3)
            team_code = (d3 or "AUTO")[:10]
            batch_no = int(datetime.now().strftime("%Y%m%d%H%M%S"))

            team_obj, created_team = Team.objects.get_or_create(
                team_name=team_name,
                defaults={
                    "id": next_available_pk(Team),
                    "division_parent": division_obj,
                    "group_parent": group_obj,
                    "code": team_code,
                    "batch_no": batch_no,
                    **({"owner": owner} if owner else {}),
                },
            )
            # Backfill required fields if existing record lacks them
            if not created_team:
                changed = False
                if getattr(team_obj, "division_parent_id", None) != (division_obj.id if division_obj else None):
                    team_obj.division_parent = division_obj; changed = True
                if getattr(team_obj, "group_parent_id", None) != (group_obj.id if group_obj else None):
                    team_obj.group_parent = group_obj; changed = True
                if not (getattr(team_obj, "code", "") or "").strip():
                    team_obj.code = team_code; changed = True
                if not getattr(team_obj, "batch_no", None):
                    team_obj.batch_no = batch_no; changed = True
                if changed:
                    team_obj.save(update_fields=["division_parent", "group_parent", "code", "batch_no"])

        # User upsert (create if missing; set owner if available)
        user, created = User.objects.get_or_create(
            username=uname,
            defaults={
                "id": next_available_pk(User),
                **({"owner": owner} if owner else {}),
            },
        )
        user.role = role_obj
        user.division = division_obj
        user.group = group_obj
        user.team = team_obj

        # If existing user has empty owner, fill it
        if owner and not getattr(user, "owner_id", None):
            user.owner = owner

        # Set unified password (overwrite)
        user.password = hashed_default
        user.save()

        created_user += 1 if created else 0
        updated_user += 0 if created else 1

        processed.append({
            "username": uname,
            "role": getattr(role_obj, "role_name", None) if role_obj else None,
            "division": getattr(division_obj, "division_name", None) if division_obj else None,
            "group": getattr(group_obj, "group_name", None) if group_obj else None,
            "team": getattr(team_obj, "team_name", None) if team_obj else None,
            "depth_used": "team" if team_obj else ("group" if group_obj else ("division" if division_obj else None)),
        })

    return {
        "success": True,
        "message": "✅ 사용자 생성/업데이트 완료",
        "summary": {
            "created_user": created_user,
            "updated_user": updated_user,
            "total_users_processed": len(processed),
        },
        "processed": processed,
    }
