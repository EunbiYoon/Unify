from django.db import models
from user.models import CustomUser
from django.utils import timezone

# Create your models here.
class Category(models.Model):
    name=models.CharField(max_length=255)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural='  1) Categories'

class Week(models.Model):
    name=models.CharField(max_length=255)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural='  2) Weeks'

class Post(models.Model):
    category=models.ForeignKey(Category, on_delete=models.CASCADE)
    week=models.ForeignKey(Week, on_delete=models.CASCADE)
    author=models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_added=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.category)+ ' | ' + str(self.week)
    class Meta:
        verbose_name_plural='  3) Posts'

class Comment(models.Model):
    category=models.ForeignKey(Category, on_delete=models.CASCADE)
    week=models.ForeignKey(Week, on_delete=models.CASCADE)
    author=models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_added=models.DateTimeField(auto_now_add=True)
    comment_body = models.TextField()
    # def save(self, *args, **kwargs):
    #     self.date_added = timezone.now()
    #     super(Comment, self).save(*args, **kwargs)
    class Meta:
        verbose_name_plural='  4) Comments'