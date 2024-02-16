# converter/views.py
from django.shortcuts import render, redirect
from pdf2docx import Converter
from .models import ToolAttachment

from django.http import HttpResponse, JsonResponse, FileResponse
from blog.models import Post
# from blog.views import BlogDetailView
from django.views import View
from django.template import TemplateDoesNotExist
from .topdf.word_to_pdf_converter import convert_word_to_pdf, clean_temp_files
from .pdfto.pdf_to_docx_converter import pdf_to_docx_converter
# from .tools.word_counter import word_counter_text
from .extra.lorem_ipsum_generator import generate_lorem_ipsum
from .pdfto.pdf_to_jpg_converter import convert_pdf_to_jpg, clean_up_jpg_files, create_zip_archive
from .pdfto.pdf_to_ppt_pptx_converter import convert_pdf_to_ppt_pptx, create_ppt_slide, clean_up_temp_files, create_zip_archives
from .topdf.excel_to_pdf_converter import convert_excel_to_pdf
from io import BytesIO
import os
import subprocess

import zipfile
from zipfile import ZipFile
from django.core.signals import request_finished
from django.dispatch import receiver
# from tools.utils import clean_up_temp_files, create_zip_archive
import docxtopdf
import tempfile
from django.conf import settings


# Create your views here.
def merge_pdf_View(request):
    context = {
    }
    return render(request, template_name='tools/merge_pdf.html')

def split_pdf_View(request):
    context = {
    }
    return render(request, template_name='tools/split_pdf.html')

def compress_pdf_View(request):
    context = {
    }
    return render(request, template_name='tools/compress_pdf.html')



# 100% Working for static url with post detail
def pdf_to_docx_converter_View(request):
    if request.method == 'POST' and 'pdf_file' in request.FILES:
        pdf_file = request.FILES['pdf_file']
        try:
            # Save the uploaded PDF file
            with open('uploaded_pdf.pdf', 'wb') as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)
            # Define paths for converted files
            output_docx_path = 'converted_doc.docx'
            # Call the pdf_to_docx_converter function
            # success, error_message = pdf_to_docx_converter('uploaded_pdf.pdf', 'converted_doc.docx')
            success, error_message = pdf_to_docx_converter('uploaded_pdf.pdf', output_docx_path)
            if success:
                with open(output_docx_path, 'rb') as docx_file:
                    response = HttpResponse(docx_file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    response['Content-Disposition'] = 'attachment; filename="converted_doc.docx"'
                    return response
            else:
                return HttpResponse(f"Conversion failed. Error: {error_message}")
        except Exception as e:
            return HttpResponse(f"Conversion failed. Error: {str(e)}")
    return render(request, 'tools/pdf_to_docx_converter.html')


# def word_counter_text_view(request):
#     word_count = 0

#     if request.method == 'POST':
#         text = request.POST.get('text', '')  # Assuming the text input field has the name 'text'
#         word_count = word_counter_text(text)
#     # return render(request, 'converter/word_counter_text.html', {'word_count': word_count}) #working but redirect
#     return JsonResponse({'word_count': word_count})


def lorem_ipsum_generator(request):
    lorem_ipsum_text = ""

    if request.method == 'POST':
        paragraphs = int(request.POST.get('paragraphs', 3))
        lorem_ipsum_text = generate_lorem_ipsum(paragraphs)

    return render(request, 'lorem_ipsum_generator.html', {'lorem_ipsum_text': lorem_ipsum_text})


# def convert_pdf_to_jpg_view(request):
#     if request.method == 'POST':
#         pdf_file = request.FILES.get('pdf_file')

#         if pdf_file:
#             # Define your desired output folder
#             output_folder = "media/pdf_to_jpg/"

#             # Convert PDF to JPG
#             jpg_paths = convert_pdf_to_jpg(pdf_file.temporary_file_path(), output_folder)

#             # Create a zip file containing all JPG images
#             zip_file_path = os.path.join(output_folder, "output_images.zip")
#             create_zip_archive(jpg_paths, zip_file_path)

#             # Clean up temporary JPG files
#             clean_up_jpg_files(jpg_paths)

#             # Serve the zip file for download
#             with open(zip_file_path, 'rb') as zip_file:
#                 response = HttpResponse(zip_file.read(), content_type='application/zip')
#                 response['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_file_path)}'
#                 return response

#     return render(request, 'tools:convert_pdf_to_jpg.html')

def convert_pdf_to_jpg_view(request):
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')

        if pdf_file:
            # Define your desired output folder
            output_folder = "media/pdf_to_jpg/"

            # Read the content of the uploaded PDF file
            pdf_content = pdf_file.read()

            # Convert PDF to JPG
            jpg_paths = convert_pdf_to_jpg(BytesIO(pdf_content), output_folder)

            # Create a zip file containing all JPG images
            zip_file_path = os.path.join(output_folder, "output_images.zip")
            create_zip_archive(jpg_paths, zip_file_path)

            # Clean up temporary JPG files
            clean_up_jpg_files(jpg_paths)

            # Serve the zip file for download
            with open(zip_file_path, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_file_path)}'
                return response

    return render(request, 'convert_pdf_to_jpg.html')


def convert_pdf_to_ppt_pptx_view(request):
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        output_folder = "media/pdf_to_ppt_pptx/"

        # Read the content of the uploaded PDF file
        pdf_content = pdf_file.read()

        # Convert PDF to PPT/PPTX
        ppt_paths = convert_pdf_to_ppt_pptx(BytesIO(pdf_content), output_folder)

        # Create a zip file containing all PowerPoint files
        zip_file_path = os.path.join(output_folder, "output_slides.zip")
        create_zip_archives(ppt_paths, zip_file_path)

        # Clean up temporary PowerPoint files
        clean_up_temp_files(ppt_paths)

        # Use FileResponse directly without manually opening the file
        response = FileResponse(open(zip_file_path, 'rb'))
        response['Content-Disposition'] = 'attachment; filename="output_slides.zip"'
        return response

    return render(request, 'tools/pdf_to_ppt_pptx.html')



def jpg_to_pdf_View(request):
    return render(request, template_name='tools/jpg_to_pdf.html')




def word_to_pdf_View(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', file.name)
        with open(temp_file_path, 'wb') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
        output_pdf_path = temp_file_path.replace('.docx', '.pdf') or temp_file_path.replace('.doc', '.pdf') or temp_file_path.replace('.txt', '.pdf')
        convert_word_to_pdf(temp_file_path, output_pdf_path)
        print(f"Temp file path : {temp_file_path} \n Output File path : {output_pdf_path}")
        clean_temp_files(temp_file_path)

        with open(output_pdf_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_pdf_path)}'
            return response
    return render(request, 'tools/word_to_pdf.html')

# def word_to_pdf_View(request):
#     if request.method == 'POST' and request.FILES.get('file'):
#         file = request.FILES['file']
#         temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', file.name)
#         with open(temp_file_path, 'wb') as temp_file:
#             for chunk in file.chunks():
#                 temp_file.write(chunk)
#         output_pdf_path = temp_file_path.replace('.docx', '.pdf').replace('.doc', '.pdf').replace('.txt', '.pdf')
#         convert_word_to_pdf(temp_file_path, output_pdf_path)
#         clean_temp_files(temp_file_path)

#         # Redirect to another page for download
#         # return redirect('/tools/download', file_name=os.path.basename(output_pdf_path))

#         # # Get the base name of the output PDF file
#         # file_name = os.path.basename(output_pdf_path)
#         # # Redirect to the download page with the file_name parameter
#         # return redirect('download', file_name=file_name)

#         file_name = os.path.basename(output_pdf_path)

#         # Redirect using the filename from the context
#         return redirect('download_page', file_name=file_name)
#     return render(request, 'tools/word_to_pdf.html')

#         # Pass file_name as context to word_to_pdf.html
#     # file_name = request.POST.get('file_name')  # Get the file_name from the form
#     # return render(request, 'tools/word_to_pdf.html', {'file_name': file_name})

# def download_page(request, file_name):
#     return render(request, 'tools/download.html', {'file_name': file_name})

# tools/views.py
# def download_page(request, file_name):
#     file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', file_name)
#     with open(file_path, 'rb') as f:
#         response = HttpResponse(f.read(), content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{file_name}"'
#         return response


def powerpoint_to_pdf_View(request):
    return render(request, template_name='tools/powerpoint_to_pdf.html')

# def excel_to_pdf_View(request):
#     return render(request, template_name='tools/excel_to_pdf.html')

# def excel_to_pdf_View(request):
#     if request.method == 'POST' and request.FILES.get('file'):
#         input_file = request.FILES['file']
#         output_file = f'media/excel_to_pdf/{input_file.name.replace(".xlsx", ".pdf")}'
#         convert_excel_to_pdf(input_file, output_file)
#         with open(output_file, 'rb') as f:
#             response = HttpResponse(f.read(), content_type='application/pdf')
#             response['Content-Disposition'] = f'attachment; filename="{input_file.name.replace(".xlsx", ".pdf")}"'
#             return response
#     return render(request, 'tools/excel_to_pdf.html')

# def excel_to_pdf_View(request):
#     if request.method == 'POST' and request.FILES.get('file'):
#         input_file = request.FILES['file']
#         output_file = os.path.join(settings.MEDIA_ROOT, 'excel_to_pdf', input_file.name.replace(".xlsx", ".pdf"))

#         # Save the uploaded file to a temporary location
#         with open(output_file, 'wb') as destination:
#             for chunk in input_file.chunks():
#                 destination.write(chunk)

#         # Convert the saved file to PDF
#         convert_excel_to_pdf(output_file, output_file)

#         # Serve the PDF file as a response
#         with open(output_file, 'rb') as f:
#             response = HttpResponse(f.read(), content_type='application/pdf')
#             response['Content-Disposition'] = f'attachment; filename="{input_file.name.replace(".xlsx", ".pdf")}"'
#             return response

#     return render(request, 'tools/excel_to_pdf.html')

# def excel_to_pdf_View(request):
#     if request.method == 'POST' and request.FILES.get('file'):
#         input_file = request.FILES['file']
#         output_file_path = os.path.join(settings.MEDIA_ROOT, 'excel_to_pdf')
#         os.makedirs(output_file_path, exist_ok=True)  # Ensure output directory exists

#         input_file_path = os.path.join(output_file_path, input_file.name)
#         output_file_name = input_file.name.replace(".xlsx", ".pdf")
#         output_file_path = os.path.join(output_file_path, output_file_name)

#         # Save the uploaded file to a temporary location
#         with open(input_file_path, 'wb') as destination:
#             for chunk in input_file.chunks():
#                 destination.write(chunk)

#         # Convert the saved file to PDF
#         convert_excel_to_pdf(input_file_path, output_file_path)

#         # Check if the PDF file was generated successfully
#         if os.path.exists(output_file_path):
#             # Serve the PDF file as a response
#             with open(output_file_path, 'rb') as f:
#                 response = HttpResponse(f.read(), content_type='application/pdf')
#                 response['Content-Disposition'] = f'attachment; filename="{output_file_name}"'
#                 return response
#         else:
#             return HttpResponse("Error occurred during conversion. Please try again.")

#     return render(request, 'tools/excel_to_pdf.html')

# def excel_to_pdf_View(request):
#     if request.method == 'POST' and request.FILES['excel_file']:
#         excel_file = request.FILES['excel_file']
#         pdf_path = convert_excel_to_pdf(excel_file)
#         with open(pdf_path, 'rb') as f:
#             response = HttpResponse(f.read(), content_type='application/pdf')
#             response['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
#             return response
#     return render(request, 'tools/excel_to_pdf.html')

from openpyxl import load_workbook
# from xtopdf import PDFWriter
from pypdf import PdfWriter

def excel_to_pdf_View(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        print("excel_file: ", excel_file)
        print("excel_file Type: ", type(excel_file))
        workbook = load_workbook(excel_file, data_only=True)
        worksheet = workbook.active

        pw = PdfWriter('converted_pdf.pdf')
        pw.setFont('Courier', 12)
        pw.setHeader('Excel to PDF Converter - Converted from XLSX data')
        pw.setFooter('Generated using openpyxl and xtopdf')

        ws_range = worksheet.iter_rows(values_only=True)
        for row in ws_range:
            s = ''
            for cell in row:
                if cell is None:
                    s += ' ' * 11
                else:
                    s += str(cell).rjust(10) + ' '
            pw.writeLine(s)
        
        pw.savePage()
        pw.close()

        # Serve the PDF for download
        with open('converted_pdf.pdf', 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="converted_pdf.pdf"'
            return response
    
    return render(request, 'tools/excel_to_pdf.html')


def html_to_pdf_View(request):
    return render(request, template_name='tools/html_to_pdf.html')



# def pdf_to_jpg_View(request):
#     return render(request, template_name='tools/pdf_to_jpg.html')

def pdf_to_jpg_View(request):
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')

        if pdf_file:
            # Define your desired output folder
            output_folder = "media/pdf_to_jpg/"

            # Read the content of the uploaded PDF file
            pdf_content = pdf_file.read()

            # Convert PDF to JPG
            jpg_paths = convert_pdf_to_jpg(BytesIO(pdf_content), output_folder)

            # Create a zip file containing all JPG images
            zip_file_path = os.path.join(output_folder, "output_images.zip")
            create_zip_archive(jpg_paths, zip_file_path)

            # Clean up temporary JPG files
            clean_up_jpg_files(jpg_paths)

            # Serve the zip file for download
            with open(zip_file_path, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_file_path)}'
                return response

    return render(request, 'tools/pdf_to_jpg.html')




# def pdf_to_word_View(request):
#     return render(request, template_name='tools/pdf_to_word.html')

def pdf_to_word_View(request):
    if request.method == 'POST' and 'pdf_file' in request.FILES:
        pdf_file = request.FILES['pdf_file']
        try:
            # Save the uploaded PDF file
            with open('uploaded_pdf.pdf', 'wb') as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)
            # Define paths for converted files
            output_docx_path = 'converted_doc.docx'
            # Call the pdf_to_docx_converter function
            # success, error_message = pdf_to_docx_converter('uploaded_pdf.pdf', 'converted_doc.docx')
            success, error_message = pdf_to_docx_converter('uploaded_pdf.pdf', output_docx_path)
            if success:
                with open(output_docx_path, 'rb') as docx_file:
                    response = HttpResponse(docx_file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    response['Content-Disposition'] = 'attachment; filename="converted_doc.docx"'
                    return response
            else:
                return HttpResponse(f"Conversion failed. Error: {error_message}")
        except Exception as e:
            return HttpResponse(f"Conversion failed. Error: {str(e)}")
    return render(request, 'tools/pdf_to_word.html')


def pdf_to_powerpoint_View(request):
    return render(request, template_name='tools/pdf_to_powerpoint.html')

def pdf_to_excel_View(request):
    return render(request, template_name='tools/pdf_to_excel.html')

def pdf_to_html_View(request):
    return render(request, template_name='tools/pdf_to_html.html')

