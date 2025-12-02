from django.urls import path
from . import views
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from pathlib import Path


urlpatterns = [
    path('', views.main_home, name="mainhome_url"),
    path("portfolio/", views.portfolio_view, name="portfolio_url"),
]
urlpatterns += [
    re_path(
        r"^portfolio/(?P<path>.+)$",
        serve,
        {"document_root": Path(settings.BASE_DIR) / "build"},
    ),
]
