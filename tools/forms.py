from django import forms
from django.forms.widgets import ClearableFileInput
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

