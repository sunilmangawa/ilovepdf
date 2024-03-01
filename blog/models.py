from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from taggit.managers import TaggableManager
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
# from meta.models import ModelMeta
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields, TranslatableManager  #TranslatableQuerySet
from parler.managers import TranslatableQuerySet
from tools.models import ToolAttachment
from meta.models import ModelMeta
# from parler.views.LanguageChoiceMixin import get_current_language


class Category(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True, default=None)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

# 100 
# def validate_comma_separated_words(value):
#     words = value.split(',')
#     for word in words:
#         word = word.strip()
#         if not word:
#             raise ValidationError('Enter at least one keyword.')
# Create your models here.
def validate_comma_separated_words(value):
    words = [word.strip() for word in value.split(',') if word.strip()]
    if not words:
        raise ValidationError('Enter at least one keyword.')    

def image_upload_path(instance, filename):
    """Renames uploaded image with the instance's slug."""
    return f"blog/images/{instance.slug}.{filename.split('.')[-1]}"


class PublishedManager(TranslatableQuerySet):
# class PublishedManager(models.Manager,TranslatableQuerySet):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED).select_related('translations')

class Post(ModelMeta,TranslatableModel):

    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'
    
    toolattachment = models.ForeignKey(ToolAttachment, on_delete=models.SET_NULL, null=True, blank=True, help_text="Select a tool's function to display in post_details.html")

    category = models.ForeignKey(Category, related_name= _('category'), on_delete=models.SET_NULL, null=True)

    translations = TranslatedFields(
        title=models.CharField(_('title'), max_length=60),
        slug=models.SlugField(_('slug'), max_length=250),#, unique_for_date='publish'
        intro=models.TextField(_('intro'), blank=False, max_length=160),
        keywords=models.TextField(_('keywords')),
        body=RichTextField(_('body'), config_name='awesome_ckeditor'),
    )

    image = models.ImageField(upload_to=image_upload_path, blank=True, null=True)
    author = models.ForeignKey(User,on_delete=models.CASCADE,related_name='blog_posts')
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2,choices=Status.choices,default=Status.DRAFT)

    objects = PublishedManager()
    published = TranslatableManager() # Our custom manager.

    tags = TaggableManager()

    class Meta:
        # ordering = self.objects.translated('en').order_by('translations__publish') # self not working
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]
        verbose_name = "post"
        verbose_name_plural = "posts"


    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', args=[self.slug])#,self.publish.year,self.publish.month,self.publish.day

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    _metadata = {
        'title': 'get_meta_title',
        'description': 'get_meta_description',
        'image': 'get_meta_image',
        'keywords': 'get_meta_keywords',

    }
    def get_meta_title(self):
        lang_code = self.get_current_language() 
        try:
            return self.safe_translation_getter('title', language_code=lang_code)
        except AttributeError:
            return None  

    def get_meta_description(self):
        lang_code = self.get_current_language()
        try:
            return self.safe_translation_getter('intro', language_code=lang_code) 
        except AttributeError:
            return None 

            
    def get_meta_keywords(self):
        lang_code = self.get_current_language()
        try:
            keywords = self.safe_translation_getter('keywords', language_code=lang_code)
            clean_keywords = set(keywords.split(','))  # Remove duplicates, join into string
            return clean_keywords
        except AttributeError:
            return None 


    def get_meta_image(self):
        if self.image:
            return self.image.url

    # _schema = {
    #     'name': 'title',
    #     'keywords': 'get_keywords',
    #     'description': 'get_description',
    #     'image': 'get_meta_image',
        # 'articleBody': 'body',
        # 'articleSection': 'get_categories',
        # 'author': 'get_schema_author',
        # 'copyrightYear': 'copyright_year',
        # 'dateCreated': 'get_date',
        # 'dateModified': 'get_date',
        # 'datePublished': 'date_published',
        # 'headline': 'headline',
        # 'url': 'get_full_url',
        # 'mainEntityOfPage': 'get_full_url',
        # 'publisher': 'get_site',
    # }


class Comment(models.Model):
    post = models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created']
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return f'Comment by {self.name} on {self.post}'

