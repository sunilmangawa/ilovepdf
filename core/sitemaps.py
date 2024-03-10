# core/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class CoreSitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        # Return a list of URL names you want to include in the sitemap
        return ['core:home', 'core:about_us', 'core:contact_us', 'core:terms_and_condition', 'core:privacy_policy']

    def location(self, items):
        # Generate the absolute URL for a given URL name
        return reverse(items)
