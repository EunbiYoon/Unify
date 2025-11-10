from django.urls import path
from . import views
from django.views.generic import TemplateView  # 템플릿으로 간단히 응답할 때

urlpatterns = [
    path('med-vqa/', views.medvqa_view, name="medvqa_url"),
    path('datascience-system/', views.ds_view, name="ds_url"),
    path('machine-learning/', views.ml_view, name="ml_url"),
    path('artificial-intelligence/', views.ai_view, name="ai_url"),
    path('reinforcement-learning/', views.rl_view, name="rl_url")
]
