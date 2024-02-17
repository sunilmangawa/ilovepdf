# core/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class CoreSitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        # Return a list of URL names you want to include in the sitemap
        return ['home', 'about', 'contactus']

    def location(self, item):
        # Generate the absolute URL for a given URL name
        return reverse(item)
