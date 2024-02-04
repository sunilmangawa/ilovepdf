from django.contrib import admin
from .models import Category, Post, Comment
from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm
from parler.utils.context import switch_language

# Register your models here.
class PostAdmin(TranslatableAdmin):
    list_display = ('title', 'slug', 'toolattachment', 'publish', 'status')
    list_filter = ('status', 'created', 'publish', 'author')
    search_fields = ('translations__title', 'translations__slug', 'translations__intro', 'translations__keywords', 'translations__body',)
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ('status', 'publish')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'toolattachment', 'intro', 'keywords', 'tags', 'image', 'body','publish', 'status'),
        }),
    )

    def get_prepopulated_fields(self, request, obj=None):
        return {
            'slug': ('title',)
        }

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        with switch_language(obj, 'en'):
            for field in ['title', 'slug', 'author', 'toolattachment', 'intro', 'keywords', 'tags', 'image', 'body','publish', 'status']:
                form.base_fields[field].widget.attrs['value'] = getattr(obj, field) #not getting value from TextField
        return form


admin.site.register(Category)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment)