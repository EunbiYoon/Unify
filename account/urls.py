from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from account.views import user_router,org_router,division_router,group_router,team_router,role_router, htmlaccountView, htmlloginView, htmlregisterView, htmllogoutView
from django.contrib.auth import views as auth_views

api = NinjaAPI(version="1.0.0",title="Welcome to Account API")
api.add_router("user", user_router)
api.add_router("org", org_router)
api.add_router("division", division_router)
api.add_router("group", group_router)
api.add_router("team", team_router)
api.add_router("role", role_router)

urlpatterns = [
    path("api/", api.urls),  # Ninja API는 여기로 (이 파일이 account/ 아래 include됐다면 /account/가 prefix)

    # ✅ 장고(HTML)용 URL은 하이픈 + 슬래시 권장
    path("register-login/", htmlaccountView, name="account_url"),
    path("login/", htmlloginView, name="login_url"),
    path("register/", htmlregisterView, name="register_url"),
    path("logout/", htmllogoutView, name="logout_url"),

    # 비밀번호 재설정(장고 기본뷰)
    path("login_password/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("email_reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("email_reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]