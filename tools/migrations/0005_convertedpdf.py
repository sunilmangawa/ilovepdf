# Generated by Django 5.0.1 on 2024-02-24 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0004_toolattachment_function_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConvertedPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf_file', models.FileField(upload_to='pdfs/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
