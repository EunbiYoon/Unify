from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from pathlib import Path
from django.http import HttpResponse
from django.conf.urls.static import static

LGSUPPORT_STATIC_ROOT = Path(settings.BASE_DIR) / "lgsupport" / "flaskapp" / "static"
QUALITY_STATIC_ROOT   = Path(settings.BASE_DIR) / "quality" / "flasktodo" / "static"

def wellknown_ok(_request):
    return HttpResponse(status=204)

urlpatterns = [
    path("", include("main.urls")),
    path("umass/", include("umass.urls")),
    path("admin/", admin.site.urls),
    path("account/", include("account.urls")),
    path("finance/", include("finance.urls")),

    path("cost/", include("cost.cost_base.urls")),
    path("cost/report/", include("cost.report.urls")),   # ✅ 중복 제거 + trailing slash

    path("securityreinvent/", include("securityreinvent.sr_base.urls")),
    path("security/visitor/", include("securityreinvent.visitor.urls")),
    path("security/parking/", include("securityreinvent.parking.urls")),
    path("security/truck/", include("securityreinvent.truck.urls")),
    path("security/delivery/", include("securityreinvent.delivery.urls")),
    path("reinvent/", include("securityreinvent.reinvent.urls")),

    re_path(r"^lgsupport/flaskapp/static/(?P<path>.*)$", serve, {"document_root": str(LGSUPPORT_STATIC_ROOT)}),
    re_path(r"^quality/flasktodo/static/(?P<path>.*)$", serve, {"document_root": str(QUALITY_STATIC_ROOT)}),

    path(".well-known/appspecific/com.chrome.devtools.json", wellknown_ok),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
