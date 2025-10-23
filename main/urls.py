from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_home, name="mainhome_url")
]