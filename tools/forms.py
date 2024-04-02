from django import forms
from django.forms.widgets import ClearableFileInput


class PDFUploadForm(forms.Form):
    pdf_files = forms.FileField(
        label='Upload PDF Files',
        widget=forms.ClearableFileInput()
        # widget=forms.FileInput(attrs={'multiple': True})  # Use FileInput instead
    )

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a PDF file')

class RotatePDFForm(forms.Form):
    file = forms.FileField(label='Select PDF file')
    rotation_choices = [
        ('90', 'Rotate 90 degrees clockwise'),
        ('180', 'Rotate 180 degrees'),
        ('270', 'Rotate 90 degrees anticlockwise')
    ]
    rotation_angle = forms.ChoiceField(choices=rotation_choices, label='Rotation Angle')
    page_range = forms.CharField(max_length=100, required=False, label='Page Range (optional)')
