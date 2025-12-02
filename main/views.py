from django.shortcuts import render

# Create your views here.
def main_home(request):
    return render(request, 'main_home.html', {})

def portfolio_view(request):
    return render(request, "index.html")