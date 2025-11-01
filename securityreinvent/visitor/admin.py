from django.contrib import admin
from .models import VisitorData

# Register your models here.
class VisitorDataAdmin(admin.ModelAdmin):
    list_display=('id','visitor_purpose','user','register_at')
admin.site.register(VisitorData,VisitorDataAdmin)
