from django.db import models
from user.models import CustomUser
from datetime import datetime
import os 

def upload_location(instance, filename):
    now = datetime.now()
    
    if not instance.checkout_at:
        username=instance.checkin_pic.username
        folder_name = f'checkin/{username}/{now.strftime("%Y-%m-%d_%I-%M-%p")}'
    else:
        username=instance.checkout_pic.username
        folder_name = f'checkout/{username}/{now.strftime("%Y-%m-%d_%I-%M-%p")}'

    return os.path.join(folder_name, filename)

# Create your models here.
class TruckData(models.Model):
    driver_name=models.CharField(max_length=255, null=True)
    license_plate=models.CharField(max_length=255, null=True)
    company_name=models.CharField(max_length=255, null=True)
    truck_number=models.CharField(max_length=255, null=True)
    direct_cntr=models.CharField(max_length=255, null=True)
    in_trailer=models.CharField(max_length=255, null=True)
    seal_number=models.CharField(max_length=255, null=True)
    
    checkin_at=models.DateTimeField(blank=True, null=True)
    checkin_pic=models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='checkin_pic')
    checkout_at=models.DateTimeField(blank=True, null=True)
    checkout_pic=models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='checkout_pic', blank=True, null=True)
    
    out_trailer=models.CharField(max_length=255, null=True,blank=True)
    load_status=models.CharField(max_length=255, null=True,blank=True)

    upload_file = models.FileField(upload_to=upload_location, null=True, blank=True)
    
    def __str__(self):
        return str(self.license_plate)
    class Meta:
        verbose_name_plural='Truck Tracking Data'

