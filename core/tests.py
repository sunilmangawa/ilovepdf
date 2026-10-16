from django.test import SimpleTestCase
from django.urls import reverse


class CoreRoutesTests(SimpleTestCase):
    """Smoke-test public page URLs shared by every device."""

    public_pages = (
        ('core:home', '/'),
        ('core:about_us', '/about-us/'),
        ('core:contact_us', '/contact-us/'),
        ('core:terms_and_condition', '/terms-and-condition/'),
        ('core:privacy_policy', '/privacy-policy/'),
        ('blog:post_list', '/blog/'),
    )

    def test_public_routes_resolve(self):
        for name, expected_path in self.public_pages:
            with self.subTest(name=name):
                self.assertEqual(reverse(name), expected_path)
