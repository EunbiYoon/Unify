from django.urls import path
from .views import PhomeView, PviolatorView, PviolatorlistView, PviolatordeleteView, Pviolator1ticketView, Pviolator2ticketView, PemployeeView, PemployeelistView, PemployeedeleteView, PviolatorexcelView, PemployeeexcelView

urlpatterns = [
    path('',PhomeView,name='Phome_url'),
    path('violator/register',PviolatorView,name='Pviolator_url'),
    path('violator/list',PviolatorlistView,name='Pviolator_list_url'),
    path('violator/delete/<int:data_id>',PviolatordeleteView,name='Pviolator_delete_url'),
    path('violator/ticket/<int:data_id>',Pviolator1ticketView,name='Pviolator_ticket_url'),
    path('violator/tow/<int:data_id>',Pviolator2ticketView,name='Pviolator_tow_url'),
    path('employee_of_month/register',PemployeeView,name='Pemployee_url'),
    path('employee_of_month/list',PemployeelistView,name='Pemployee_list_url'),
    path('employee_of_month/delete/<int:data_id>',PemployeedeleteView,name='Pemployee_delete_url'),
    path('violator/list/download',PviolatorexcelView,name='Pviolator_excel_url'),
    path('employee_of_month/list/download',PemployeeexcelView,name='Pemployee_excel_url'),
]