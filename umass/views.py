from django.shortcuts import render

# Create your views here.
def medvqa_view(request):
    return render(request, 'med_vqa.html')
def ds_view(request):
    return render(request, 'datascience_system.html')
def ml_view(request):
    return render(request, 'machine_learning.html')
def ai_view(request):
    return render(request, 'artificial_intelligence.html')
def rl_view(request):
    return render(request, 'reinforcement_learning.html')