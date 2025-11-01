from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from account.views import user_router,org_router,division_router,group_router,team_router,role_router, logoutView

api = NinjaAPI(version="1.0.0")

api.add_router("user", user_router)
api.add_router("org", org_router)
api.add_router("division", division_router)
api.add_router("group", group_router)
api.add_router("team", team_router)
api.add_router("role", role_router)

urlpatterns = [
    path("", api.urls),  # ✅ 이 라인이 반드시 있어야 /account/docs 작동
    path('logout/',logoutView, name="logout_url"),
]
