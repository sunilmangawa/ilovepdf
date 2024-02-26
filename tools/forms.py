from django import forms

class PDFUploadForm(forms.Form):
    pdf_files = forms.FileField(
        label='Upload PDF Files',
        widget=forms.ClearableFileInput()
        # widget=forms.FileInput(attrs={'multiple': True})  # Use FileInput instead


    )

