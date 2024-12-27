from django.urls import path
from .views import DhomeView, DsearchView, DsearchcheckoutView, DcheckoutView, DaddView, DgenqrView,DallexcelView, DdeleteView

urlpatterns = [
    path('',DhomeView,name='Dhome_url'),
    path('search',DsearchView, name='Dsearch_url'),
    path('checkout/<int:pk>',DsearchcheckoutView, name='Dsearchout_url'),
    path('checkout',DcheckoutView,name="Dcheckout_url"),
    path('generate/qrcode',DgenqrView,name='Dgenerateqr_url'),
    path('add',DaddView,name='Dadd_url'),
    path('search/download',DallexcelView,name='Dallexcel_url'),
    path('delete/<int:pk>',DdeleteView,name='Ddelete_url'),
]