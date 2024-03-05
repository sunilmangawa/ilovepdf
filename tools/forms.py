from django import forms
from django.forms.widgets import ClearableFileInput

# class CustomClearableFileInput(ClearableFileInput):
#     def is_multipart(self):
#         return True

class PDFUploadForm(forms.Form):
    pdf_files = forms.FileField(
        label='Upload PDF Files',
        widget=forms.ClearableFileInput()
        # widget=forms.FileInput(attrs={'multiple': True})  # Use FileInput instead


    )

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a PDF file')

# class PDFUploadMergeForm(forms.Form):
#     # pdf_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
#     pdf_files = forms.FileField(widget=CustomClearableFileInput(attrs={'multiple': True}))
