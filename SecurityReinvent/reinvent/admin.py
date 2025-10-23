from django.contrib import admin
from .models import ReinventData

class ReinventDataAdmin(admin.ModelAdmin):
    list_display=('program','applied_day','user','request_at')
admin.site.register(ReinventData,ReinventDataAdmin)
