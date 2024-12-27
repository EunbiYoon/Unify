from django.urls import path
from .views import detail_bom_view, detail_cost_view, category_bom_view, category_cost_view, detail_comment_view
urlpatterns = [
    path('bom-comparison/<int:pk>/', detail_bom_view, name='detail_bom_url'),
    path('cost-review/<int:pk>/', detail_cost_view, name='detail_cost_url'),
    path('bom-comparison/category', category_bom_view, name='category_bom_url'),
    path('cost-review/category', category_cost_view, name='category_cost_url'),
    path('comment/<int:pk>/', detail_comment_view, name='detail_comment_url')
]
