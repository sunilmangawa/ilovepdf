from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from .models import Post, Comment
from django.http import Http404, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import CommentForm
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.db import connection 
from django.core.paginator import Page
from django.template import TemplateDoesNotExist

# Create your views here.
# def postList(request):
#     post = 'All Post will be listed on this page.'
#     context = {
#         'post': post
#     }
#     return render(request, 'blog/post_list.html', context)


# def post_detail(request):
#     post = 'All Post Detail will be listed on this page.'
#     context = {
#         'post': post
#     }
#     return render(request, 'blog/post_detail.html', context)


def post_list(request, tag_slug=None):
    # post_list = Post.published.all().prefetch_related('translations')
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    count = Post.published.count()
    return render(request, 'blog/post_list.html', {'posts': posts, 'tag': tag_slug, 'count': count})


def post_detail(request, post):
    try:
        post = get_object_or_404(Post.published, slug=post)
        # post = get_object_or_404(Post.published, translations__slug=post)
        # post = Post.published.get(translations__slug=post, status=Post.Status.PUBLISHED)
    except Post.DoesNotExist:
        raise Http404("Post does not exist")

    toolattachment = post.toolattachment
    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    try:
        tool_template = f"tools/{toolattachment.function_name}.html"
        tool_content = render(request, tool_template).content.decode('utf-8')
    except (TemplateDoesNotExist, AttributeError):
        tool_content = f"Template not found CHECK PATH: {tool_template}"

    return render(
        request,
        'blog/post_detail.html',
        {'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts, 'tool_content': tool_content}
    )


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    # A comment was posted
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Create a Comment object without saving it to the database
        comment = form.save(commit=False)
        # Assign the post to the comment
        comment.post = post
        # Save the comment to the database
        comment.save()
    return render(request, 'blog/post/comment.html',{'post': post,'form': form,'comment': comment})

