from urllib.parse import urlsplit, urlunsplit

from django.conf import settings


def seo(request):
    """Expose stable, host-independent SEO URLs to the shared templates."""
    scheme = getattr(settings, "SEO_SITE_PROTOCOL", "https")
    host = getattr(settings, "SEO_SITE_DOMAIN", "ilovepdfconverteronline.com")
    path = urlsplit(request.get_full_path()).path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    if path != "/" and not path.endswith("/"):
        path += "/"

    canonical = urlunsplit((scheme, host, path, "", ""))
    return {
        "seo_canonical": canonical,
        "seo_site_name": getattr(settings, "META_SITE_NAME", "iLovePdfConverterOnline"),
        "seo_default_description": (
            "Free online PDF tools to merge, split, compress, convert and edit PDF files."
        ),
    }
