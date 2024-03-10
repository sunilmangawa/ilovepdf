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
