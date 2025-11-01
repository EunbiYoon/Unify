# account/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Division, Group, Team, Role, CustomUser

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ("id", "division_name")
    list_display_links = ("id", "division_name")
    readonly_fields = ("id",)               # ← 폼에 표시 (읽기전용)
    fields = ("id", "division_name")        # ← 폼 배치
    ordering = ("id",)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "group_name", "division_parent")
    list_display_links = ("id", "group_name")
    list_filter = ("division_parent",)
    search_fields = ("group_name", "division_parent__division_name")
    readonly_fields = ("id",)               # ← 중요
    fields = ("id", "division_parent", "group_name")  # ← 스크린샷 화면에 id가 나오게
    ordering = ("id",)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("id", "team_name", "code","group_parent", "division_parent","created_at","updated_at")  # division_parent 추가
    list_display_links = ("id", "team_name")
    list_filter = ("group_parent", "group_parent__division_parent")  # division_parent로 필터링 추가
    search_fields = ("team_name", "code","group_parent__group_name", "group_parent__division_parent__division_name")  # division_name으로 검색 가능
    readonly_fields = ("id",)
    fields = ("id", "code","division_parent", "group_parent", "team_name",)  # division_parent 추가
    ordering = ("id",)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "role_name")
    list_display_links = ("id", "role_name")
    search_fields = ("role_name",)
    readonly_fields = ("id",)
    fields = ("id", "role_name")
    ordering = ("id",)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "email", "is_staff", "role", "team", "group", "division")
    list_display_links = ("id", "username")
    search_fields = ("username", "email", "role__role_name", "team__team_name")
    list_filter = ("is_staff", "is_superuser", "is_active", "role", "division", "group")
    readonly_fields = ("id",)  # ← 사용자 폼에서도 id 보이게
    ordering = ("id",)
    fieldsets = UserAdmin.fieldsets + (
        ("Organization / Role", {
            "fields": ("id", "phone_number", "division", "group", "team", "role"),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Organization / Role", {"fields": ("division", "group", "team", "role")}),
    )
