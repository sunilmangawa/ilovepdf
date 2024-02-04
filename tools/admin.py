from django.contrib import admin
from .models import ToolAttachment
from parler.admin import TranslatableAdmin


# Register your models here.

admin.site.register(ToolAttachment)
# admin.site.register(ToolAttachment, TranslatableAdmin)