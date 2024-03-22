from celery import shared_task
import os
import time
from django.conf import settings
from django.utils import timezone
from celer import app 
import shutil

@app.task  
def delete_old_pdfs():
    folders = [
        os.path.join(settings.MEDIA_ROOT, 'excel_to_pdf'), 
        os.path.join(settings.MEDIA_ROOT, 'images'), 
        os.path.join(settings.MEDIA_ROOT, 'pdf_to_jpg'), 
        os.path.join(settings.MEDIA_ROOT, 'pdf_to_ppt_pptx'), 
        os.path.join(settings.MEDIA_ROOT, 'word_to_pdf'), 
        settings.BASE_DIR,  # Assuming your root directory '/' is accessible 
        settings.MEDIA_ROOT
    ]
    extensions = ['.pdf', '.docx', '.doc', '.jpg', '.identifier']
    expiration_threshold = timezone.now() - timezone.timedelta(hours=1)  # More flexible
    expiration_time = 600

    for folder in folders:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.splitext(filename)[1].lower() in extensions:
                creation_time = os.path.getctime(file_path)
                # if timezone.datetime.fromtimestamp(creation_time) < expiration_threshold:
                if (time.time() - creation_time) > expiration_time:
                    os.remove(file_path)
                    print(f"Deleted expired file: {file_path}")


    for root, dirs, files in os.walk('.'):  # Search recursively 
        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                print(f"Deleted .pyc file: {file_path}")


# @app.task  
# def delete_expired_files():
#     # ... (your existing code) ... 

#     for root, dirs, files in os.walk('.'):  # Search recursively 
#         for file in files:
#             if file.endswith('.pyc'):
#                 file_path = os.path.join(root, file)
#                 os.remove(file_path)
#                 print(f"Deleted .pyc file: {file_path}")



# # tools/tasks.py
# from celery import shared_task
# import os
# import time
# from django.conf import settings
# from django.utils import timezone
# from celer import app  # Import the Celery app instance

# @app.task
# # @shared_task
# def delete_old_pdfs():
#     pdf_folder = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')
#     expiration_time = 60  # 1 hour in seconds

#     for filename in os.listdir(pdf_folder):
#         if filename.endswith('.pdf'):
#             file_path = os.path.join(pdf_folder, filename)
#             creation_time = os.path.getctime(file_path)

#             if (time.time() - creation_time) > expiration_time:
#                 os.remove(file_path)


# @app.task
# # @shared_task
# def delete_root_pdfs():
#     pdf_folder = os.path.join(settings.MEDIA_ROOT, '/')
#     expiration_time = 60  # 1 hour in seconds

#     for filename in os.listdir(pdf_folder):
#         if filename.endswith('.pdf'):
#             file_path = os.path.join(pdf_folder, filename)
#             creation_time = os.path.getctime(file_path)

#             if (time.time() - creation_time) > expiration_time:
#                 os.remove(file_path)





# @app.task  # Use @app.task instead of @shared_task
# @shared_task
# def delete_old_pdfs():
#     pdf_folder = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')
#     expiration_threshold = timezone.now() - timezone.timedelta(minutes=1)  # More flexible threshold

#     for filename in os.listdir(pdf_folder):
#         if filename.endswith('.pdf'):
#             file_path = os.path.join(pdf_folder, filename)
#             creation_time = os.path.getctime(file_path)

#             if timezone.datetime.fromtimestamp(creation_time) < expiration_threshold:
#                 os.remove(file_path)
#                 print(f"Deleted expired PDF: {file_path}")  
