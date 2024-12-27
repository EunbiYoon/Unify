from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from CostData.report.models import Post, Comment
from .forms import PostForm, EditForm
from django.urls import reverse_lazy
from django.shortcuts import render
from django.db.models import ObjectDoesNotExist

# Create your views here.
def CosthomeView(request):
    try:
        recent_bom = Post.objects.filter(category__name='BOM Comparison').latest('date_added')
    except ObjectDoesNotExist:
        recent_bom = None

    try:
        recent_cost = Post.objects.filter(category__name='Cost Review').latest('date_added')
    except ObjectDoesNotExist:
        recent_cost = None

    context = {
        'recent_bom': recent_bom.id if recent_bom else None,
        'recent_cost': recent_cost.id if recent_cost else None,
    }
    return render(request, 'cost_home.html', context)

class CommentView(ListView):
    template_name='comment.html'
    ordering=['-date_added']
    model=Comment

class CommentDetailView(DetailView):
    model=Comment
    template_name='comment_detail.html'

class CommentAddView(CreateView):
    model=Comment
    form_class=PostForm
    template_name='comment_add.html'
    success_url=reverse_lazy('comment_url')
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class CommentUpdateView(UpdateView):
    model=Comment
    form_class=EditForm
    template_name='comment_update.html'
    success_url=reverse_lazy('comment_url')
    
class CommentDeleteView(DeleteView):
    model=Comment
    template_name='comment_delete.html'
    success_url=reverse_lazy('comment_url')