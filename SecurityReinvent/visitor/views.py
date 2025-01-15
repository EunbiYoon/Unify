from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import VisitorData
from datetime import datetime
from django.utils import timezone
from django.http import HttpResponse
import csv
import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string

security_manager='eunbi1.yoon@lge.com'
security_leader='eunbi1.yoon@lge.com'

# Create your views here.
def VhomeView(request):
    return render(request, 'visitor_home.html')

@login_required
def VregisterView(request):
    if request.method=='POST':
        get_name=request.POST.get('name')
        get_company=request.POST.get('company')
        get_date=request.POST.get('date')
        get_purpose=request.POST.get('purpose')
        get_laptop=request.POST.get('laptop')
        get_contact=request.POST.get('phone')
        get_remark=request.POST.get('remark')
        
        if get_name=="" or get_company=="" or get_date=="" or get_purpose=="":
            empty_list=list()
            print(3)
            if get_name=="":
                empty_list.insert(0,"Visitor's Name")
            if get_company=="":
                empty_list.insert(1,"Visitor's Company")
            if get_date=="":
                empty_list.insert(2,'Visit Date')
            if get_purpose=="":
                empty_list.insert(3,'Visit Purpose')
            empty_string=', '.join(empty_list)
            print(empty_string)
            context={
                'empty_message':empty_string
            }
            return render(request,'visitor_register.html', context)
        
        if len(get_date)>11:
            get_to_date=get_date.split('to')
            start_strip=get_to_date[0].replace(" ","")
            end_strip=get_to_date[1].replace(" ","")
            get_start=start_strip
            get_end=end_strip
        else:
            get_start=get_date
            get_end=""
        visitor_add=VisitorData(visitor_name=get_name, visitor_company=get_company, start_date=get_start, end_date=get_end, visitor_purpose=get_purpose, bring_laptop=get_laptop, pic_contact=get_contact, remark=get_remark, user=request.user, get_approval_status="Requested")
        visitor_add.save()
        return redirect('Vmy_url')
    return render(request, 'visitor_register.html')

@login_required
def VmyView(request):
    #if there is no contents -> no sending to templates
    try:
        visitor_mylist=VisitorData.objects.filter(user=request.user).order_by('-id')
        context={
            'visitor_mylist':visitor_mylist
        }
        return render(request, 'visitor_my.html', context)
    # if there is contents
    except:
        return render(request, 'visitor_my.html')

def VdetailView(request, pk):
    visitor_detail=VisitorData.objects.get(pk=pk)
    context={
        'visitor_detail':visitor_detail
    }
    return render(request, 'visitor_detail.html', context)

    
def VlistView(request):
    try:
        visitor_list=VisitorData.objects.all().order_by('-id')
        context={
            'visitor_list':visitor_list
        }
        return render(request, 'visitor_list.html', context)
    except:
        return render(request,'visitor_list.html')

@login_required
def VdeleteView(request, data_id):
    selected_data=VisitorData.objects.get(pk=data_id)
    selected_data.delete()
    return redirect('Vmy_url')


@login_required
def VlistdeleteView(request, data_id):
    if request.method=='POST':
        try:
            selected_data=VisitorData.objects.get(pk=data_id)
            selected_data.delete()
        except VisitorData.DoesNotExist:
            pass
    return redirect('Vlist_url')


@login_required
def VtogglemyView(request, data_id):
    if request.method=='POST':
        visitor=get_object_or_404(VisitorData, id=data_id)
        visitor.show_remark=not visitor.show_remark
        visitor.save()
        return redirect('Vmy_url')

def VtogglelistView(request, data_id):
    if request.method=='POST':
        visitor=get_object_or_404(VisitorData, id=data_id)
        visitor.show_remark=not visitor.show_remark
        visitor.save()
        return redirect('Vlist_url')

@login_required
def VapprovalView(request, data_id):
    approve_data=VisitorData.objects.get(id=data_id)
    approve_data.approval_status="Approved"
    approve_data.save()
    return redirect('Vlist_url')

@login_required
def VrejectView(request, data_id):
    approve_data=VisitorData.objects.get(id=data_id)
    approve_data.approval_status="Rejected"
    approve_data.save()
    return redirect('Vlist_url')

@login_required
def VpassView(request, data_id):
    parking_data=VisitorData.objects.get(id=data_id)
    return render(request, 'parkingpass.html', {'parking_list':parking_data})

@login_required
def VcheckinView(request, data_id):
    if request.method=="POST":
        checkin_data=VisitorData.objects.get(id=data_id)
        checkin_data.check_in=timezone.now()
        checkin_data.save()
        return redirect('Vlist_url')

@login_required
def VcheckoutView(request, data_id):
    if request.method=="POST":
        checkout_data=VisitorData.objects.get(id=data_id)
        checkout_data.check_out=timezone.now()
        checkout_data.save()
        return redirect('Vlist_url')  
    
@login_required
def VmyexcelView(request):
    data=VisitorData.objects.filter(user=request.user).order_by('-id')

    # Convert queryset to DataFrame
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.datetime.now().strftime("%m%d")
    filename = f"MyVisitorList_{current_date}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['No','Visitor Name', 'Visitor Company', 'Visit Date(Start)','Visit Date(End)','Visit Purpose','Bring Laptop', 'Visitor PIC','Remark', 'Check In','Check Out', 'Status','Requster','Request Date']) # CSV header
    
    for index, obj in enumerate(data, start=1):
        writer.writerow([index, obj.visitor_name, obj.visitor_company, obj.start_date, obj.end_date, obj.visitor_purpose, obj.bring_laptop, obj.pic, obj.remark, obj.check_in, obj.check_out, obj.status, obj.user,obj.register_at]) # Replace with your model fields
    return response



def VallexcelView(request):
    data=VisitorData.objects.all().order_by('-id') 
    
    # Convert queryset to DataFrame
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.datetime.now().strftime("%m%d")
    filename = f"AllVisitorList_{current_date}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['No','Request', 'Applied Day', 'Late Day(Flexible Worhours)','Remark','Register At','Requester']) # CSV header
    
    for index, obj in enumerate(data, start=1):
        writer.writerow([index, obj.program, obj.applied_day, obj.late_day, obj.remark, obj.request_at, obj.user]) # Replace with your model fields
    return response
