from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Post, Comment
from .forms import CommentForm
import json
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required


@login_required(login_url='login_url')
def detail_bom_view(request, pk):
    #get the specific posts
    post = Post.objects.get(pk=pk)
 
    #initial settings
    model_input="DR"
    new_comment=None
    model_title="Dryer (Prod Model : RV13D1AMAZU.ABWEUUS / Sales Model : DLE3400W)"
    trend_template=str(pk)+'/DR_trend.html'
    item_template=str(pk)+'/DR_item.html'

    if request.method == 'POST':
        action=request.POST.get('action')
        if action in ['Dryer', 'Front Loader', 'Top Loader']:
            comment_form = CommentForm()
            if action=='Dryer':
                model_input="DR"
                model_title="Dryer (Prod Model : RV13D1AMAZU.ABWEUUS / Sales Model : DLE3400W)"
                trend_template=str(pk)+'/DR_trend.html'
                item_template=str(pk)+'/DR_item.html'
            elif action=="Front Loader":
                model_input="FL"
                model_title="Front Loader (Prod Model : F3P2CYUBW.ABWEUUS / Sales Model : WM4000HWA)"
                trend_template=str(pk)+'/FL_trend.html'
                item_template=str(pk)+'/FL_item.html'
            elif action=="Top Loader":
                model_input="TL"
                model_title="Top Loader (Prod Model : T1889EFHUW.ABWEUUS / Sales Model : WT7400CW)"
                trend_template=str(pk)+'/TL_trend.html'
                item_template=str(pk)+'/TL_item.html'

        elif action == 'Add Comment':
            comment_form = CommentForm(request.POST, instance=post)  # create new instance with required=False
            if comment_form.is_valid():
                name = request.user.username
                body = comment_form.cleaned_data['comment_body']
                new_comment = Comment(post=post, commenter_name=name, comment_body=body)
                new_comment.save()
                #refresh the page and delete the text
                return redirect('detail_bom_url', pk=post.pk) 
            else:
                print('form is invalid')   
    else:
        comment_form = CommentForm()    
    
    #week number
    week_num=post.week.name

    #get file
    file_result="file/bom/"+str(pk)+"/result_"+str(week_num)+".xlsx"
    file_compare="file/bom/"+str(pk)+"/BOM Comparison_"+str(model_input)+"_"+str(week_num)+".xlsx"

    #get graph json data
    graph_json_path=settings.STATICFILES_DIRS[0]+'/json/bom-graph.json'
    with open(graph_json_path,'r') as f:
        data=json.load(f)
    selected_graph=data[week_num][model_input]
    graph_column=selected_graph["columns"]
    graph_value=selected_graph["PAC Net - BOM Net"]
    graph_value1=selected_graph["Price Change"]
    graph_value2=selected_graph["Substitute"]
    graph_value3=selected_graph["PO + Substitute"]

    context = {
        'post_detail':post,
        'new_comment': new_comment,
        'form_detail':comment_form,
        'detail_graph_column':json.dumps(graph_column),
        'detail_graph_value':json.dumps(graph_value),
        'detail_graph_value1':json.dumps(graph_value1),
        'detail_graph_value2':json.dumps(graph_value2),
        'detail_graph_value3':json.dumps(graph_value3),
        'week_num':week_num,
        'model_title':model_title,
        'item_template':item_template,
        'trend_template':trend_template,
        'file_result':file_result,
        'file_compare':file_compare
    }
    return render(request, 'detail-bom.html', context)

@login_required(login_url='login_url')
def detail_cost_view(request, pk):
    #get the specific posts
    post = Post.objects.get(pk=pk)
 
    #initial settings
    model_input="BPA-FL"
    model_title="Front Loader BPA"
    new_comment=None
    if request.method == 'POST':
        action=request.POST.get('action')
        if action in ["Front Loader BPA","Top Loader BPA","Dryer BPA","Front Loader PAC","Top Loader PAC","Dryer PAC"]:
            if action=="Front Loader BPA":
                model_input="BPA-FL"
                model_title=action
            elif action=="Top Loader BPA":
                model_input="BPA-TL"
                model_title=action
            elif action=='Dryer BPA':
                model_input="BPA-DR"
                model_title=action
            elif action=="Front Loader PAC":
                model_input="PAC-FL"
                model_title=action
            elif action=="Top Loader PAC":
                model_input="PAC-TL"
                model_title=action
            elif action=='Dryer PAC':
                model_input="PAC-DR"
                model_title=action
            comment_form = CommentForm()

        elif action == 'Add Comment':
            comment_form = CommentForm(request.POST, instance=post)  # create new instance with required=False
            if comment_form.is_valid():
                name = request.user.username
                body = comment_form.cleaned_data['comment_body']
                new_comment = Comment(post=post, commenter_name=name, comment_body=body)
                new_comment.save()
                #refresh the page and delete the text
                return redirect('detail_cost_url', pk=post.pk) 
            else:
                print('form is invalid')   
    else:
        comment_form = CommentForm()  

    #week number
    week_num=post.week.name

    #get file
    file_result="file/cost/Cost Review_"+str(week_num)+".xlsx"

    #get table trend json data
    table_json_path=settings.STATICFILES_DIRS[0]+'/json/cost-trend.json'
    with open(table_json_path,'r') as f:
        json_trend=json.load(f)
    trend_json=json_trend[week_num][model_input]

    #get table item json data
    table_json_path=settings.STATICFILES_DIRS[0]+'/json/cost-item.json'
    with open(table_json_path,'r') as f:
        json_item=json.load(f)
    increase_item_json=json_item[week_num][model_input]["Increase"]
    decrease_item_json=json_item[week_num][model_input]["Decrease"]

    #get graph json data
    graph_json_path=settings.STATICFILES_DIRS[0]+'/json/cost-graph.json'
    with open(graph_json_path,'r') as f:
        json_graph=json.load(f)
    selected_graph=json_graph[week_num][model_input]
    graph_column=selected_graph["columns"]
    graph_index=selected_graph["index"]
    value0_column=selected_graph["value0"]
    value1_column=selected_graph["value1"]
    value2_column=selected_graph["value2"]
    value3_column=selected_graph["value3"]
    value4_column=selected_graph["value4"]
    value5_column=selected_graph["value5"]
    value6_column=selected_graph["value6"]

    context = {
        'post_detail':post,
        'new_comment': new_comment,
        'form_detail':comment_form,
        'graph_column':json.dumps(graph_column),
        'graph_index':json.dumps(graph_index),
        'graph_value0':json.dumps(value0_column),
        'graph_value1':json.dumps(value1_column),
        'graph_value2':json.dumps(value2_column),
        'graph_value3':json.dumps(value3_column),
        'graph_value4':json.dumps(value4_column),
        'graph_value5':json.dumps(value5_column),
        'graph_value6':json.dumps(value6_column),
        'trend_table_data':trend_json,
        'increase_item':increase_item_json,
        'decrease_item':decrease_item_json,
        'model_title':model_title,
        'week_num':week_num,
        'file_result':file_result
    }

    return render(request, 'detail-cost.html', context)

@login_required(login_url='login_url')
def category_bom_view(request):
    posts = Post.objects.filter(category__name='BOM Comparison').order_by('week__name')

    # Group posts by month
    grouped_posts = {}
    for post in posts:
        month_year = post.week.name[:5]  # Extract the month and year (e.g., '23.07')
        if month_year not in grouped_posts:
            grouped_posts[month_year] = []
        grouped_posts[month_year].append(post)

    context = {
        'category': 'BOM Comparison',
        'grouped_posts': grouped_posts
    }


    return render(request, 'category-bom.html', context)

@login_required(login_url='login_url')
def category_cost_view(request):
    posts = Post.objects.filter(category__name='Cost Review').order_by('week__name')

    # Group posts by month
    grouped_posts = {}
    for post in posts:
        month_year = post.week.name[:5]  # Extract the month and year (e.g., '23.07')
        if month_year not in grouped_posts:
            grouped_posts[month_year] = []
        grouped_posts[month_year].append(post)

    context = {
        'category': 'Cost Review',
        'grouped_posts': grouped_posts
    }


    return render(request, 'category-cost.html', context)


@login_required
def detail_comment_view(request, pk):
    get_post = get_object_or_404(Post, pk=pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = get_post
            comment.week = get_post.week
            comment.category = get_post.category
            comment.save()

    form = CommentForm()
    comments = Comment.objects.filter(category=get_post.category, week=get_post.week).order_by('-date_added')

    context={
        'form': form, 
        'post_detail': get_post, 
        'comments':comments
    }

    return render(request, 'detail-comment.html', context)
