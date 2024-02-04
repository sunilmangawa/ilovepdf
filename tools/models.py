from django.db import models
from parler.models import TranslatableModel, TranslatedFields
from django.utils.translation import gettext_lazy as _

# Create your models here.
class ToolAttachment(models.Model):
    function_name = models.CharField(max_length=50, unique=True, blank=True, null=True, default=None, help_text="Unique identifier for the tool's function")
    template_name = models.CharField(max_length=100, blank=True, null=True, default=None, help_text="Template path for the tool's function")

# class ToolAttachment(TranslatableModel):    
#     translation = TranslatedFields(
#         function_name = models.CharField(_('function_name'), max_length=50, unique=True, help_text="Unique identifier for the tool's function"),
#         template_name = models.CharField( _('template_name'), max_length=100, help_text="Template path for the tool's function")
#     )


    class Meta:
        verbose_name = 'tool'
        verbose_name_plural = 'tools'

    def __str__(self):
        return self.function_name