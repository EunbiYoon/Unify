from django.db import models
from django.contrib.auth.models import User
from user.models import CustomUser

# Create your models here.
class DeliveryData(models.Model):
    tracking_number=models.CharField(max_length=255)
    registered_by=models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    receiver=models.CharField(max_length=255)
    qty=models.IntegerField(default=1, blank=False, null=False)
    arriving_date=models.DateTimeField(auto_now_add=True)
    checkout=models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name_plural='Delivery Data'

