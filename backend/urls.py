# system/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse  
from django.urls import re_path
from django.views.static import serve
from django.conf import settings
from pathlib import Path


LGSUPPORT_STATIC_ROOT = Path(settings.BASE_DIR) / "lgsupport" / "flaskapp" / "static"
QUALITY_STATIC_ROOT = Path(settings.BASE_DIR) / "quality" / "flasktodo" / "static"

urlpatterns = [
    path('',include('main.urls')),
    path('umass/',include('umass.urls')),             
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
    path('quality/dashboard', lambda request: JsonResponse({"message": "Flask 앱 에러 발생. QualityAnalysis폴더에서 flask run하여 에러를 확인하세요."})),
    re_path(r"^lgsupport/flaskapp/static/(?P<path>.*)$",serve,{"document_root": str(LGSUPPORT_STATIC_ROOT)}),
    re_path(r"^video/flasktodo/static/(?P<path>.*)$",serve,{"document_root": str(QUALITY_STATIC_ROOT)}),
]
