from __future__ import annotations
from django import forms
from django.forms.widgets import ClearableFileInput
from ckeditor.widgets import CKEditorWidget
# for HTML to PDF conversion, you can create a form like this:


from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# from tools.models import ToolAttachment

# class ToolAttachmentForm(forms.ModelForm):
#     description = forms.CharField(widget=CKEditorWidget()) 
    
#     class Meta: 
#         model = ToolAttachment 
#         fields = "__all__"


# from django.core.exceptions import ValidationError

# def validate_file_type(value):
#     """
#     Validates that the uploaded file is a PDF.
#     """
#     allowed_types = ['application/pdf']
#     if value.content_type not in allowed_types:
#         raise ValidationError('Only PDF files are allowed.')

# class PDFUploadForm(forms.Form):
#     pdf_files = forms.FileField(
#         label='Upload PDF Files',
#         widget=forms.ClearableFileInput()
#         # widget=forms.FileInput(attrs={'multiple': True})  # Use FileInput instead
#     )

class PDFUploadForm(forms.Form):
    pdf_file = forms.FileField()

class UploadFileForm(forms.Form):
    file = forms.FileField(
        label='Select a PDF file',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        # validators=[validate_file_type]  # Server-side validation
        )



ROTATION_CHOICES = [
    (0, '0 Degrees'),
    (90, '90 Degrees (Clockwise)'),
    (180, '180 Degrees'),
    (270, '270 Degrees (Counter-clockwise)'),
]

class RotatePDFForm(forms.Form):
    pdf_file = forms.FileField(
        label='Select PDF to Rotate',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    rotation_angle = forms.ChoiceField(
        choices=ROTATION_CHOICES,
        label='Rotation Angle',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    pages = forms.CharField(
        required=False,
        label='Pages to Rotate (e.g., 1,2,3 or 1-3)',
        help_text='Leave blank to rotate all pages',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

# class RotatePDFForm(forms.Form):
#     pdf_file = forms.FileField(label='Select PDF to Rotate')
#     rotation_angle = forms.ChoiceField(choices=ROTATION_CHOICES, label='Rotation Angle')
#     pages = forms.CharField(
#         required=False,
#         label='Pages to Rotate (e.g., 1,2,3 or 1-3)',
#         help_text='Leave blank to rotate all pages'
#     )

# for HTML to PDF conversion, you can create a form like this:



class HtmlToPdfForm(forms.Form):
    url = forms.URLField(
        required=False,
        label=_("Web page URL"),
        widget=forms.URLInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "https://example.com/page",
                "autocomplete": "url",
                "inputmode": "url",
            }
        ),
    )
    html_file = forms.FileField(
        required=False,
        label=_("HTML file"),
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control form-control-lg",
                "accept": ".html,.htm,text/html",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        url = (cleaned.get("url") or "").strip()
        html_file = cleaned.get("html_file")

        if bool(url) == bool(html_file):
            raise ValidationError(_("Provide either a web page URL or one HTML file, not both."))

        if url:
            scheme = url.split(":", 1)[0].lower()
            if scheme not in settings.HTML_TO_PDF_ALLOWED_SCHEMES:
                self.add_error("url", _("Only HTTP and HTTPS URLs are supported."))

        if html_file:
            name = html_file.name.lower()
            if not name.endswith((".html", ".htm")):
                self.add_error("html_file", _("Upload an HTML file ending in .html or .htm."))
            if html_file.size > settings.HTML_TO_PDF_MAX_UPLOAD_BYTES:
                self.add_error(
                    "html_file",
                    _("The HTML file is too large. Maximum size is %(size)s MB.")
                    % {"size": settings.HTML_TO_PDF_MAX_UPLOAD_BYTES // (1024 * 1024)},
                )

        return cleaned