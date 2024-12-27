from django.urls import path
from .views import homeView,securityhomeView,reinventhomeView

urlpatterns = [
    path('',homeView,name='sr_home_url'),
    path('security',securityhomeView,name='securityhome_url'),
    path('reinvent',reinventhomeView,name='reinventhome_url')
]