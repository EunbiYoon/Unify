from django import forms
from .models import TruckData

class TruckCheckInForm(forms.ModelForm):
    class Meta:
        model=TruckData
        fields=['driver_name', 'license_plate','company_name','truck_number','direct_cntr','in_trailer','seal_number','upload_file']

class TruckCheckOutForm(forms.ModelForm):
    class Meta:
        model=TruckData
        fields=['out_trailer','load_status','upload_file']
