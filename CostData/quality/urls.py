from django.urls import path
from .views import qualtiyhomeView

urlpatterns = [
    path('',qualtiyhomeView,name='qualityhome_url')
]