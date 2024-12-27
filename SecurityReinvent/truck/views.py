from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import TruckData
from .forms import TruckCheckInForm, TruckCheckOutForm
from django.utils import timezone
from django.http import HttpResponse
import csv
import datetime
from django.shortcuts import get_object_or_404

# Create your views here.
def ThomeView(request):
    return render(request, 'truck_home.html')

def TcheckinView(request):
    if request.method=='POST':
        get_driver=request.POST.get('drivername')
        get_plate=request.POST.get('plate')
        get_company=request.POST.get('company')
        get_truck=request.POST.get('trucknumber')
        get_cntr=request.POST.get('cntr')
        get_trailer=request.POST.get('trailer')
        get_seal=request.POST.get('seal')
        if get_driver!='' and get_plate!='' and get_company!='' and get_truck!='' and get_cntr!='' and get_trailer!='' and get_seal!='':
            data_add=TruckData(
                            driver_name=get_driver, license_plate=get_plate,
                            company_name=get_company, truck_number=get_truck,
                            direct_cntr=get_cntr, in_trailer=get_trailer,
                            seal_number=get_seal)
            data_add.checkin_pic=request.user
            data_add.checkin_at=timezone.now()
            data_add.save()
            return redirect('Ttruckhistory_url')
        else:
            empty_list=list()
            if get_driver=='':
                empty_list.insert(0,'Driver Name')
            if get_plate=='':
                empty_list.insert(1,"License Plate")
            if get_company=='':
                empty_list.insert(2,"Company")
            if get_truck=='':
                empty_list.insert(3,"Truck Number")
            if get_cntr=='':
                empty_list.insert(4,"Direct Delivery CNTR")
            if get_trailer=='':
                empty_list.insert(5,"Trailer Number")
            if get_seal=='':
                empty_list.insert(6,"Seal Number")
            empty_string=', '.join(empty_list)
            context={
                'error_message':empty_string
            }
            return render(request,'truck_in.html', context)
    return render(request,'truck_in.html')

def TcheckoutView(request,pk):
    truck_data=TruckData.objects.get(pk=pk)
    if request.method=='POST':
        get_trailer=request.POST.get('outtrailer')
        get_load=request.POST.get('load')
        
        truck_data.out_trailer=get_trailer
        truck_data.load_status=get_load
        truck_data.checkout_at=timezone.now()
        truck_data.checkout_pic=request.user
        truck_data.save()

        return redirect('Ttruckhistory_url')
    context={
        'truck_data':truck_data
    }
    return render(request, 'truck_out.html', context)

def ThistoryView(request):
    truck_list=TruckData.objects.all().order_by('-checkin_at')
    context={
        'truck_list':truck_list
    }
    return render(request, 'truck_history.html', context)

def TdetailView(request, pk):
    truck_detailed=get_object_or_404(TruckData, pk=pk)
    context={
        'truck_detailed':truck_detailed
    }
    return render(request, 'truck_detail.html', context)

@login_required
def TeditInView(request,pk):
    truck_edit=get_object_or_404(TruckData, pk=pk)
    if request.method=="POST":
        form=TruckCheckInForm(request.POST, request.FILES, instance=truck_edit)
        if form.is_valid():
            form.save()
            return redirect('Ttruckdetail_url', pk=pk)
        else:
            message="Form is not valid"
            context={
                "message":message,
                'form':form,
                'info':"Check In",
                'data':truck_edit
            }
            return render(request, "truck_edit.html", context)
    else:
        form=TruckCheckInForm(instance=truck_edit)
        context={
            'form':form,
            'info':"Check In",
            'data':truck_edit
        }
    return render(request, 'truck_edit.html', context)

@login_required
def TeditOutView(request,pk):
    truck_edit=get_object_or_404(TruckData, pk=pk)
    if request.method=="POST":
        form=TruckCheckOutForm(request.POST, instance=truck_edit)
        if form.is_valid():
            form.save()
            return redirect('Ttruckdetail_url', pk=pk)
        else:
            message="Form is not valid"
            context={
                "message":message,
                'form':form,
                'info':"Check Out",
                'data':truck_edit
            }
            return render(request, "truck_edit.html", context)
    else:
        form=TruckCheckOutForm(instance=truck_edit)
        context={
            'form':form,
            'info':"Check Out",
            'data':truck_edit
        }
    return render(request, 'truck_edit.html', context)
@login_required
def TdeleteView(request, pk):
    selected_data=TruckData.objects.get(pk=pk)
    selected_data.delete()
    return redirect('Ttruckhistory_url')

def TallexcelView(request):
    data=TruckData.objects.all().order_by('-id') 
    
    # Convert queryset to DataFrame
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.datetime.now().strftime("%m%d")
    filename = f"TruckTrackingList_{current_date}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['No','Driver Name','License Plate', 'Company Name', 'Truck Number','Direct Delivery CNTR','Trailer Number','Seal Number','Check-In PIC','Check-In Time','Check-Out PIC','Check-Out Time','Out Trailer Number/Bobtail','Load Status']) # CSV header
    
    for index, obj in enumerate(data, start=1):
        writer.writerow([index, obj.driver_name, obj.license_plate, obj.company_name, obj.truck_number, obj.direct_cntr, obj.in_trailer, obj.seal_number, obj.checkin_pic, obj.checkin_at, obj.checkout_pic, obj.checkout_at, obj.out_trailer, obj.load_status]) # Replace with your model fields
    return response

