def word_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('word_file'):
            word_file = request.FILES['word_file']

            # Generate a unique temporary file name (optional)
            import uuid 
            temp_filename = f"{uuid.uuid4()}.docx"
            temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename)

            # Save the uploaded Word file to the media directory
            with open(temp_file_path, 'wb') as temp_file:
                for chunk in word_file.chunks():
                    temp_file.write(chunk)

            # Generate the output PDF file name (with renaming)
            output_file_name = word_file.name.replace(' ', '_').replace('.docx', '.pdf').replace('.doc', '.pdf').replace('.txt', '.pdf')
            output_pdf_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', output_file_name)

            # Initialize error message
            error_message = None

            # Convert the Word file to PDF
            convert_word_to_pdf(temp_file_path, os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', output_file_name))


            # Serve the PDF file for download if it was created successfully
            with open(output_pdf_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={output_file_name}'
                return response
        else:
            return view_func(request, *args, **kwargs)  
    return wrapper_function    
















import os
import subprocess

def convert_to_pdf(input_file_path, output_file_path):
    try:
        # Convert using LibreOffice
        subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', input_file_path, '--outdir', os.path.dirname(output_file_path)])
        return True
    except Exception as e:
        print(f"Conversion Error: {e}")
        return False


import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage

def word_to_pdf_view_logic(request):
    if request.method == "POST" and request.FILES.get('word_file'):
        word_file = request.FILES['word_file']

        # Generate unique temporary file name
        temp_filename = f"{uuid.uuid4()}.docx"
        temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename)

        # Save uploaded Word file to temporary location
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'word_to_pdf'))
        temp_file = fs.save(temp_filename, word_file)

        # Generate output PDF file name
        output_file_name = os.path.splitext(word_file.name)[0] + '.pdf'
        output_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', output_file_name)

        # Convert Word file to PDF
        if convert_to_pdf(temp_file_path, output_file_path):
            # Serve the PDF file for download
            with open(output_file_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={output_file_name}'
                return response
        else:
            return HttpResponse("Error converting file to PDF")

    return render(request, 'tools/word_to_pdf.html')
