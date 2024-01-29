from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('ilovepdfs/', include('blog.urls', namespace='blog')),
    path('tools/', include('tools.urls')),
]
