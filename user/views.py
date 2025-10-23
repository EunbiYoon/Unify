from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Team, CustomUser
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import views as auth_views

################# User Authentication ###################
def accountView(request):
    team_list=Team.objects.all()
    previous_page = request.META.get('HTTP_REFERER', '/')
    context = {
        'previous_page': previous_page,
        'team_list':team_list
    }
    return render(request, 'account.html',context)

def customloginView(request):
    if request.method=="POST":
        get_id=request.POST['id'] 
        get_password=request.POST['password']
        user=authenticate(request, username=get_id, password=get_password)
        if user is not None:
            login(request, user)
            return redirect('mainhome_url')        
        else:
            messages.error(request,"Wrong Credentials", extra_tags='login')
            return HttpResponseRedirect(reverse('account_url'))
    return redirect('account_url')

def registerView(request):
    if request.method=='POST':
        get_fname=request.POST['fname']
        get_lname=request.POST['lname']
        get_email=request.POST['email']
        get_team=request.POST['team']
        get_pass1=request.POST['pass1']
        get_pass2=request.POST['pass2']

        if get_fname=='' or get_lname=='' or get_team=='' or get_email=='' or get_pass1=='' or get_pass2=='':
            messages.error(request,'Please fill out all blanks.',  extra_tags='register')
            return HttpResponseRedirect(reverse('account_url'))
        if CustomUser.objects.filter(first_name=get_fname, last_name=get_lname).exists():
            messages.error(request,'Firstname and lastname already exists.',  extra_tags='register')
            return HttpResponseRedirect(reverse('account_url'))
        if get_team=="----":
            messages.error(request,'Team required, contact eunbi1.yoon@lge.com if team not exists.',  extra_tags='register')
            return HttpResponseRedirect(reverse('account_url')) 
        if CustomUser.objects.filter(email=get_email).exists():
            messages.error(request,'Email already exists.',  extra_tags='register')
            return HttpResponseRedirect(reverse('account_url'))  
        if "@" not in get_email:
            messages.error(request,'Wrong email form.',  extra_tags='register')
            return HttpResponseRedirect(reverse('account_url')) 
        email_spilt=get_email.split('@')
        email_start=email_spilt[0].lstrip()  
        email_end=email_spilt[1].strip()  
        #@ sign need to split           
        if email_end!="lge.com":
            messages.error(request,'Email address must end with lge.com.',  extra_tags='register')
            return HttpResponseRedirect(reverse('account_url'))
        if get_pass1!=get_pass2:
            messages.error(request,'Passwords are not matched.',  extra_tags='register')
            return HttpResponseRedirect(reverse('account_url'))
        if len(get_pass1)<8:
            messages.error(request,'Password should be more than 8 digits.',  extra_tags='register')
            return HttpResponseRedirect(reverse('account_url'))

        #foreign key
        get_team_Team=Team.objects.get_or_create(team_name=get_team)
        #make fix the firstname and lastname capitalize
        cap_fname=get_fname.capitalize()
        cap_lname=get_lname.capitalize()
        #hashed password
        hashed_password=make_password(get_pass1)
        user=CustomUser.objects.create(username=email_start, first_name=cap_fname, last_name=cap_lname, email=get_email, team_at=get_team_Team[0], password=hashed_password)
        user.save()
        if user is not None:
            login(request, user)
            return redirect('mainhome_url')
    
        
def logoutView(request):
    logout(request)
    return redirect('mainhome_url')

