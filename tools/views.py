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
from django.utils.text import slugify
from .extra.merge_pdf import merge_pdfs

from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from .forms import PDFUploadForm
import tempfile
from django.core.files.base import File

# tools/views.py

from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import ConvertedPDF
from .topdf.imgtopdf import convert_to_pdf

import img2pdf

from openpyxl import load_workbook
from pypdf import PdfWriter
import pdfkit
import requests
from meta.views import Meta


def merge_pdf_view(request):
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

    meta = Meta(
        title='iLovePdfConverterOnline - PDF to JPG| JPEG Image',
        description='Convert PDF in to JPG| JPEG Image file. PDF will be converted to Image.',
        keywords=['png', 'image', 'jpg', 'jpeg'],
        og_title='iLovePdfConverterOnline - PDF to JPG| JPEG Image',
        og_description='Convert PDF in to JPG| JPEG Image file. PDF will be converted to Image.',

    )

    context = {'meta': meta}

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

    meta = Meta(
        title='iLovePdfConverterOnline - PDF to JPG| JPEG Image',
        description='Convert PDF in to JPG| JPEG Image file. PDF will be converted to Image.',
        keywords=['png', 'image', 'jpg', 'jpeg'],
        og_title='iLovePdfConverterOnline - PDF to JPG| JPEG Image',
        og_description='Convert PDF in to JPG| JPEG Image file. PDF will be converted to Image.',

    )

    context = {'meta': meta}


    return render(request, 'tools/pdf_to_ppt_pptx.html')



def jpg_to_pdf_View(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        image_files = request.FILES.getlist('images')

        # Temporary directory to store uploaded images
        # temp_directory = '/media/temporary/'
        temp_directory = os.path.join(settings.MEDIA_ROOT, 'temporary')  # Use project-specific directory
        os.makedirs(temp_directory, exist_ok=True)
        
        # Save uploaded images to the temporary directory
        image_paths = []
        for img_file in image_files:
            image_path = os.path.join(temp_directory, img_file.name)
            with open(image_path, 'wb') as f:
                for chunk in img_file.chunks():
                    f.write(chunk)
            image_paths.append(image_path)

        # Convert images to PDF
        pdf_data = img2pdf.convert(image_paths)

        # Create an HTTP response with PDF content to force download
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="output.pdf"'
        
        # Clean up: remove temporary image files and directory
        for image_path in image_paths:
            os.remove(image_path)
        os.rmdir(temp_directory)

        return response
    meta = Meta(
        title='iLovePdfConverterOnline - JPG/JPEG Image to PDF',
        description='Convert JPG/JPEG Image file in to PDF. Image will be converted to PDF.',
        keywords=['png', 'image', 'jpg', 'jpeg'],
        og_title='iLovePdfConverterOnline - JPG/JPEG Image to PDF',
        og_description='Convert JPG/JPEG Image file in to PDF. Image will be converted to PDF',

    )

    context = {'meta': meta}


    return render(request, 'tools/jpg_to_pdf.html')



#100% working for image to pdf
def img_to_pdf(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        image_files = request.FILES.getlist('images')

        # Temporary directory to store uploaded images
        # temp_directory = '/media/temporary/'
        temp_directory = os.path.join(settings.MEDIA_ROOT, 'temporary')  # Use project-specific directory
        os.makedirs(temp_directory, exist_ok=True)
        
        # Save uploaded images to the temporary directory
        image_paths = []
        for img_file in image_files:
            image_path = os.path.join(temp_directory, img_file.name)
            with open(image_path, 'wb') as f:
                for chunk in img_file.chunks():
                    f.write(chunk)
            image_paths.append(image_path)

        # Convert images to PDF
        pdf_data = img2pdf.convert(image_paths)

        # Create an HTTP response with PDF content to force download
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="output.pdf"'
        
        # Clean up: remove temporary image files and directory
        for image_path in image_paths:
            os.remove(image_path)
        os.rmdir(temp_directory)

        return response
    meta = Meta(
        title='iLovePdfConverterOnline - Image to PDF',
        description='Convert image file (jpg, jpeg, png) to PDF file format',
        keywords=['png', 'image', 'jpg', 'jpeg'],
        og_title='iLovePdfConverterOnline - Image to PDF',
        og_description='Convert image file (jpg, jpeg, png) to PDF file format',

    )

    context = {'meta': meta}

    return render(request, 'tools/imgtopdf.html')


def word_to_pdf_View(request):
    if request.method == 'POST' and request.FILES.get('word_file'):
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

        # Convert the Word file to PDF 
        convert_word_to_pdf(temp_file_path, output_pdf_path) 

        # Clean up temporary file
        clean_temp_files(temp_file_path)

        # Serve the PDF file for download
        with open(output_pdf_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={output_file_name}'
            return response

    # all_keywords = ['word', 'pdf',  'convert', 'doc', 'docx', 'online converter']
    meta = Meta(
        title='Word to PDF converter',
        description='iLovePdfConverterOnline Convert word document file (doc, docx) to PDF file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'docxtopdf'],
        # keywords=', '.join(all_keywords),
        og_title='Word to PDF converter',
        og_description='iLovePdfConverterOnline Convert word document file (doc, docx) to PDF file format',

    )

    tool_attachment = ToolAttachment.objects.get(function_name='word_to_pdf_View')
    context = {'meta': meta, 'tool_attachment': tool_attachment}     
    return render(request, 'tools/word_to_pdf.html', context)

    
def powerpoint_to_pdf_View(request):
    return render(request, template_name='tools/powerpoint_to_pdf.html')

# def excel_to_pdf_View(request):
#     return render(request, template_name='tools/excel_to_pdf.html')

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


# def html_to_pdf_View(request):
#     return render(request, template_name='tools/html_to_pdf.html')

# working 100%
def html_to_pdf_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - HTML to PDF',
        description='Convert HTML file or URL to PDF.',
        keywords=['html', 'url', 'urls', 'links', 'file', 'download'],
        og_title='iLovePdfConverterOnline - HTML to PDF',
        og_description='Convert HTML file or URL to PDF.',
    )

    context = {'meta': meta}

    if request.method == 'POST':
        if 'url' in request.POST:
            url = request.POST['url']
            # Check if the URL is not empty
            if url:
                pdf = pdfkit.from_url(url, False)
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="download.pdf"'
                return response
            else:
                # return HttpResponse("URL is empty")
                if 'html_file' in request.FILES:
                    html_file = request.FILES['html_file']
                    # Read content of HTML file
                    html_content = html_file.read().decode('utf-8')
                    # print(html_content)
                    # Convert HTML content to PDF
                    pdf = pdfkit.from_string(html_content, options={"enable-local-file-access": ""})
                    response = HttpResponse(pdf, content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename="download.pdf"'
                    return response
                else:
                    return HttpResponse("Invalid Request")
    else:
        return render(request, 'tools/html_to_pdf.html', context)



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
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to JPEG',
        description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
        keywords=['png', 'image', 'jpg', 'jpeg'],
        og_title='iLovePdfConverterOnline - PDF to JPEG',
        og_description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',

    )

    context = {'meta': meta}

    return render(request, 'tools/pdf_to_jpg.html', context)




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
    
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to Word Document',
        description='Convert PDF file in to to Word Document. PDF pages will be converted to editable text with same Formatting.',
        keywords=['word', 'ms word', 'doc', 'docx'],
        og_title='iLovePdfConverterOnline - PDF to Word Document',
        og_description='Convert PDF file in to to Word Document. PDF pages will be converted to editable text with same Formatting.',

    )

    context = {'meta': meta}

    return render(request, 'tools/pdf_to_word.html', context)


def pdf_to_powerpoint_View(request):
    return render(request, template_name='tools/pdf_to_powerpoint.html')

def pdf_to_excel_View(request):
    return render(request, template_name='tools/pdf_to_excel.html')

def pdf_to_html_View(request):
    return render(request, template_name='tools/pdf_to_html.html')

