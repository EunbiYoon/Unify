from django.contrib import admin
from django.urls import path
from .views import RrequestView, Rmyday_requestView, Rflex_requestView, RmyView, RteamView,RallView, RmydeleteMessageView, RmydeleteView, RmyexcelView, RteamexcelView, RallexcelView

urlpatterns = [
    path('request',RrequestView, name='Rrequest_url'),
    path('request/flexibleworkhours',Rflex_requestView, name='Rrequestflex_url'),
    path('request/myday',Rmyday_requestView, name='Rrequestmyday_url'),
    path('me',RmyView, name='Rmy_url'),
    path('team',RteamView, name='Rteam_url'),
    path('all',RallView, name='Rall_url'),
    path('me/delete/message/<int:data_id>',RmydeleteMessageView,name='Rmydeletemessage_url'),
    path('me/delete/<int:data_id>',RmydeleteView,name='Rmydelete_url'),
    path('me/excel',RmyexcelView,name='Rmyexcel_url'),
    path('team/excel',RteamexcelView,name='Rteamexcel_url'),
    path('all/excel',RallexcelView,name='Rallexcel_url'),
]