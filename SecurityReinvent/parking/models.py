from django.db import models
from user.models import CustomUser

# Create your models here.
class ViolatorData(models.Model):
    car_plate=models.CharField(max_length=255)
    parking_lot=models.CharField(max_length=255)
    parking_at=models.DateTimeField(auto_now_add=True)
    violate_count=models.IntegerField(null=False, blank=False)
    register_by=models.ForeignKey(CustomUser, on_delete=models.CASCADE)

class EmployeeOfMonthData(models.Model):
    employee_name=models.CharField(max_length=255)
    register_at=models.DateTimeField(auto_now_add=True)
    start_date=models.CharField(max_length=100, null=False, blank=False)
    end_date=models.CharField(max_length=100, null=True, blank=True)
    register_by=models.ForeignKey(CustomUser, on_delete=models.CASCADE)
