from django.shortcuts import render, redirect,  HttpResponseRedirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ReinventData
from django.urls import reverse
import csv
import datetime


# request
def RrequestView(request):
    active_tab = 'tab1'
    current_user=request.user
    user_credit=current_user.myday_credit
    context={
        'user_credit':user_credit,
        'active_tab': active_tab
    }
    return render(request, 're_request.html', context)


def Rflex_requestView(request):
    if request.method=='POST':
        next_day=request.POST.get('hidden_nextday')
        print(next_day)
        if next_day=='Not Applicable':
            messages.error(request,"Late day fininshed before 7PM. This is only possible to request when you finish after 7PM.",extra_tags='location1')
            return HttpResponseRedirect(reverse('Rrequest_url'))
        if not next_day:
            messages.error(request,"Please fill out late day finished blank.",extra_tags='location1')
            return HttpResponseRedirect(reverse('Rrequest_url'))
        else:
            get_program="Flexible Workhours"
            get_lateday=request.POST.get('lateday')
            get_nextday=next_day
            get_remark=request.POST.get('remark')
            add_data=ReinventData(program=get_program, late_day=get_lateday, applied_day=get_nextday, remark=get_remark, user=request.user)
            add_data.save()
            return redirect('Rmy_url')
        
@login_required
def Rmyday_requestView(request):
    if request.method=='POST':
        current_user=request.user
        user_credit=current_user.myday_credit
        if user_credit<=0:
            message2="There are no credits available for My Day. Credits reset to 1 on the first of each month."
            active_tab='tab2'
            context={
                'message2':message2,
                'active_tab':active_tab
            }
            return render(request, 're_request.html', context)
        else:
            #save reinvent
            get_program="My Day"
            get_date=request.POST.get('myday')
            get_remark=request.POST.get('remark')
            add_data=ReinventData(program=get_program, applied_day=get_date, remark=get_remark, user=request.user)
            add_data.save()
            #save user
            current_user.myday_credit-=1
            current_user.save()
            return redirect('Rmy_url')
        

# list view
@login_required
def RmyView(request):
    reinvent_mylist=ReinventData.objects.filter(user=request.user).order_by('-id')
    context={
        'reinvent_mylist':reinvent_mylist,
    }
    return render(request, 're_my.html', context)

@login_required
def RteamView(request):
    current_user=request.user
    user_team=current_user.team_at

    ReinventData_instances=ReinventData.objects.filter(user__team_at=user_team).order_by('-id')

    context={
        'reinvent_teamlist':ReinventData_instances,
        'my_team':user_team
    }
    return render(request, 're_team.html', context)

def RallView(request):
    reinvent_alllist=ReinventData.objects.all().order_by('-id')
    context={
        'reinvent_alllist':reinvent_alllist
    }
    return render(request, 're_all.html', context)

@login_required
def RmydeleteMessageView(request, data_id):
    selected_data=get_object_or_404(ReinventData, pk=data_id)
    context={
        'selected_data':selected_data
    }
    return render(request, 're_delete.html', context)

    
@login_required
def RmydeleteView(request, data_id):
    selected_data=get_object_or_404(ReinventData, pk=data_id)
    selected_program=selected_data.program
    if selected_program == 'My Day':
        current_user=request.user
        current_user.myday_credit+=1
        current_user.save()
    # delete the data
    selected_data.delete()
    return redirect('Rmy_url')
    

@login_required
def RmyexcelView(request):
    data=ReinventData.objects.filter(user=request.user).order_by('-id')

    # Convert queryset to DataFrame
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.datetime.now().strftime("%m%d")
    filename = f"MyREINVENT_{current_date}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['No','Request', 'Applied Day', 'Late Day(Flexible Worhours)','Remark','Request At','Team', 'Requester']) # CSV header
    
    for index, obj in enumerate(data, start=1):
        writer.writerow([index, obj.program, obj.applied_day, obj.late_day, obj.remark, obj.request_at, obj.user.team_at, obj.user]) # Replace with your model fields
    return response

@login_required
def RteamexcelView(request):
    current_user=request.user
    user_team=current_user.team_at
    data=ReinventData.objects.filter(user__team_at=user_team).order_by('-id')

    # Convert queryset to DataFrame
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.datetime.now().strftime("%m%d")
    filename = f"{user_team}TeamREINVENT_{current_date}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['No','Request', 'Applied Day', 'Late Day(Flexible Worhours)','Remark','Register At','Requester']) # CSV header
    
    for index, obj in enumerate(data, start=1):
        writer.writerow([index, obj.program, obj.applied_day, obj.late_day, obj.remark, obj.request_at, obj.user]) # Replace with your model fields
    return response


def RallexcelView(request):
    data=ReinventData.objects.all().order_by('-id') 
    
    # Convert queryset to DataFrame
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.datetime.now().strftime("%m%d")
    filename = f"AllREINVENT_{current_date}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['No','Request', 'Applied Day', 'Late Day(Flexible Worhours)','Remark','Register At','Requester']) # CSV header
    
    for index, obj in enumerate(data, start=1):
        writer.writerow([index, obj.program, obj.applied_day, obj.late_day, obj.remark, obj.request_at, obj.user]) # Replace with your model fields
    return response