from django import forms
from CostData.report.models import Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['week', 'category', 'comment_body']

class EditForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['week', 'category', 'comment_body']