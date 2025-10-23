from django.contrib import admin

# Register your models here.
from .models import Category, Week, Post, Comment

admin.site.register(Category)
admin.site.register(Week)
admin.site.register(Post)
admin.site.register(Comment)