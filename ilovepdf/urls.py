from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.i18n import set_language
from django.contrib.sitemaps.views import sitemap
from blog.sitemaps import PostSitemap
from core.sitemaps import CoreSitemap
from tools.sitemaps import ToolsSitemap
from django.views.generic.base import TemplateView



sitemaps = {
    'posts': PostSitemap,
    'core': CoreSitemap,
    'tools': ToolsSitemap,
}

urlpatterns = i18n_patterns(
    path('robots.txt/', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    path('admin/', admin.site.urls),

    path('rosetta/', include('rosetta.urls')),

    path("django-check-seo/", include("django_check_seo.urls")),

    path('', include('core.urls')),
    path('', include('blog.urls', namespace='blog')),
    path('tools/', include('tools.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path(r'^set-language/$', set_language, name='set_language'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path("", include("pwa.urls")),

    prefix_default_language = False,

)

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
