from django.db import models
from parler.models import TranslatableModel, TranslatedFields
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField

# Create your models here.
class ToolAttachment(models.Model):
    function_name = models.CharField(max_length=50, unique=True, blank=True, null=True, default=None, help_text="Unique identifier for the tool's function")
    template_name = models.CharField(max_length=100, blank=True, null=True, default=None, help_text="Template path for the tool's function")
    body=RichTextField(blank=True, null=True, default=None, config_name='awesome_ckeditor')


    class Meta:
        verbose_name = 'tool'
        verbose_name_plural = 'tools'

    def __str__(self):
        return self.function_name


class ConvertedPDF(models.Model):
    pdf_file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

