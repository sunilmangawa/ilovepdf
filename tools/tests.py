from django.test import SimpleTestCase
from django.urls import reverse


class ToolRoutesTests(SimpleTestCase):
    """Keep main tool links and embedded URLs in sync."""

    tool_pages = (
        ('merge_pdf', '/tools/merge-pdf/'),
        ('split_pdf', '/tools/split-pdf/'),
        ('compress_pdf', '/tools/compress-pdf/'),
        ('rotate_pdf', '/tools/rotate-pdf/'),
        ('image_to_pdf', '/tools/jpg-to-pdf/'),
        ('pdf_to_word', '/tools/pdf-to-word/'),
        ('crop_pdf', '/tools/crop-pdf/'),
        ('edit_pdf', '/tools/edit-pdf/'),
        ('forms_pdf', '/tools/pdf-forms/'),
        ('organize_pdf', '/tools/organize-pdf/'),
        ('scan_pdf', '/tools/scan-pdf/'),
    )

    def test_tool_routes_resolve(self):
        for name, expected_path in self.tool_pages:
            with self.subTest(name=name):
                self.assertEqual(reverse(f'tools:{name}'), expected_path)

    def test_embedded_tool_routes_resolve(self):
        for name, expected_path in (
            ('merge_pdf_include', '/tools/merge-pdf-files/'),
            ('edit_pdf_include', '/tools/edit-pdf-file/'),
            ('forms_pdf_include', '/tools/pdf-forms/file/'),
            ('scan_pdf_include', '/tools/scan-pdf-file/'),
        ):
            with self.subTest(name=name):
                self.assertEqual(reverse(f'tools:{name}'), expected_path)
