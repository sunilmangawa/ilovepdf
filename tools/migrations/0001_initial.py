# Generated by Django 5.0.1 on 2024-01-28 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ToolAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_name', models.CharField(help_text="Template path for the tool's function", max_length=100)),
            ],
            options={
                'verbose_name': 'tool',
                'verbose_name_plural': 'tools',
            },
        ),
    ]
