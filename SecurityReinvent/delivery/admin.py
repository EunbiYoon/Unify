from django.contrib import admin
from .models import DeliveryData

class DeliveryDataAdmin(admin.ModelAdmin):
    list_display=['tracking_number','arriving_date','registered_by','receiver','qty','checkout']

# Register your models here.
admin.site.register(DeliveryData, DeliveryDataAdmin)
