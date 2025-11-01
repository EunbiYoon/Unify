# 표준 라이브러리
from collections import defaultdict
from typing import List

# Django
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from ninja.errors import HttpError

# Third-party
from ninja import Router, Query
from pydantic import BaseModel
from ninja import Router, File, Form
from ninja.files import UploadedFile
from django.contrib.admin.models import LogEntry
from django.db import transaction, connection


# 로컬 앱
from .models import Division, Group, Team, Role, CustomUser
from .schemas import (
    Division_In, Division_Out,
    Group_In, Group_Update_In, Group_Out,
    Team_In, Team_Update_In, Team_Out,
    Role_In, Role_Out,
    Signup_Schema, User_Info_Out, TeamTreeSchema,
    Login_Schema, Login_Response, ResetPasswordSchema,
    UserSchema, UserUpdateSchema, UserInitiateIn
)
from finance.models import CctrProcessed
from typing import Optional
from account.utils.initiate_user import initiate_bulk_user

user_router = Router(tags=["[User Authenticaion Page] User Management"])
org_router = Router(tags=["[User Authenticaion Page - DEV] Organization(Division,Group,Team,Role) Initate"])
division_router = Router(tags=["[User Authenticaion Page - DEV] Division Management"])
group_router = Router(tags=["[User Authenticaion Page - DEV] Group Management"])
team_router = Router(tags=["[User Authenticaion Page - DEV] Team Management"])
role_router = Router(tags=["[User Authenticaion Page - DEV] Role Management"])

# ===================================================================
# ✅ User Signup/Login/Logout/Reset-Password
# ===================================================================
# upload all the role
@user_router.post("/initiate")
def initiate_users_from_excel(request, file: UploadedFile = File(...)):
    """
    업로드된 엑셀을 이용해 User만 생성/업데이트.
    - owner는 항상 request.user
    - 파일은 영구 저장하지 않음 (임시파일 사용)
    """
    if not request.user.is_authenticated:
        raise HttpError(401, "Please login first")

    # (선택) 간단한 확장자 체크
    if not (file.name or "").lower().endswith(".xlsx"):
        raise HttpError(400, "Only xlsx file can upload")
    result = initiate_bulk_user(file)
    return result

def _reset_pk_sequence_portable(table_name: str):
    """
    DB 벤더별로 PK 시퀀스를 현재 MAX(id)+0 상태로 맞춤
    (다음 INSERT는 max(id)+1부터 시작)
    """
    qname = connection.ops.quote_name
    with connection.cursor() as cursor:
        # 현재 최대 id
        cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {qname(table_name)}")
        max_id = cursor.fetchone()[0] or 0

        if connection.vendor == "postgresql":
            # 시퀀스 이름 얻어서 setval
            cursor.execute("SELECT pg_get_serial_sequence(%s, 'id')", [table_name])
            seq_name = cursor.fetchone()[0]
            if seq_name:
                cursor.execute("SELECT setval(%s, %s, true)", [seq_name, max_id])

        elif connection.vendor == "sqlite":
            # sqlite_sequence row 보장 후 max_id로 맞춤
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(1) FROM sqlite_sequence WHERE name=%s", [table_name])
                exists = cursor.fetchone()[0]
                if exists:
                    cursor.execute("UPDATE sqlite_sequence SET seq=%s WHERE name=%s", [max_id, table_name])
                else:
                    cursor.execute("INSERT INTO sqlite_sequence(name, seq) VALUES (%s, %s)", [table_name, max_id])

        elif connection.vendor in ("mysql", "mariadb"):
            cursor.execute(f"ALTER TABLE {qname(table_name)} AUTO_INCREMENT = %s", [max_id + 1])
        else:
            # 기타 벤더는 스킵
            pass

@user_router.post("/reset/records")
def purge_users_except_first(request):
    """
    CustomUser: id가 가장 작은 1명은 유지, 나머지 모두 삭제 + PK 시퀀스 리셋
    - django_admin_log 참조는 선행해서 NULL 처리 (FK 에러 방지)
    """
    if not request.user.is_authenticated:
        raise HttpError(401, "Please login first")

    User = get_user_model()
    table_name = User._meta.db_table

    before = User.objects.count()

    # 남길 사용자 id (가장 작은 id)
    keep_id = (
        User.objects.order_by("id").values_list("id", flat=True).first()
    )

    # 1) admin 로그에서 참조 끊기 (user_id -> NULL)
    LogEntry.objects.filter(user_id__isnull=False).exclude(user_id=keep_id).update(user_id=keep_id)

    # 2) 첫 번째 사용자 제외 전부 삭제
    deleted_count, detail = User.objects.exclude(id=keep_id).delete()

    # 3) PK 시퀀스 리셋
    _reset_pk_sequence_portable(table_name)

    return {
        "success": True,
        "message": f"첫 사용자(id={keep_id})를 제외하고 모두 삭제 완료. (총 {deleted_count}건)",
        "before_count": before,
        "kept_id": keep_id,
        "deleted_count": deleted_count,
        "detail": detail,
    }

# 화원가입
@user_router.post("/signup")
def signup(request, data: Signup_Schema):
    """📌 회원가입: 팀/롤 이름으로 사용자 생성 (team_name / role_name 기준)"""
    # 1) 사용자 중복
    if CustomUser.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username already exists")

    division_instance = group_instance = team_instance = None

    try:
        # 2) 역할 조회/생성
        role_instance, _ = Role.objects.get_or_create(role_name=data.role_name)

        # 역할별 조직 계층 보장
        if data.role_name in ["site-admin", "finance-admin"]:
            pass

        elif data.role_name == "division-leader":
            if not data.division_name:
                raise HttpError(400, "division_name is required for division-leader")
            division_instance, _ = Division.objects.get_or_create(
                division_name=data.division_name
            )

        elif data.role_name == "group-leader":
            if not (data.division_name and data.group_name):
                raise HttpError(400, "division_name and group_name are required for group-leader")
            division_instance, _ = Division.objects.get_or_create(
                division_name=data.division_name
            )
            # ✅ 변수명: division_instance 사용
            group_instance, _ = Group.objects.get_or_create(
                group_name=data.group_name,
                defaults={"division_parent": division_instance},
            )
            if group_instance.division_parent_id != division_instance.id:
                group_instance.division_parent = division_instance
                group_instance.save(update_fields=["division_parent"])

        elif data.role_name == "team-leader":
            if not (data.division_name and data.group_name and data.team_name):
                raise HttpError(400, "division_name, group_name and team_name are required for team-leader")
            division_instance, _ = Division.objects.get_or_create(
                division_name=data.division_name
            )
            group_instance, _ = Group.objects.get_or_create(
                group_name=data.group_name,
                defaults={"division_parent": division_instance},
            )
            if group_instance.division_parent_id != division_instance.id:
                group_instance.division_parent = division_instance
                group_instance.save(update_fields=["division_parent"])

            team_instance, _ = Team.objects.get_or_create(
                team_name=data.team_name,
                defaults={
                    "group_parent": group_instance,
                    "division_parent": division_instance,
                },
            )
            # 부모 연결 보정
            changed = []
            if team_instance.group_parent_id != (group_instance.id if group_instance else None):
                team_instance.group_parent = group_instance
                changed.append("group_parent")
            if team_instance.division_parent_id != (division_instance.id if division_instance else None):
                team_instance.division_parent = division_instance
                changed.append("division_parent")
            if changed:
                team_instance.save(update_fields=changed)

        else:
            raise HttpError(400, "Invalid role")

        # 3) 사용자 생성 (비번 해시)
        user = CustomUser.objects.create(
            username=data.username,
            email=data.email,
            phone_number=data.phone_number,
            password=make_password(data.password),
            division=division_instance,
            group=group_instance,
            team=team_instance,
            role=role_instance,
        )

    except IntegrityError:
        raise HttpError(500, "Database error occurred, please try again.")

    return {"message": "✅ User created", "user_id": user.id}

def to_user_info(user) -> User_Info_Out:
    role = getattr(user, "role", None)
    division = getattr(user, "division", None)
    group = getattr(user, "group", None)
    team = getattr(user, "team", None)

    def extract_last(part):
        return part.split("-")[-1] if part else None

    return User_Info_Out(
        user_id=user.id,
        user_name=user.username,
        role_id=role.id if role else None,
        role_name=role.role_name if role else None,
        division_id=division.id if division else None,
        division_name=extract_last(division.division_name) if division else None,
        group_id=group.id if group else None,
        group_name=extract_last(group.group_name) if group else None,
        team_id=team.id if team else None,
        team_name=extract_last(team.team_name) if team else None,
    )


@user_router.get("/me", response=User_Info_Out)
def user_find_me(request):
    user = request.user
    if not user.is_authenticated:
        raise HttpError(401, "Please login first")
    return to_user_info(user)  # ✅ 여기서 dict가 아닌 User_Info_Out 객체여야 함

def build_team_tree(user, only_my_team=False):
    role = getattr(user, "role", None)
    role_name = getattr(role, "role_name", None)
    user_team = getattr(user, "team", None)
    user_group = getattr(user, "group", None)
    user_division = getattr(user, "division", None)

    # CctrProcessed가 존재하면 
    if CctrProcessed.objects.exists():
        # 1. 가장 최신 배치넘버 조회
        latest_batch = CctrProcessed.objects.order_by("-batch_no").values_list("batch_no", flat=True).first()
        # 2. 해당 배치넘버를 가진 모든 객체 조회
        latest_cctr_objects = CctrProcessed.objects.filter(batch_no=latest_batch)
        if only_my_team and user_team:
            teams = latest_cctr_objects.filter(id=user_team.id)
        elif role_name in ["group-leader", "team-leader"]:
            teams = latest_cctr_objects.filter(group_parent=user_group)
        elif role_name == "division-leader":
            teams = latest_cctr_objects.filter(division_parent=user_division)
        elif role_name in ["site-admin", "finance-admin"] or user.is_superuser:
            teams = latest_cctr_objects.all()
        else:
            return {"organization": []}

    elif Team.objects.exists():
        if only_my_team and user_team:
            teams = Team.objects.filter(id=user_team.id)
        elif role_name in ["group-leader", "team-leader"]:
            teams = Team.objects.filter(group_parent=user_group)
        elif role_name == "division-leader":
            teams = Team.objects.filter(division_parent=user_division)
        elif role_name in ["site-admin", "finance-admin"] or user.is_superuser:
            teams = Team.objects.all()
        else:
            return {"organization": []}
    
    else:
        raise HttpError(400, "Need to fill out Team or CctrProcessed first")

    tree = defaultdict(lambda: defaultdict(list))
    for team in teams.select_related("group_parent", "division_parent"):
        division_name = team.division_parent.division_name.split("-")[-1]
        group_name = team.group_parent.group_name.split("-")[-1]
        team_name = team.team_name.split("-")[-1]
        tree[division_name][group_name].append(team_name)

    result = {
        "organization": [
            {
                "division_name": division,
                "groups": [
                    {
                        "group_name": group,
                        "teams": team_list
                    }
                    for group, team_list in groups.items()
                ]
            }
            for division, groups in tree.items()
        ]
    }
    return result


@user_router.get("/select", response=TeamTreeSchema)
def get_accessible_team_names(request):
    """📌 유저 권한(role)에 따라 접근 가능한 팀 리스트를 트리 구조로 반환"""
    if not request.user.is_authenticated:
        raise HttpError(401, "Login Required")

    return build_team_tree(request.user, only_my_team=False)

# ✅ 로그인
@user_router.post("/login", response=Login_Response)
def loginView(request, data: Login_Schema):
    """📌 로그인: 세션 인증 + 최소 사용자 정보 반환"""
    user = authenticate(request, username=data.username, password=data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")

    login(request, user)
    return {
        "message": "Login successful",
        "user": to_user_info(user),
    }

# ✅ 로그아웃
@user_router.post("/logout")
def logoutView(request):
    logout(request)
    return redirect('mainhome_url')

# ✅ 비밀번호 재설정
@user_router.post("/reset-password")
def reset_password(request, data: ResetPasswordSchema):
    if not request.user.is_authenticated:
        raise HttpError(401, "❌ Login Required")

    if data.password != data.password_confirmed:
        raise HttpError(400, "❌ Both passward are not matched")

    user = request.user
    user.set_password(data.password)
    user.save()

    # ✅ 비번 변경 후 현재 세션 유지
    update_session_auth_hash(request, user)

    return {"success": True, "message": "✅ 비밀번호가 변경되었습니다."}


# ===================================================================
# ✅ User CRUD
# ===================================================================
@user_router.get("/all", response=List[UserSchema])
def list_users(request):
    return CustomUser.objects.all()

@user_router.get("/detail/{user_id}", response=UserSchema)
def get_user(request, user_id: int):
    return get_object_or_404(CustomUser, id=user_id)

# --------- Helpers ---------
def _unique_guard(u: CustomUser, data: dict):
    """username/email 중복 방지"""
    if "username" in data and data["username"] \
       and CustomUser.objects.exclude(id=u.id).filter(username=data["username"]).exists():
        raise HttpError(409, "Already existed username")
    if "email" in data and data["email"] \
       and CustomUser.objects.exclude(id=u.id).filter(email=data["email"]).exists():
        raise HttpError(409, "Already existed email")

def _resolve_fk_by_string(value: Optional[str], model, field: str):
    """문자열로 FK 조회 (없으면 None)"""
    if value in (None, ""):
        return None
    return get_object_or_404(model, **{field: value})

# --------- Update ---------
@user_router.put("/detail/{user_id}")
def update_user(request, user_id: int, payload: UserUpdateSchema):
    u = get_object_or_404(CustomUser, id=user_id)
    data = payload.model_dump(exclude_unset=True)

    # 1) 유니크 검증
    _unique_guard(u, data)

    # 2) 일반 필드
    for f in ("username","email","first_name","last_name","phone_number","is_active"):
        if f in data:
            setattr(u, f, data[f])

    # 3) 비밀번호
    if "password" in data and data["password"]:
        u.set_password(data["password"])

    # 4) FK 매핑
    if "division" in data:
        u.division = _resolve_fk_by_string(data["division"], Division, "division_name")
    if "group" in data:
        u.group = _resolve_fk_by_string(data["group"], Group, "group_name")
    if "team" in data:
        u.team = _resolve_fk_by_string(data["team"], Team, "team_name")
    if "role" in data:
        u.role = _resolve_fk_by_string(data["role"], Role, "role_name")

    u.save()
    return {"success": True, "message": f"✅ 사용자 업데이트 완료: {u.username}", "id": u.id}

    
@user_router.delete("/detail/{user_id}")
def delete_user(request, user_id: int):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    return {"success": True}


# ===================================================================
# ✅ Organization(Division,Group,Team) Initiate
# ===================================================================


# ✅ 팀 초기화 (슈퍼유저만)
# @org_router.post("/init")
# def init_team_master(request, reset: bool = Query(False)):
#     """📌 (DEV Only - DB Migration) Initiate Organization DB (Division/Group/Team/Role 시드)
#     - reset=True: 팀(및 옵션에 따라 상위) 초기화 후 재생성
#     - 내부적으로 account.utils.initiate_org.run(...) 실행
#     """
#     result = init_orgs(reset=reset)
#     return {"message": "Team master initialized", **result}

@org_router.post("/reset/division&group")
def flush_all_orgs(request):
    """📌 Division, Group 데이터 전체 삭제 (순서 중요)"""
    if not request.user.is_superuser:
        raise HttpError(403, "❌ This is only available for superuser authority")

    # 삭제 순서 주의: Team → Group → Division
    Group.objects.all().delete()
    Division.objects.all().delete()

    return {"success": True, "message": "✅ Delete all organization info (Group → Division)"}

# ===================================================================
# ✅ Division CRUD
# ===================================================================

# ✅ Division 전체 조회
@division_router.get("/all", response=list[Division_Out])
def list_divisions(request):
    """📌 Division 전체 조회"""
    return Division.objects.all()

# ✅ Division 생성
@division_router.post("/new", response=Division_Out)
def create_division(request, data: Division_In):
    """📌 Division 생성"""
    division = Division.objects.create(division_name=data.division_name)
    return division

# ✅ Division 수정
@division_router.put("/detail/{division_id}", response=Division_Out)
def update_division(request, division_id: int, data: Division_In):
    """📌 Division 수정: division_name 변경"""
    division = get_object_or_404(Division, id=division_id)
    division.division_name = data.division_name
    division.save()
    return division

# ✅ Division 삭제
@division_router.delete("/detail/{division_id}")
def delete_division(request, division_id: int):
    """📌 Division 삭제"""
    division = get_object_or_404(Division, id=division_id)
    division.delete()
    return {"message": "Division deleted"}


# ===================================================================
# ✅ Group DB CRUD
# ===================================================================

# ✅ Group 전체 조회
@group_router.get("/all", response=list[Group_Out])
def list_groups(request):
    """📌 Group 전체 조회 (+ 상위 Division 정보 포함)"""
    groups = Group.objects.select_related("division_parent").all()
    return [
        {
            "id": g.id,
            "group_name": g.group_name,
            "division_id": g.division_parent_id,
            "division_name": g.division_parent.division_name if g.division_parent else None,
        }
        for g in groups
    ]

# ✅ Group 생성 (division_name으로 Division 찾기)
@group_router.post("/new", response=Group_Out)
def create_group(request, data: Group_In):
    """📌 Group 생성: division_name으로 상위 Division 지정"""
    division = get_object_or_404(Division, division_name=data.division_name)
    group = Group.objects.create(
        division_parent=division,
        group_name=data.group_name,
    )
    return {
        "id": group.id,
        "group_name": group.group_name,
        "division_id": division.id,
        "division_name": division.division_name,
    }

# ✅ Group 수정 (group_name 변경 / division 이동)
@group_router.put("/detail/{group_id}", response=Group_Out)
def update_group(request, group_id: int, data: Group_Update_In):
    """📌 Group 수정: 그룹명 변경 / 다른 Division으로 이동"""
    group = get_object_or_404(Group, id=group_id)

    # 그룹명 변경
    if data.group_name is not None:
        group.group_name = data.group_name

    # division 이동
    if data.division_name is not None:
        new_div = get_object_or_404(Division, division_name=data.division_name)
        group.division_parent = new_div

    group.save()
    return {
        "id": group.id,
        "group_name": group.group_name,
        "division_id": group.division_parent_id,
        "division_name": group.division_parent.division_name if group.division_parent else None,
    }

# ✅ Group 삭제
@group_router.delete("/detail/{group_id}")
def delete_group(request, group_id: int):
    """📌 Group 삭제"""
    group = get_object_or_404(Group, id=group_id)
    group.delete()
    return {"message": "Group deleted"}


# ===================================================================
# ✅ Team DB CRUD
# ===================================================================

# ✅ 팀 전체 조회
@team_router.get("/all", response=list[Team_Out])
def list_teams(request):
    """📌 Team 전체 조회"""
    # select_related로 group 이름까지 같이 직렬화하려면 아래처럼 가공 반환도 가능
    teams = CctrProcessed.objects.select_related("group_parent").all()
    return [
        {
            "id": t.id,
            "team_name": t.team_name,
            "group_id": t.group_parent_id,
            "group_name": t.group_parent.group_name if t.group_parent else None,
        }
        for t in teams
    ]

# ✅ 팀 생성
@team_router.post("/new", response=Team_Out)
def create_team(request, data: Team_In):
    """📌 Team 생성: group_id로 상위 Group 지정"""
    team = CctrProcessed.objects.create(
        team_name=data.team_name,           # ← team_name
        group_parent_id=data.group_id,     # ← group_id
    )
    # 응답 스키마에 맞춰 dict로 반환(그룹명 포함)
    group = team.group_parent
    return {
        "id": team.id,
        "team_name": team.team_name,
        "group_id": team.group_parent_id,
        "group_name": group.group_name if group else None,
    }

# ✅ 팀 수정
@team_router.put("/detail/{team_id}", response=Team_Out)
def update_team(request, team_id: int, data: Team_Update_In):
    """📌 Team 수정: 팀명 변경 / 다른 Group으로 이동"""
    team = get_object_or_404(Team, id=team_id)
    if data.team_name is not None:
        team.team_name = data.team_name
    if data.group_id is not None:
        team.group_parent_id = data.group_id
    team.save()
    group = team.group_parent
    return {
        "id": team.id,
        "team_name": team.team_name,
        "group_id": team.group_parent_id,
        "group_name": group.group_name if group else None,
    }

# ✅ 팀 삭제
@team_router.delete("/detail/{team_id}")
def delete_team(request, team_id: int):
    """📌 Team 삭제"""
    team = get_object_or_404(Team, id=team_id)
    team.delete()
    return {"message": "Team deleted"}


# ===================================================================
# ✅ Role DB Initiate + CRUD
# ===================================================================
# ✅ 역할 전체 조회
@role_router.get("/all", response=list[Role_Out])
def list_roles(request):
    """📌 Role 전체 조회"""
    return Role.objects.all()

# ✅ 역할 생성
@role_router.post("/new", response=Role_Out)
def create_role(request, data: Role_In):
    """📌 Role 생성"""
    role = Role.objects.create(role_name=data.role_name)  # ← role_name
    return role

# ✅ 역할 수정
@role_router.put("/detail/{role_id}", response=Role_Out)
def update_role(request, role_id: int, data: Role_In):
    """📌 Role 수정: role_name 변경"""
    role = get_object_or_404(Role, id=role_id)
    role.role_name = data.role_name                         # ← role_name
    role.save()
    return role

# ✅ 역할 삭제
@role_router.delete("/detail/{role_id}")
def delete_role(request, role_id: int):
    """📌 Role 삭제"""
    role = get_object_or_404(Role, id=role_id)
    role.delete()
    return {"message": "Role deleted"}

