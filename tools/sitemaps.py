# tools/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from . import urls as tool_urls

class ToolsSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        # Only expose GET landing pages. Upload/action endpoints are not indexable.
        excluded = ('_include', '_file', 'download', 'alias', 'full')
        return sorted({
            pattern.name for pattern in tool_urls.urlpatterns
            if pattern.name and not any(pattern.name.endswith(suffix) for suffix in excluded)
        })

    def location(self, item):
        return reverse('tools:' + item)
