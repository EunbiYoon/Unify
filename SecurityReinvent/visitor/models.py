from django.db import models
from user.models import CustomUser

# Create your models here.
class VisitorData(models.Model):
    visitor_name=models.CharField(max_length=255, null=False, blank=False)
    visitor_company=models.CharField(max_length=255, null=False, blank=False)
    start_date=models.CharField(max_length=100, null=False, blank=False)
    end_date=models.CharField(max_length=100, null=True, blank=True)
    visitor_purpose=models.TextField(null=False, blank=False)
    bring_laptop=models.CharField(max_length=255, null=False, blank=False)
    pic_contact=models.CharField(max_length=255, null=True, blank=True)
    register_at=models.DateTimeField(auto_now_add=True)
    remark=models.TextField(null=True, blank=True)
    check_in=models.DateTimeField(null=True, blank=True)
    check_out=models.DateTimeField(null=True, blank=True)
    user=models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    approval_status=models.CharField(max_length=20)