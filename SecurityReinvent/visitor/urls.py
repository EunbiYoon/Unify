from django.urls import path
from .views import VhomeView, VregisterView, VmyView, VdetailView, VlistView, VdeleteView, VlistdeleteView, VtogglemyView, VtogglelistView, VapprovalView, VrejectView, VpassView, VcheckinView, VcheckoutView, VmyexcelView, VallexcelView

urlpatterns = [
    path('',VhomeView,name='Vhome_url'),
    path('register',VregisterView,name='Vregister_url'),
    path('my',VmyView,name='Vmy_url'),
    path('detail/<int:pk>',VdetailView,name='Vdetail_url'),
    path('list',VlistView,name='Vlist_url'),
    path('delete/<int:data_id>',VdeleteView,name='Vdelete_url'),
    path('list/delete/<int:data_id>',VlistdeleteView,name='Vlistdelete_url'),
    path('my/<int:data_id>', VtogglemyView, name='Vmytoggle_url'),
    path('list/<int:data_id>', VtogglelistView, name='Vlisttoggle_url'),
    path('list/approve/<int:data_id>',VapprovalView, name='Vlistapproval_url'),
    path('list/reject/<int:data_id>',VrejectView, name='Vlistreject_url'),
    path('list/parkingpass/<int:data_id>', VpassView, name='Vparkingpass_url'),
    path('list/checkin/<int:data_id>', VcheckinView, name='Vcheckin_url'),
    path('list/checkout/<int:data_id>', VcheckoutView, name='Vcheckout_url'),
    path('my/download',VmyexcelView,name='Vmyexcel_url'),
    path('my/download',VallexcelView,name='Vallexcel_url')
]