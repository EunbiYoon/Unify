from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect

# Create your views here.
@login_required(login_url='login_url')
def qualtiyhomeView(request):
    return redirect('costhome_url')