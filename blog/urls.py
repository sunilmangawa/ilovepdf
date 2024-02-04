from django.urls import path
from . import views
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    path('blog/', views.post_list, name='post_list'),
    path('<slug:post>/', views.post_detail, name='post_detail'),#<int:year>/<int:month>/<int:day>/
    # path('<slug:post>/', views.PostDetailView.as_view(), name='post_detail'),
    path('<int:post_id>/comment/',views.post_comment, name='post_comment'),
    path('tag/<slug:tag_slug>/',views.post_list, name='post_list_by_tag'),
    path('feed/', LatestPostsFeed(), name='post_feed'),
]