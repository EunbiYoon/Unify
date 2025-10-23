from django.contrib import admin
from .models import TruckData

class TruckDataAdmin(admin.ModelAdmin):
    list_display=('id', 'license_plate','driver_name', 'checkin_pic', 'checkin_at', 'checkout_pic', 'checkout_at')
admin.site.register(TruckData,TruckDataAdmin)

