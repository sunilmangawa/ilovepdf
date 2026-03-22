from django.contrib import admin
from .models import ToolAttachment
from parler.admin import TranslatableAdmin
# from .forms import ToolAttachmentForm

# Register your models here.

admin.site.register(ToolAttachment)
# admin.site.register(ToolAttachment, TranslatableAdmin)

# @admin.register(ToolAttachment) 
# class ToolAttachmentAdmin(admin.ModelAdmin):
#     form = ToolAttachmentForm