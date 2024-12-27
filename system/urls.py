"""system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('',include('main.urls')),
    path('admin/', admin.site.urls),
    path('accounts/',include('user.urls')),
    path('portfolio/', include('Portfolio.urls')),
    path('securityreinvent/',include('SecurityReinvent.SR_Base.urls')),
    path('security/visitor/',include('SecurityReinvent.visitor.urls')),
    path('security/parking/',include('SecurityReinvent.parking.urls')),
    path('security/truck/',include('SecurityReinvent.truck.urls')),
    path('security/delivery/',include('SecurityReinvent.delivery.urls')),
    path('reinvent/',include('SecurityReinvent.reinvent.urls')),
    path('cost/', include('CostData.cost_base.urls')),
    path('cost/report/', include('CostData.report.urls')),
    path('quality/', include('CostData.quality.urls')),
]
