# system/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse  


urlpatterns = [
    path('',include('main.urls')),              # ✅ 루트 헬스체크
    path("admin/", admin.site.urls),
    path("account/", include("account.urls")), 
    path("finance/", include("finance.urls")),  
    path('cost/', include('cost.cost_base.urls')),
    path('cost/report', include('cost.report.urls')),
    path('cost/report', include('cost.report.urls')),
    path('portfolio/', include('portfolio.urls')),
    path('securityreinvent/',include('securityreinvent.sr_base.urls')),
    path('security/visitor',include('securityreinvent.visitor.urls')),
    path('security/parking',include('securityreinvent.parking.urls')),
    path('security/truck',include('securityreinvent.truck.urls')),
    path('security/delivery',include('securityreinvent.delivery.urls')),
    path('reinvent',include('securityreinvent.reinvent.urls')),
]
