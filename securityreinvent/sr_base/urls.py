from django.urls import path
from .views import homeView,securityhomeView,reinventhomeView

urlpatterns = [
    path('',homeView,name='sr_home_url'),
    path('securitycenter',securityhomeView,name='securityhome_url'),
    path('reinventcenter',reinventhomeView,name='reinventhome_url')
]