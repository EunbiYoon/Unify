from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime

class Division(models.Model):
    id = models.BigAutoField(primary_key=True)
    division_name = models.CharField(max_length=50, unique=True)  # 예: "SS-TDD"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)      # 변경 시각
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="owned_divisions"
    )

    def __str__(self):
        return self.division_name


class Group(models.Model):
    id = models.BigAutoField(primary_key=True)
    division_parent = models.ForeignKey(Division, on_delete=models.CASCADE, related_name="groups")
    group_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="owned_groups"
    )

    def __str__(self):
        return self.group_name


class Team(models.Model):
    id = models.BigAutoField(primary_key=True)
    division_parent = models.ForeignKey(Division, on_delete=models.CASCADE, related_name="teams_in_division")
    group_parent = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="teams_in_group")
    team_name = models.CharField(max_length=20)
    code = models.CharField(max_length=10)
    batch_no = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="owned_teams"
    )

    def __str__(self):
        return self.team_name


class Role(models.Model):
    id = models.BigAutoField(primary_key=True)
    role_name = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="owned_roles"
    )

    def __str__(self):
        return self.role_name


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="owned_users"
    )

    def __str__(self):
        return self.username
