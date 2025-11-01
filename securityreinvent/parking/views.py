from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import ViolatorData, EmployeeOfMonthData
from datetime import datetime
from django.http import HttpResponse
import csv
import datetime

# Create your views here.
def PhomeView(request):
    return render(request, 'parking_home.html')

def PviolatorView(request):
    if request.method=='POST':
        get_location=request.POST.get('location')
        get_plate=request.POST.get('plate')
        
        if get_plate=="":
            err="There is no plate number. Please type car plate number."
            return render(request, 'violator.html', {'message':err})
        else:
            get_plate_front=str(get_plate).lstrip()
            get_plate_back=str(get_plate_front).strip()
            get_plate_middle=str(get_plate_back).replace(" ","")
            get_plate=get_plate_middle


            recent_data=ViolatorData.objects.filter(car_plate=get_plate, parking_lot=get_location).order_by('-parking_at').first()
            if recent_data:
                previous_count=recent_data.violate_count
                plate_count=previous_count+1
            else:
                plate_count=1
            data_add=ViolatorData(car_plate=get_plate, parking_lot=get_location, violate_count=plate_count, register_by=request.user)
            data_add.save()
            return redirect('Pviolator_list_url')
    return render(request, 'violator.html')


def PviolatorlistView(request):
    violator_list=ViolatorData.objects.all().order_by('-id') 
    context={
        'violator_list':violator_list
    }
    return render(request, 'violator_list.html', context)

@login_required
def PviolatordeleteView(request, data_id):
    if request.method=='POST':
        selected_data=ViolatorData.objects.get(pk=data_id)
        selected_data.delete()
    return redirect('Pviolator_list_url')


def Pviolator1ticketView(request, data_id):
    if request.method=='POST':
        selected_data=ViolatorData.objects.get(pk=data_id)
        return render(request, 'violator_ticket.html', {'violator_data':selected_data})


def Pviolator2ticketView(request, data_id):
    if request.method=='POST':
        selected_data=ViolatorData.objects.get(pk=data_id)
        return render(request, 'violator_tow.html', {'violator_data':selected_data})


def PemployeeView(request):
    if request.method=='POST':
        get_name=request.POST.get('name')
        get_date=request.POST.get('date')
        if get_name=="":
            if get_date=="":
                err="You didn't enter anything. Please type employee name and duration date."
                return render(request, 'employee.html', {'message':err}) 
            else:
                err="There is no employee name. Please type employee name."
                return render(request, 'employee.html', {'message':err})
        elif get_date=="":
            err="There is no duration date. Please type duration date."
            return render(request, 'employee.html', {'message':err}) 
        else:
            if len(get_date)>11:
                get_to_date=get_date.split('to')
                start_strip=get_to_date[0].replace(" ","")
                end_strip=get_to_date[1].replace(" ","")
                get_start=start_strip
                get_end=end_strip
            else:
                get_start=get_date
                get_end=""
            data_add=EmployeeOfMonthData(employee_name=get_name, start_date=get_start, end_date=get_end, register_by=request.user)
            data_add.save()
            return redirect('Pemployee_list_url')
    return render(request, 'employee.html')


def PemployeelistView(request):
    employee_list=EmployeeOfMonthData.objects.all().order_by('-id') 
    context={
        'employee_list':employee_list
    }
    return render(request, 'employee_list.html', context)

@login_required
def PemployeedeleteView(request, data_id):
    if request.method=='POST':
        selected_data=EmployeeOfMonthData.objects.get(pk=data_id)
        selected_data.delete()
    return redirect('Pemployee_list_url')

def PviolatorexcelView(request):
    data=ViolatorData.objects.all().order_by('id') 
    
    # Convert queryset to DataFrame
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.datetime.now().strftime("%m%d")
    filename = f"AllViolatorParkingList_{current_date}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['No','Car Plate', 'Violate Date', 'Parking Location','Violate Count']) # CSV header
    
    for index, obj in enumerate(data, start=1):
        print(obj.parking_at)
        writer.writerow([index, obj.car_plate, obj.parking_at, obj.parking_lot, obj.violate_count]) # Replace with your model fields
    return response


def PemployeeexcelView(request):
    data=EmployeeOfMonthData.objects.all()
    
    # Convert queryset to DataFrame
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.datetime.now().strftime("%m%d")
    filename = f"AllEmployeeOfMonthParkingList_{current_date}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['No','Employee', 'Start Date','End Date', 'Parking Location','Request Date']) # CSV header
    
    for index, obj in enumerate(data, start=1):
        writer.writerow([index, obj.employee_name, obj.start_date, obj.end_date, 'Visitor Parking Lot Employee Of Month Section', obj.register_at]) # Replace with your model fields
    return response