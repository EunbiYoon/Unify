from django.shortcuts import render

# Create your views here.
def homeView(request):
    return render(request, 'sr_home.html')

def securityhomeView(request):
    return render(request, 'securityhome.html')

def reinventhomeView(request):
    return render(request, 'reinventhome.html')