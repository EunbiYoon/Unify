from django.urls import path
from .views import frontendView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', frontendView),  # React의 SPA 라우팅 처리
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)