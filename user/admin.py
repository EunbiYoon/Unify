from django.contrib import admin
from .models import CustomUser, Team

# Register your models here.
class TeamAdmin(admin.ModelAdmin):
    list_display=('team_name','team_manager','manager_email')
    def team_name(self,obj):
        return obj.team.name if obj.team.manager else None
admin.site.register(Team,TeamAdmin)

class CustomUserAdmin(admin.ModelAdmin):
    list_display=('username','team_at','first_name','last_name','username','email','myday_credit', 'is_superuser')
admin.site.register(CustomUser, CustomUserAdmin)