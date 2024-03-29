# Generated by Django 5.0.1 on 2024-02-02 17:10

import django.db.models.deletion
import parler.fields
import parler.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0002_toolattachment_function_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='toolattachment',
            name='function_name',
        ),
        migrations.RemoveField(
            model_name='toolattachment',
            name='template_name',
        ),
        migrations.CreateModel(
            name='ToolAttachmentTranslation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language_code', models.CharField(db_index=True, max_length=15, verbose_name='Language')),
                ('function_name', models.CharField(help_text="Unique identifier for the tool's function", max_length=50, unique=True, verbose_name='function_name')),
                ('template_name', models.CharField(help_text="Template path for the tool's function", max_length=100, verbose_name='template_name')),
                ('master', parler.fields.TranslationsForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translation', to='tools.toolattachment')),
            ],
            options={
                'verbose_name': 'tool Translation',
                'db_table': 'tools_toolattachment_translation',
                'db_tablespace': '',
                'managed': True,
                'default_permissions': (),
                'unique_together': {('language_code', 'master')},
            },
            bases=(parler.models.TranslatableModel, models.Model),
        ),
    ]
