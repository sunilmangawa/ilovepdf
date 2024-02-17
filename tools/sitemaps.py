# tools/sitemaps.py

from django.contrib.sitemaps import Sitemap
from .models import ToolAttachment
from django.urls import reverse

class ToolsSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        # Return queryset of objects you want to include in the sitemap
        return ToolAttachment.objects.all()

    def location(self, item):
        # Generate the absolute URL for a given object
        return reverse('tools:' + item.template_name)
