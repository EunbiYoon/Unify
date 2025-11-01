# schemas.py
from typing import Optional
from ninja import Schema
from pydantic import BaseModel
from typing import List, Optional
from pydantic import BaseModel, Field, constr, EmailStr

# =========================
# Division
# =========================
class Division_In(Schema):
    division_name: str


class Division_Out(Schema):
    id: int
    division_name: str

    class Config:
        from_attributes = True


# =========================
# Group
# =========================
class Group_In(Schema):
    # 생성 시: Division은 'division_name'으로 지정
    division_name: str
    group_name: str


class Group_Update_In(Schema):
    # 수정 시: 그룹명 변경 및/또는 다른 Division으로 이동
    group_name: Optional[str] = None
    division_name: Optional[str] = None


class Group_Out(Schema):
    id: int
    group_name: str
    division_id: int
    division_name: str

    class Config:
        from_attributes = True


# =========================
# Team
# =========================
class Team_In(Schema):
    team_name: str
    group_id: int


class Team_Update_In(Schema):
    team_name: Optional[str] = None
    group_id: Optional[int] = None


class Team_Out(Schema):
    id: int
    team_name: str
    group_id: int
    group_name: str

    class Config:
        from_attributes = True


# =========================
# Role
# =========================
class Role_In(Schema):
    role_name: str


class Role_Out(Schema):
    id: int
    role_name: str

    class Config:
        from_attributes = True


# =========================
# Auth / User
# =========================
class Signup_Schema(Schema):
    username: str
    password: str
    email: str
    phone_number: Optional[str] = None
    division_name: Optional[str] = None
    group_name: Optional[str] = None
    team_name: Optional[str] = None
    role_name: str


class User_Info_Out(BaseModel):
    user_id: int
    user_name: str
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    division_id: Optional[int] = None
    division_name: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None

class TeamTreeSchema(Schema):
    organization: List[dict]  

class Login_Schema(Schema):
    username: str
    password: str


class Login_Response(Schema):
    message: str
    user: User_Info_Out


class ResetPasswordSchema(BaseModel):
    password: constr(min_length=5)
    password_confirmed: constr(min_length=5) = Field(alias="passwordConfirmed")

    class Config:
        populate_by_name = True


# =========================
# Auth / User
# =========================
class UserSchema(BaseModel):
    id: int
    username: str
    email: str | None = None
    class Config:
        from_attributes = True

class UserUpdateSchema(BaseModel):
    # Core
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    # FK as strings (exact match)
    division: Optional[str] = None         # matches Division.division_name
    group: Optional[str] = None            # matches Group.group_name
    team: Optional[str] = None             # matches Team.team_name
    role: Optional[str] = None             # matches Role.role_name



# =========================
# Auth / User
# =========================
class UserInitiateIn(Schema):
    file_path: str