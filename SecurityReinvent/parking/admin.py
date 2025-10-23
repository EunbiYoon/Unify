from django.contrib import admin
from .models import ViolatorData,EmployeeOfMonthData

# Register your models here.
class ViolatorDataAdmin(admin.ModelAdmin):
    list_display=['car_plate','parking_at','violate_count']
admin.site.register(ViolatorData, ViolatorDataAdmin)


# Register your models here.
class EmployeeOfMonthDataAdmin(admin.ModelAdmin):
    list_display=['employee_name','register_at','start_date','end_date']
admin.site.register(EmployeeOfMonthData, EmployeeOfMonthDataAdmin)
