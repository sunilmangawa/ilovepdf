from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include
from django.views.i18n import set_language


urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),

    path('rosetta/', include('rosetta.urls')),

    path('', include('core.urls')),
    path('', include('blog.urls', namespace='blog')),
    path('tools/', include('tools.urls')),

    path(r'^set-language/$', set_language, name='set_language'),

    prefix_default_language = False,

)

