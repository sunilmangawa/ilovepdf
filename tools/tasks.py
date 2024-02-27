# tools/tasks.py
from celery import shared_task
import os
import time
from django.conf import settings

@shared_task
def delete_old_pdfs():
    pdf_folder = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')
    expiration_time = 60  # 1 hour in seconds

    for filename in os.listdir(pdf_folder):
        if filename.endswith('.pdf'):
            file_path = os.path.join(pdf_folder, filename)
            creation_time = os.path.getctime(file_path)

            if (time.time() - creation_time) > expiration_time:
                os.remove(file_path)
