from django.urls import path
from .views import CosthomeView, CommentView, CommentDetailView, CommentAddView, CommentUpdateView, CommentDeleteView

urlpatterns = [
    path('',CosthomeView,name='costhome_url'),
    path('comment',CommentView.as_view(),name='comment_url'),
    path('comment/<int:pk>',CommentDetailView.as_view(), name='article-detail'),
    path('comment/add', CommentAddView.as_view(), name='add_post'),
    path('comment/edit/<int:pk>', CommentUpdateView.as_view(), name="update_post"),
    path('comment/delete/<int:pk>/remove', CommentDeleteView.as_view(), name="delete_post"),
]