from django.shortcuts import render, redirect
from .models import DeliveryData
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render
import datetime
from django.http import HttpResponse
import csv

# Create your views here.
def DhomeView(request):
    return render(request, 'delivery_home.html')


def DsearchView(request):
    item_list=DeliveryData.objects.all().order_by('-arriving_date')
    username=request.user.username
    context={
        'item_list':item_list,
        'username':username,
    }
    return render(request, 'delivery-search.html', context)


def DsearchcheckoutView(request, pk):
    delivery_data=DeliveryData.objects.get(pk=pk)
    delivery_data.checkout=timezone.now()
    print(delivery_data.checkout)
    delivery_data.save()
    return redirect('Dsearch_url')


def DcheckoutView(request):
    if request.method=='POST':
        scan_track=request.POST.get('result')

        #remove input 4 digit space
        scan_track=scan_track.replace(" ","")

        #check tracking_number exist
        try:
            entry=DeliveryData.objects.get(tracking_number=scan_track)
            if entry.checkout:
                context={
                    "error_message":"This package has already been checked out!"
                }
                return render(request,'delivery-out.html',context)
            else:
                entry.checkout=timezone.now()    
                entry.save()
                return redirect('Dsearch_url')
        except DeliveryData.DoesNotExist:
            context={
                "error_message":"Tracking number not exists!"
            }
            return render(request,'delivery-out.html',context)
    return render(request,'delivery-out.html')


def DaddView(request):
    if request.method=='POST':
        scan_track=request.POST.get('result')
        #remove input 4 digit space
        scan_track=scan_track.replace(" ","")
        scan_receiver=request.POST.get('receiver')

        #if each colum empty
        if not scan_track:
            context={
                "error_message":"Tracking number is empty!"
            }
            return render(request,'delivery-add.html',context)
        elif not scan_receiver:
            context={
                "error_message":"Receiever is empty!"
            }
            return render(request,'delivery-add.html',context)
        #compare existed query
        else:
            entry_exists=DeliveryData.objects.filter(tracking_number=scan_track).exists()
            if entry_exists:
                context={
                    "error":"Tracking number already exists!"
                }
                return render(request,'delivery-add.html',context)
            else:
                qr_code_scan=DeliveryData(receiver=scan_receiver, tracking_number=scan_track, registered_by=request.user)
                qr_code_scan.save()
                return redirect('Dsearch_url')
    return render(request,'delivery-add.html')


def DgenqrView(request):
    return render(request,'delivery-qr.html')


def DallexcelView(request):
    data=DeliveryData.objects.all().order_by('-id') 
    
    # Convert queryset to DataFrame
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.datetime.now().strftime("%m%d")
    filename = f"DeliveryPackageList_{current_date}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['No','Tracking Number','Receiver', 'Qty', 'Security Checkout', 'Arriving Date']) # CSV header
    
    for index, obj in enumerate(data, start=1):
        writer.writerow([index, obj.tracking_number, obj.receiver, obj.qty, obj.checkout, obj.arriving_date]) # Replace with your model fields
    return response

@login_required
def DdeleteView(request, pk):
    selected_data=DeliveryData.objects.get(pk=pk)
    selected_data.delete()
    return redirect('Dsearch_url')