from django.urls import path
from .views import ThomeView, TcheckinView, TcheckoutView, ThistoryView, TdetailView,TeditInView,TeditOutView,TdeleteView,TallexcelView

urlpatterns = [
    path('',ThomeView,name='Thome_url'),
    path('in',TcheckinView,name='Ttruckin_url'),
    path('out/<int:pk>',TcheckoutView,name='Ttruckout_url'),
    path('history',ThistoryView,name='Ttruckhistory_url'),
    path('detail/<int:pk>',TdetailView,name='Ttruckdetail_url'),
    path('edit/in/<int:pk>',TeditInView,name='TtruckeditIn_url'),
    path('edit/out/<int:pk>',TeditOutView,name='TtruckeditOut_url'),
    path('delete/<int:pk>',TdeleteView,name='Ttruckdelete_url'),
    path('history/download',TallexcelView,name='Tallexcel_url')
]
