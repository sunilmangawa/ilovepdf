from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.urls import path
from . import views
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    path('blog/', views.post_list, name='post_list'),
    path('<slug:post>/', views.post_detail, name='post_detail'),#<int:year>/<int:month>/<int:day>/
    path('<int:post_id>/comment/',views.post_comment, name='post_comment'),
    path('tag/<slug:tag_slug>/',views.post_list, name='post_list_by_tag'),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    # path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'),
    # path('<int:post_id>/share/', views.post_share, name='post_share'),
    # path('<int:post_id>/comment/', views.post_comment, name='post_comment'),

    # path('post-json/', views.post_json, name='post_json'),

]

# urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
# urlpatterns += staticfiles_urlpatterns()

# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
