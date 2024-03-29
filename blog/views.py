from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Page
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# from django.core.serializers import serialize

from django.db import connection 
from django.db.models import Count
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import TemplateDoesNotExist
from django.utils import translation
from django.utils.translation import get_language#, set_current_language
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from django.views.i18n import set_language
from meta.views import Meta
from parler.models import TranslationDoesNotExist
from parler.utils.context import switch_language
from parler.views import TranslatableSlugMixin
from taggit.models import Tag

from .forms import CommentForm

from .models import Post, Comment


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


# def post_json(request):
#     # Adjust the query as needed, e.g., using .all() for all posts or .filter() for specific ones.
#     posts = Post.objects.all()  
#     # Serialize the queryset
#     data = serialize('json', posts)
#     # Return an HttpResponse with JSON content
#     return JsonResponse(data, safe=False)

# def post_json_custom(request):
#     posts = Post.objects.all()
#     posts_list = list(posts.values('title', 'slug', 'intro'))  # Example fields
#     return JsonResponse({'posts': posts_list}, safe=False)

def post_detail(request, post):
    try:
        post = Post.published.translated(request.LANGUAGE_CODE).filter(translations__slug=post).first()
        if post != None:
            toolattachment = post.toolattachment
        else:
            post = get_object_or_404(Post.published, translations__slug=post)
            toolattachment = post.toolattachment
        meta = post.as_meta()  # Generate meta data
        meta.url = post.slug
        # print(f'meta: {meta}')
        # print(f'meta type: {type(post)}')
        # print(f'post: {post}')
        # print(f'post type: {type(post)}')
        # print(f'meta.title: {meta.title}')
        # print(f'meta.author: {meta.author}')
        # print(f'meta.url: {meta.url}')
        # print(f'meta.sitename: {meta.site_name}')
        # meta = Meta(
        #     extra_props = {'viewport': 'width=device-width, initial-scale=1.0, minimum-scale=1.0'},
        #     extra_custom_props=[('http-equiv', 'Content-Type', 'text/html; charset=UTF-8'),]
        # )

    except Post.DoesNotExist:
        raise Http404("Post does not exist")

    # comments = post.comments.filter(active=True)
    comments = post.comments.filter(active=True) if hasattr(post, 'comments') else None
    form = CommentForm()
    # post_tags_ids = post.tags.values_list('id', flat=True)
    post_tags_ids = post.tags.values_list('id', flat=True) if hasattr(post, 'tags') else []
    # Check if post is not None before excluding it from similar_posts
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id) if post else None
    
    # Additional check for similar_posts
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4] if similar_posts else []

    try:
        if toolattachment:  # Check if toolattachment is not None
            tool_template = f"tools/{toolattachment.template_name}.html"
            tool_content = render(request, tool_template).content.decode('utf-8')
        else:
            tool_content = "Template not found: No toolattachment associated."
    except (TemplateDoesNotExist, AttributeError):
        tool_content = f"Template not found CHECK PATH: {tool_template}"

    return render(
        request,
        'blog/post_detail.html',
        {'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts, 'tool_content': tool_content, 'meta':meta}
    )

def get_schema(self, context=None):
    return {
        'name': self.object.get_meta_title(),
        'keywords': self.object.get_meta_keywords(),
        'description': self.object.get_meta_description(),
        'image': self.object.get_meta_image(),
        'author': self.object.get_meta_author(),
    }




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




# 100% working
# def post_detail(request, post):
#     try:
#         post = Post.published.translated(request.LANGUAGE_CODE).filter(translations__slug=post).first()
#         if post != None:
#             toolattachment = post.toolattachment
#         else:
#             post = get_object_or_404(Post.published, translations__slug=post)
#             toolattachment = post.toolattachment
#     except Post.DoesNotExist:
#         raise Http404("Post does not exist")

#     # comments = post.comments.filter(active=True)
#     comments = post.comments.filter(active=True) if hasattr(post, 'comments') else None
#     form = CommentForm()
#     # post_tags_ids = post.tags.values_list('id', flat=True)
#     post_tags_ids = post.tags.values_list('id', flat=True) if hasattr(post, 'tags') else []
#     # Check if post is not None before excluding it from similar_posts
#     similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id) if post else None
    
#     # Additional check for similar_posts
#     similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4] if similar_posts else []

#     try:
#         if toolattachment:  # Check if toolattachment is not None
#             tool_template = f"tools/{toolattachment.template_name}.html"
#             tool_content = render(request, tool_template).content.decode('utf-8')
#         else:
#             tool_content = "Template not found: No toolattachment associated."
#     except (TemplateDoesNotExist, AttributeError):
#         tool_content = f"Template not found CHECK PATH: {tool_template}"


#     return render(
#         request,
#         'blog/post_detail.html',
#         {'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts, 'tool_content': tool_content}
#     )

