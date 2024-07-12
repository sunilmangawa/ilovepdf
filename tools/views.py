# tools/views.py

# Django default libraries import
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.signals import request_finished
from django.dispatch import receiver
from django.forms import Form
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render, redirect
from django.template import TemplateDoesNotExist
from django.utils.text import slugify
from django.urls import reverse
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from PyPDF2 import PdfReader, PdfWriter, PageObject
from xlrd import open_workbook

# Models Import
from .models import ToolAttachment#, ConvertedPDF
from blog.models import Post

# Forms Import
from .forms import PDFUploadForm, RotatePDFForm, UploadFileForm
from .forms import RotatePDFForm

# from .tools.word_counter import word_counter_text
from .extra.split_pdf import split_pdf_by_page
from .extra.lorem_ipsum_generator import generate_lorem_ipsum

from .pdfto.pdf_to_docx_converter import pdf_to_docx_converter
from .pdfto.pdf_to_jpg_converter import convert_pdf_to_jpg, clean_up_jpg_files, create_zip_archive
# from .pdfto.pdf_to_ppt_pptx_converter import convert_pdf_to_pptx, create_ppt_slide, clean_up_temp_files, create_zip_archives

from .topdf.excel_to_pdf_converter import convert_excel_to_pdf
from .topdf.imgtopdf import convert_to_pdf
from .topdf.powerpoint_to_pdf_converter import convert_ppt_to_pdf
from .topdf.word_to_pdf_converter import clean_temp_files, convert_to_pdf#, convert_word_to_pdf


import os
import re
import docxtopdf
import img2pdf
import pdfkit
import requests
import subprocess
import tempfile
import zipfile

import base64
import ghostscript
import json
import locale
import pandas as pd
import pdf2image
import PyPDF2
import tabula
import traceback
import uuid


from io import BytesIO
from openpyxl import load_workbook
from pdf2docx import Converter
from pypdf import PdfWriter
from meta.views import Meta
from PyPDF2 import PdfMerger

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.http import require_POST
from pdfminer.high_level import extract_text_to_fp
from PIL import Image, ImageSequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, legal
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from functools import wraps

from .topdf.word_to_pdf_converter import convert_to_pdf#, LibreOfficeError, sanitize_filename


import logging
logger = logging.getLogger(__name__)



# Views for the Tools From Here:

# ------------------------CHECKED
def merge_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST":
            files = request.FILES.getlist('pdf_files')
            if len(files) == 0:
                return HttpResponse("No files uploaded.", status=400)

            merger = PdfMerger()
            try:
                for file in files:
                    merger.append(file)

                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="merged_file.pdf"'

                merger.write(response)
                merger.close()

                return response

            except Exception as e:
                return HttpResponse(str(e), status=500)
        else:
            return view_func(request, *args, **kwargs)  
    return wrapper_function

# Merge PDF Tool for Attachment in the Blog Post, uses base.html
@merge_pdf_logic
def merge_pdf_view(request):
    meta = Meta(
        title='Merge PDF files free online',
        description='Merge PDF or Combine PDF in Order you want just within clicks.',
        keywords=['merge', 'combine', 'join', 'add'],
        og_title='Merge PDF files free online',
        og_description='Merge PDF or Combine PDF in Order you want just within clicks.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='merge_pdf_view')
    context = {'meta': meta, 'tool_attachment':tool_attachment}
    return render(request, 'tools/merge_pdf.html', context)

# Merge PDF Tool for Attachment in the Blog Post, doesn't use extends base.html
@merge_pdf_logic
def merge_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Merge PDF Tool',
        description='Merge PDF or Combine PDF in Order you want just within clicks.',
        keywords=['merge', 'combine', 'join', 'add'],
        og_title='iLovePdfConverterOnline - Merge PDF Tool',
        og_description='Merge PDF or Combine PDF in Order you want just within clicks.',
    )
    context = {'meta': meta}
    return render(request, 'tools/merge_pdf_include.html', context)

# -----------------------------------------================================

def split_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST":
            form = Form(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                page_numbers = request.POST.get('page_numbers', '')
                output_files = split_pdf_by_page(file, page_numbers)

                response = HttpResponse(content_type='application/zip')
                zip_file = zipfile.ZipFile(response, 'w')
                for output_file in output_files:
                    zip_file.write(output_file, os.path.basename(output_file))
                zip_file.close()
                response['Content-Disposition'] = f'attachment; filename={file.name}.zip'
                return response
        else:
            return view_func(request, *args, **kwargs)  
    return wrapper_function


@split_pdf_logic
def split_pdf_view(request):
    meta = Meta(
        title='Split PDF document online',
        description='Split PDF or Unmerge PDF in Order you want just within clicks.',
        keywords=['split', 'unmerge', 'remove'],
        og_title='Split PDF document online',
        og_description='Split PDF or Unmerge PDF in Order you want just within clicks.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='split_pdf_view')
    context = {'meta': meta, 'tool_attachment':tool_attachment}
    return render(request, 'tools/split_pdf.html', context)

@split_pdf_logic
def split_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Split PDF',
        description='Split PDF or Unmerge PDF in Order you want just within clicks.',
        keywords=['split', 'unmerge', 'remove'],
        og_title='iLovePdfConverterOnline - Split PDF',
        og_description='Split PDF or Unmerge PDF in Order you want just within clicks.',
    )
    context = {'meta': meta}  
    return render(request, 'tools/split_pdf_include.html', context)

# -----------------------------------------================================


def get_pdf_settings(compress_level):
    """Returns the Ghostscript PDFSETTINGS parameter based on the compression level."""
    if compress_level <= 25:
        return "screen"  # Low quality
    elif compress_level <= 50:
        return "ebook"  # Medium quality
    elif compress_level <= 75:
        return "printer"  # High quality
    else:
        return "prepress"  # Maximum quality

def compress_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST':
            pdf_file = request.FILES.get('pdf_file')
            compress_level = int(request.POST.get('compress_level', 50))

            if pdf_file:
                temp_pdf_path = default_storage.save('temp_uploaded.pdf', ContentFile(pdf_file.read()))
                temp_pdf_full_path = os.path.join(default_storage.location, temp_pdf_path)
                compressed_pdf_path = os.path.join(settings.MEDIA_ROOT, 'compressed_output.pdf')

                cargs = [
                    "ps2pdf",
                    "-dNOPAUSE", "-dBATCH", "-dSAFER",
                    "-sDEVICE=pdfwrite",
                    f"-dCompatibilityLevel=1.4",
                    f"-dPDFSETTINGS=/{get_pdf_settings(compress_level)}",
                    f"-sOutputFile={compressed_pdf_path}",
                    temp_pdf_full_path
                ]

                encoding = locale.getpreferredencoding()
                cargs = [a.encode(encoding) for a in cargs]

                try:
                    ghostscript.Ghostscript(*cargs)
                except ghostscript.GhostscriptError as e:
                    return HttpResponse(f"Error processing file with Ghostscript: {e}", status=500)

                default_storage.delete(temp_pdf_path)

                with open(compressed_pdf_path, 'rb') as pdf:
                    response = HttpResponse(pdf.read(), content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename="compressed_output.pdf"'
                    os.remove(compressed_pdf_path)
                    return response
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@compress_pdf_logic
def compress_pdf_view(request):
    meta = Meta(
        title='Compress PDF file online',
        description='Compress PDF to reduce the file size with percentage level.',
        keywords=['compress', 'reduce', 'small'],
        og_title='Compress PDF file online',
        og_description='Compress PDF file online in percentage level you want just within clicks.',
    )    
    tool_attachment = ToolAttachment.objects.get(function_name='compress_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/compress_pdf.html', context)

@compress_pdf_logic
def compress_pdf_include(request):
    meta = Meta(
        title='Compress PDF file online',
        description='Compress PDF to reduce the file size with percentage level.',
        keywords=['compress', 'reduce', 'small'],
        og_title='Compress PDF file online',
        og_description='Compress PDF file online in percentage level you want just within clicks.',
    ) 
    context = {'meta': meta}
    return render(request, 'tools/compress_pdf_include.html', context)

# -----------------------------------------================================


def parse_page_numbers(pages):
    page_numbers = set()
    for part in pages.split(','):
        if '-' in part:
            start, end = part.split('-')
            page_numbers.update(range(int(start) - 1, int(end)))  # Pages are 0-indexed internally
        else:
            page_numbers.add(int(part) - 1)  # Pages are 0-indexed internally
    return page_numbers

def rotate_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST':
            form = RotatePDFForm(request.POST, request.FILES)
            if form.is_valid():
                pdf_file = request.FILES['pdf_file']
                rotation_angle = int(form.cleaned_data['rotation_angle'])
                pages_to_rotate = form.cleaned_data['pages']

                reader = PdfReader(pdf_file)
                writer = PdfWriter()

                if pages_to_rotate:
                    pages_to_rotate = parse_page_numbers(pages_to_rotate)
                else:
                    pages_to_rotate = range(len(reader.pages))

                for i, page in enumerate(reader.pages):
                    if i in pages_to_rotate:
                        page.rotate(rotation_angle)
                    writer.add_page(page)

                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="rotated.pdf"'
                writer.write(response)

                return response
        return view_func(request, *args, **kwargs)
    return wrapper_function

@rotate_pdf_logic
def rotate_pdf_view(request):
    if request.method == 'GET':
        form = RotatePDFForm()
        meta = Meta(
            title='iLovePdfConverterOnline - Rotate PDF',
            description='Rotate PDF file or pages in 90, 180 or 270 degree.',
            keywords=['rotate', 'pdf', 'turn'],
            og_title='iLovePdfConverterOnline - Rotate PDF file or pages',
            og_description='Rotate PDF file or pages in 90, 180 or 270 degree.',
        )
        tool_attachment = ToolAttachment.objects.get(function_name='rotate_pdf_view')
        context = {'meta':meta, 'form': form, 'tool_attachment': tool_attachment}
        return render(request, 'tools/rotate_pdf.html', context)

@rotate_pdf_logic
def rotate_pdf_include(request):
    if request.method == 'GET':
        form = RotatePDFForm()
        meta = Meta(
            title='iLovePdfConverterOnline - Rotate PDF',
            description='Rotate PDF file or pages in 90, 180 or 270 degree.',
            keywords=['rotate', 'pdf', 'turn'],
            og_title='iLovePdfConverterOnline - Rotate PDF file or pages',
            og_description='Rotate PDF file or pages in 90, 180 or 270 degree.',
        )
        context = {'meta':meta, 'form': form}
        return render(request, 'tools/rotate_pdf_include.html', context)


# -----------------------------------------================================

#Working on Server
def word_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('word_file'):
            try:
                word_file = request.FILES['word_file']

                # Generate unique temporary file name
                temp_filename = f"{uuid.uuid4()}.docx"
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename)

                # Save uploaded Word file to temporary location
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'word_to_pdf'))
                temp_file = fs.save(temp_filename, word_file)
                
                word_filename = word_file.name

                out_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_pdf_filename = os.path.splitext(word_filename)[0] + '.pdf'
                output_pdf_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename.replace(temp_filename.split('.')[1], 'pdf'))

                if os.path.exists(output_pdf_path):
                    # Serve the PDF file for download
                    response = FileResponse(open(output_pdf_path, 'rb'), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_pdf_path)}'
                    
                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_pdf_path]

                    return response
                else:
                    return HttpResponse("Error converting file to PDF")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function



@word_to_pdf_logic
def word_to_pdf_view(request):
    meta = Meta(
        title='Word to PDF converter',
        description='iLovePdfConverterOnline Convert word document file (doc, docx) to PDF file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'docxtopdf'],
        og_title='Word to PDF converter',
        og_description='iLovePdfConverterOnline Convert word document file (doc, docx) to PDF file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='word_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/word_to_pdf.html', context) 

@word_to_pdf_logic
def word_to_pdf_include(request):
    meta = Meta(
        title='Word to PDF file converter',
        description='iLovePdfConverterOnline Convert word document file (doc, docx) to PDF file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'docxtopdf'],
        og_title='Word to PDF file converter',
        og_description='iLovePdfConverterOnline Convert word document file (doc, docx) to PDF file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/word_to_pdf_include.html', context)

# -----------------------------------------================================


def pdf_to_word_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST' and 'pdf_file' in request.FILES:
            pdf_file = request.FILES['pdf_file']
            try:
                # Define paths for uploaded and converted files
                upload_folder = os.path.join(settings.MEDIA_ROOT, 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                uploaded_pdf_path = os.path.join(upload_folder, 'uploaded_pdf.pdf')
                output_docx_path = os.path.join(upload_folder, 'converted_doc.docx')

                # Save the uploaded PDF file
                with open(uploaded_pdf_path, 'wb') as destination:
                    for chunk in pdf_file.chunks():
                        destination.write(chunk)

                # Call the pdf_to_docx_converter function
                success, error_message = pdf_to_docx_converter(uploaded_pdf_path, output_docx_path)
                if success:
                    with open(output_docx_path, 'rb') as docx_file:
                        response = HttpResponse(docx_file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                        response['Content-Disposition'] = 'attachment; filename="PDF_to_Word_iLovePDFconverteronline.com.docx"'
                        response.cleanup_files = [uploaded_pdf_path, output_docx_path]  # Add files for cleanup
                        return response
                else:
                    return HttpResponse(f"Conversion failed. Error: {error_message}")
            except Exception as e:
                return HttpResponse(f"Conversion failed. Error: {str(e)}")
        else:
            return view_func(request, *args, **kwargs)  # Continue with the original view function
    return wrapper_function


@pdf_to_word_logic
def pdf_to_word_view(request):
    meta = Meta(
        title='PDF to Word Document converter',
        description='Convert PDF file in to to Word Document. PDF pages will be converted to editable text with same Formatting.',
        keywords=['word', 'ms word', 'doc', 'docx'],
        og_title='PDF to Word Document converter',
        og_description='Convert PDF file in to to Word Document. PDF pages will be converted to editable text with same Formatting.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_word_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_word.html', context)

@pdf_to_word_logic
def pdf_to_word_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to Word Document',
        description='Convert PDF file in to to Word Document. PDF pages will be converted to editable text with same Formatting.',
        keywords=['word', 'ms word', 'doc', 'docx'],
        og_title='iLovePdfConverterOnline - PDF to Word Document',
        og_description='Convert PDF file in to to Word Document. PDF pages will be converted to editable text with same Formatting.',
    )
    context = {'meta': meta}
    return render(request, 'tools/pdf_to_word_include.html',  context)


# -----------------------------------------================================

# Perfect working 
# https://github.com/pdf2htmlEX/pdf2htmlEX/releases/download/v0.18.8.rc1/pdf2htmlEX-0.18.8.rc1-master-20200630-Ubuntu-bionic-x86_64.deb
#   sudo dpkg -i pdf2htmlEX.deb
#   apt-get install -f


def pdf_to_html_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('pdf_file'):
            pdf_file = request.FILES['pdf_file']
            
            # Save the uploaded PDF file
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
            filename = fs.save(pdf_file.name, pdf_file)
            uploaded_file_path = fs.path(filename)
            
            # Define the output HTML file path
            output_html_path = os.path.splitext(uploaded_file_path)[0] + ".html"
            
            # Convert the PDF to HTML using pdf2htmlEX
            try:

                p = subprocess.run(['pdf2htmlEX', '--dest-dir', fs.location, uploaded_file_path])
                # p = subprocess.Popen(['pdf2htmlEX', '--dest-dir', fs.location, uploaded_file_path])
                # p.wait()
            except subprocess.CalledProcessError:
                raise Http404("Error in converting PDF to HTML")
            
            # Create an HTTP response with the HTML content
            with open(output_html_path, 'r', encoding='utf-8') as html_file:
                html_content = html_file.read()
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = 'attachment; filename="PDF2HTML_ilovepdfconverteronline.com.html"'
            response.cleanup_files = [uploaded_file_path, output_html_path]
            return response
        
        return view_func(request, *args, **kwargs)
    
    return wrapper_function


@pdf_to_html_logic
def pdf_to_html_view(request):
    meta = Meta(
        title='PDF to HTML converter online',
        description='Convert HTML file or URL to PDF.',
        keywords=['html', 'url', 'urls', 'links', 'file', 'download'],
        og_title='PDF to HTML converter online',
        og_description='Convert PDF file in to HTML file.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_html_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_html.html', context)

@pdf_to_html_logic
def pdf_to_html_include(request):
        meta = Meta(
            title='PDF to HTML converter online',
            description='Convert HTML file or URL to PDF.',
            keywords=['html', 'url', 'urls', 'links', 'file', 'download'],
            og_title='PDF to HTML converter online',
            og_description='Convert PDF file in to HTML file.',
        )
        context = {'meta': meta}
        return render(request, 'tools/pdf_to_html_include.html', context)

# -----------------------------------------================================

def image_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        pdf_data=False
        if request.method == "POST" and request.FILES.getlist('images'):
            image_files = request.FILES.getlist('images')         
            temp_directory = os.path.join(settings.MEDIA_ROOT, 'temporary')
            os.makedirs(temp_directory, exist_ok=True)
            
            image_paths = []
            for img_file in image_files:
                image_path = os.path.join(temp_directory, img_file.name)
                with open(image_path, 'wb') as f:
                    for chunk in img_file.chunks():
                        f.write(chunk)
                image_paths.append(image_path)
                # pdf_data = img2pdf.convert(image_paths)
            try:
                pdf_data = img2pdf.convert(image_paths)
            except:
                os.remove(image_path)
                os.rmdir(temp_directory)
            if pdf_data:
                response = HttpResponse(pdf_data, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="Image_to_PDF_iLovePDFconverteronline.com.pdf"'
                
                for image_path in image_paths:
                    os.remove(image_path)
                os.rmdir(temp_directory)

                return response
            else:
                return render(request, 'tools/image_to_pdf.html')
        else:
            return view_func(request, *args, **kwargs)  
    return wrapper_function

@image_to_pdf_logic
def image_to_pdf_view(request):
    meta = Meta(
        title='JPG|JPEG|PNG Image to PDF',
        description='Convert JPG/JPEG Image file in to PDF. Image will be converted to PDF.',
        keywords=['png', 'image', 'jpg', 'jpeg'],
        og_title='JPG|JPEG|PNG Image to PDF',
        og_description='Convert JPG/JPEG Image file in to PDF. Image will be converted to PDF',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='image_to_pdf_view')
    context = {'meta': meta, 'tool_attachment':tool_attachment}
    return render(request, 'tools/image_to_pdf.html', context) 

@image_to_pdf_logic
def image_to_pdf_include(request):
    meta = Meta(
        title='Image to PDF',
        description='Convert image file (jpg, jpeg, png) to PDF file format',
        keywords=['png', 'image', 'jpg', 'jpeg'],
        og_title='Image to PDF',
        og_description='Convert image file (jpg, jpeg, png) to PDF file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/image_to_pdf_include.html')  


# -----------------------------------------================================
from django.core.management import call_command
import threading
import time

def schedule_cleanup(file_paths, delay=60):
    """Schedule file cleanup after a delay in seconds."""
    def cleanup():
        time.sleep(delay)
        try:
            print(f"Attempting to call cleanup_files with: {file_paths}")
            call_command('cleanup_files', *file_paths)
        except Exception as e:
            print(f"Error during cleanup: {e}")

    thread = threading.Thread(target=cleanup)
    thread.start()


def pdf_to_image_decorator(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST':
            pdf_file = request.FILES.get('pdf_file')

            if pdf_file:
                # Define your desired output folder
                output_folder = os.path.join(settings.MEDIA_ROOT, "pdf_to_jpg")

                # Read the content of the uploaded PDF file
                pdf_content = pdf_file.read()

                # Convert PDF to JPG
                jpg_paths = convert_pdf_to_jpg(BytesIO(pdf_content), output_folder)
                print(f'Length of jpg_paths {len(jpg_paths)}')
                print(f'jpg_paths {jpg_paths}')
                image_urls = []
                for jpg_path in jpg_paths:
                    image_urls.append(request.build_absolute_uri(os.path.join(settings.MEDIA_URL, "pdf_to_jpg", os.path.basename(jpg_path))))
                
                response = JsonResponse({'image_urls': image_urls})
                schedule_cleanup(jpg_paths)  # Schedule file cleanup
                return response

        return view_func(request, *args, **kwargs)
    return wrapper_function


@pdf_to_image_decorator
def pdf_to_image_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to JPG|JPEG|PNG Image',
        description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
        keywords=['png', 'image', 'jpg', 'jpeg'],
        og_title='iLovePdfConverterOnline - PDF to JPG|JPEG|PNG Image',
        og_description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_image_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_image.html', context)

@pdf_to_image_decorator
def pdf_to_image_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to JPG|JPEG|PNG Image',
        description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
        keywords=['png', 'image', 'jpg', 'jpeg'],
        og_title='iLovePdfConverterOnline - PDF to JPG|JPEG|PNG Image',
        og_description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
    )
    context = {'meta': meta}
    return render(request, 'tools/pdf_to_image_include.html', context)

# -----------------------------------------================================

#Working for server
def powerpoint_to_pdf_logic(func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('ppt_file'):
            try:
                ppt_file = request.FILES['ppt_file']
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                filename = fs.save(ppt_file.name, ppt_file)
                file_path = fs.path(filename)

                # Convert the PPT/PPTX file to PDF using LibreOffice
                output_dir = fs.location
                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
                output_file_path = os.path.join(out_path, os.path.splitext(filename)[0] + '.pdf')

                env = os.environ.copy()
                env['HOME'] = '/tmp'
                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_path, file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                with open(output_file_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_file_path)}'

                    # Add files to cleanup list
                    response.cleanup_files = [file_path, output_file_path]

                    return response
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        return func(request, *args, **kwargs)
    return wrapper


# Settings done before working on server
# sudo mkdir -p /tmp/nobody_home
# sudo chown nobody:nogroup /tmp/nobody_home
# sudo chmod 700 /tmp/nobody_home

@csrf_exempt
@powerpoint_to_pdf_logic
def powerpoint_to_pdf_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Powerpoint to PDF converter',
        description='Convert PPT, PPTX file of PowerPoint in to PDF file format.',
        keywords=['ppt', 'pptx', 'slide', 'pdf'],
        og_title='iLovePdfConverterOnline - Powerpoint to PDF converter',
        og_description='Convert PPT, PPTX file of PowerPoint in to PDF file format.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='powerpoint_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/powerpoint_to_pdf.html', context)

@csrf_exempt
@powerpoint_to_pdf_logic
def powerpoint_to_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Powerpoint to PDF converter',
        description='Convert PPT, PPTX file of PowerPoint in to PDF file format.',
        keywords=['ppt', 'pptx', 'slide', 'pdf'],
        og_title='iLovePdfConverterOnline - Powerpoint to PDF converter',
        og_description='Convert PPT, PPTX file of PowerPoint in to PDF file format.',
    )
    context = {'meta': meta}
    return render(request, 'tools/powerpoint_to_pdf_include.html', context)

# -----------------------------------------================================

# decorators.py
from pptx import Presentation
from pdf2image import convert_from_bytes

def pdf_to_pptx_logic(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and 'pdf_file' in request.FILES:
            pdf_file = request.FILES['pdf_file']
            pdf_bytes = pdf_file.read()
            images = convert_from_bytes(pdf_bytes)
            
            prs = Presentation()
            blank_slide_layout = prs.slide_layouts[6]  # Choosing a blank slide layout

            for image in images:
                slide = prs.slides.add_slide(blank_slide_layout)
                image_stream = BytesIO()
                image.save(image_stream, format='PNG')
                image_stream.seek(0)
                
                slide.shapes.add_picture(image_stream, 0, 0, width=prs.slide_width, height=prs.slide_height)

            pptx_stream = BytesIO()
            prs.save(pptx_stream)
            pptx_stream.seek(0)

            response = HttpResponse(pptx_stream, content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
            response['Content-Disposition'] = 'attachment; filename="PDF2PowerPoint.pptx"'
            return response
        
        return func(request, *args, **kwargs)
    return wrapper


@pdf_to_pptx_logic
def pdf_to_pptx_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to PPTX (PowerPoint) converter online',
        description='Convert PDF to PPTX (PowerPoint) file online in free.',
        keywords= ['pdf', 'pptx', 'file', 'PowerPoint', 'power point', 'slide'],
        og_title='iLovePdfConverterOnline - PDF to PPTX (PowerPoint) converter online',
        og_description='Convert PDF to PPTX (PowerPoint) file online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_pptx_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    
    return render(request, 'tools/pdf_to_pptx.html', context)

@pdf_to_pptx_logic
def pdf_to_pptx_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to PPTX (PowerPoint) converter online',
        description='Convert PDF to PPTX (PowerPoint) file online in free.',
        keywords= ['pdf', 'pptx', 'file', 'PowerPoint', 'power point', 'slide'],
        og_title='iLovePdfConverterOnline - PDF to PPTX (PowerPoint) converter online',
        og_description='Convert PDF to PPTX (PowerPoint) file online in free.',
    )
    context = {'meta': meta}
    return render(request, 'tools/pdf_to_pptx_include.html', context)



# -----------------------------------------================================

#Working for XLSX, XLSM, XLTX XLTM including XLS & CSV (created with Excel but not Downloaded)
def excel_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('excel_file'):
            excel_file = request.FILES['excel_file']
            file_name = excel_file.name.lower()
            file_extension = os.path.splitext(file_name)[1]

            # Save uploaded file to MEDIA_ROOT
            file_path = os.path.join(settings.MEDIA_ROOT, excel_file.name)
            with open(file_path, 'wb') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)

            # Create PDF
            pdf_path = os.path.join(settings.MEDIA_ROOT, 'output.pdf')
            c = canvas.Canvas(pdf_path, pagesize=landscape(letter))

            top_margin = 0.5 * inch
            left_margin = 0.5 * inch
            bottom_margin = 0.5 * inch
            right_margin = 0.5 * inch

            page_width, page_height = landscape(letter)

            cell_height = 20
            font_size = 10  # Starting font size
            font = 'Helvetica'  # Font family

            if file_extension in ['.xlsx', '.xlsm', '.xltx', '.xltm']:
                workbook = load_workbook(file_path)
                worksheet = workbook.active
                max_row = worksheet.max_row
                max_column = worksheet.max_column
                ws_range = worksheet.iter_rows(values_only=True)
            elif file_extension == '.xls':
                workbook = open_workbook(file_path)
                worksheet = workbook.sheet_by_index(0)
                max_row = worksheet.nrows
                max_column = worksheet.ncols
                ws_range = (worksheet.row_values(row) for row in range(max_row))
            elif file_extension == '.csv':
                try:
                    with open(file_path, newline='', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                        data = list(reader)
                except UnicodeDecodeError:
                    return HttpResponse("Unable to decode the CSV file. Please ensure it is encoded in UTF-8.", content_type="text/plain")

                max_row = len(data)
                max_column = len(data[0]) if max_row > 0 else 0
                ws_range = iter(data)
            else:
                return HttpResponse("Unsupported file type.", content_type="text/plain")

            cell_width = (page_width - left_margin - right_margin) / max_column
            max_text_width = cell_width - 2  # Subtracting a bit for padding

            y = page_height - top_margin  # Initial y position

            for row in ws_range:
                for col_num, cell in enumerate(row):
                    x = left_margin + col_num * cell_width
                    text = str(cell)
                    current_font_size = font_size
                    while c.stringWidth(text, font, current_font_size) > max_text_width and current_font_size > 1:
                        current_font_size -= 1
                    c.setFont(font, current_font_size)
                    c.drawString(x, y, text)
                
                y -= cell_height
                
                if y < bottom_margin:
                    c.showPage()
                    y = page_height - top_margin

            c.save()

            # Provide the PDF file for download
            with open(pdf_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename=Excel2PDF_ilovepdfconverteronline.com.pdf'
                response.cleanup_files = [file_path, pdf_path]
                return response

        return view_func(request, *args, **kwargs)  # Continue with the original view function

    return wrapper_function

@excel_to_pdf_logic
def excel_to_pdf_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Excel to PDF converter',
        description='Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV file in to PDF file format.',
        keywords=['XLSX', 'XLSM', 'XLTX', 'XLTM', 'XLS'  'CSV', 'pdf'],
        og_title='iLovePdfConverterOnline - Excel to PDF converter',
        og_description='Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV file in to PDF file format.',
    )    
    tool_attachment = ToolAttachment.objects.get(function_name='excel_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/excel_to_pdf.html')

@excel_to_pdf_logic
def excel_to_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Excel to PDF converter',
        description='Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV file in to PDF file format.',
        keywords=['XLSX', 'XLSM', 'XLTX', 'XLTM', 'XLS'  'CSV', 'pdf'],
        og_title='iLovePdfConverterOnline - Excel to PDF converter',
        og_description='Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV file in to PDF file format.',
    )    
    context = {'meta': meta}
    return render(request, 'tools/excel_to_pdf_include.html')

# -----------------------------------------================================


def pdf_to_excel_logic(func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('pdf_file'):
            pdf_file = request.FILES['pdf_file']

            # Save the uploaded PDF file to uploads directory
            upload_folder = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            pdf_file_path = os.path.join(upload_folder, pdf_file.name)
            
            with open(pdf_file_path, 'wb') as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)

            try:
                # Convert PDF to CSV using tabula
                csv_file_path = os.path.join(upload_folder, 'PDF2Excel_ilovepdfconverteronline.com.csv')
                tabula.convert_into(input_path=pdf_file_path, output_path=csv_file_path, output_format='csv', pages='all', stream=True)

                # Convert CSV to XLSX using pandas
                xlsx_file_path = os.path.join(upload_folder, 'PDF2Excel_ilovepdfconverteronline.com.xlsx')
                read_file = pd.read_csv(csv_file_path)
                read_file.to_excel(xlsx_file_path, index=None, header=True)

                # Provide the XLSX file for download
                with open(xlsx_file_path, 'rb') as excel_file:
                    response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = 'attachment; filename=PDF2Excel_ilovepdfconverteronline.com.xlsx'
                    response.cleanup_files = [pdf_file_path, csv_file_path, xlsx_file_path]  # Add files for cleanup
                    return response

            except Exception as e:
                return HttpResponse(f"Conversion failed. Error: {str(e)}")

        # If GET request or no pdf_file in POST
        return func(request, *args, **kwargs)

    return wrapper


@pdf_to_excel_logic
def pdf_to_excel_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to XLSX file converter online',
        description='Convert PDF to XLSX file online in free.',
        keywords= ['pdf', 'file', 'excel', 'xlsx', 'xls'],
        og_title='iLovePdfConverterOnline - PDF to XLSX file converter online',
        og_description='Convert PDF to XLSX file online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_excel_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_excel.html')

@pdf_to_excel_logic
def pdf_to_excel_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to XLSX file converter online',
        description='Convert PDF to XLSX file online in free.',
        keywords= ['pdf', 'file', 'excel', 'xlsx', 'xls'],
        og_title='iLovePdfConverterOnline - PDF to XLSX file converter online',
        og_description='Convert PDF to XLSX file online in free.',
    )
    context = {'meta': meta}
    return render(request, 'tools/pdf_to_excel_include.html')

# -----------------------------------------================================


def pdf_to_csv_logic(func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('pdf_file'):
            pdf_file = request.FILES['pdf_file']

            # Save the uploaded PDF file to uploads directory
            upload_folder = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            pdf_file_path = os.path.join(upload_folder, pdf_file.name)
            
            with open(pdf_file_path, 'wb') as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)

            try:
                # Convert PDF to CSV using tabula
                csv_file_path = os.path.join(upload_folder, 'PDF2CSV_ilovepdfconverteronline.com.csv')
                tabula.convert_into(input_path=pdf_file_path, output_path=csv_file_path, output_format='csv', pages='all', stream=True)

                # Provide the CSV file for download
                with open(csv_file_path, 'rb') as csv_file:
                    response = HttpResponse(csv_file.read(), content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=PDF2CSV_ilovepdfconverteronline.com.csv'
                    response.cleanup_files = [pdf_file_path, csv_file_path]  # Add files for cleanup
                    return response

            except Exception as e:
                return HttpResponse(f"Conversion failed. Error: {str(e)}")

        # If GET request or no pdf_file in POST
        return func(request, *args, **kwargs)

    return wrapper


@pdf_to_csv_logic
def pdf_to_csv_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to CSV file converter online',
        description='Convert PDF (Portable Document Format) to CSV (comma-separated values) file online in free.',
        keywords= ['pdf', 'file', 'excel', 'csv', 'comma-separated values', 'Portable Document Format'],
        og_title='iLovePdfConverterOnline - PDF to CSV file converter online',
        og_description='Convert PDF (Portable Document Format) to CSV (comma-separated values)  file online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_csv_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_csv.html',context)

@pdf_to_csv_logic
def pdf_to_csv_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to CSV file converter online',
        description='Convert PDF (Portable Document Format) to CSV (comma-separated values) file online in free.',
        keywords= ['pdf', 'file', 'excel', 'csv', 'comma-separated values', 'Portable Document Format'],
        og_title='iLovePdfConverterOnline - PDF to CSV file converter online',
        og_description='Convert PDF (Portable Document Format) to CSV (comma-separated values)  file online in free.',
    )
    context = {'meta': meta}
    return render(request, 'tools/pdf_to_csv_include.html', context)

# -----------------------------------------================================

def json_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST' and 'json_file' in request.FILES:
            json_file = request.FILES['json_file']
            try:
                # Save the uploaded JSON file
                with open('uploaded_json.json', 'wb') as destination:
                    for chunk in json_file.chunks():
                        destination.write(chunk)
                
                # Load the JSON data
                with open('uploaded_json.json', 'r') as file:
                    data = json.load(file)
                
                if not isinstance(data, dict):
                    return HttpResponse("Conversion failed. The uploaded JSON file is not properly formatted.")
                
                # Create PDF
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="JSON_to_PDF.pdf"'

                # Render JSON data to PDF
                pdf = canvas.Canvas(response, pagesize=letter)
                y_coordinate = 700
                for line in json.dumps(data, indent=4).split('\n'):
                    pdf.drawString(100, y_coordinate, line)
                    y_coordinate -= 12  # Move to the next line
                pdf.save()
                
                return response
            except Exception as e:
                logger.error(f"Conversion failed. Error: {e}")
                logger.error(traceback.format_exc())
                return HttpResponse("Conversion failed. An error occurred during conversion. Check File Type Uploaded.")
        else:
            return view_func(request, *args, **kwargs)  # Continue with the original view function
    return wrapper_function

@json_to_pdf_logic
def json_to_pdf_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - JSON to PDF converter online',
        description='Convert JSON (JavaScript Object Notation) file in to PDF (Portable Document Format) online in free.',
        keywords=['pdf', 'json', 'Portable Document Format', 'JavaScript Object Notation'],
        og_title='iLovePdfConverterOnline - JSON to PDF converter online',
        og_description='Convert JSON (JavaScript Object Notation) file in to PDF (Portable Document Format) online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='json_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/json_to_pdf.html', context)

def json_to_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - JSON to PDF converter online',
        description='Convert JSON (JavaScript Object Notation) file in to PDF (Portable Document Format) online in free.',
        keywords=['pdf', 'json', 'Portable Document Format', 'JavaScript Object Notation'],
        og_title='iLovePdfConverterOnline - JSON to PDF converter online',
        og_description='Convert JSON (JavaScript Object Notation) file in to PDF (Portable Document Format) online in free.',
    )
    context = {'meta': meta}
    return render(request, 'tools/json_to_pdf_include.html', context)

# -----------------------------------------================================

import logging
logger = logging.getLogger(__name__)

def pdf_to_json_logic(view_func):
    @wraps(view_func)
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST' and 'pdf_file' in request.FILES:
            pdf_file = request.FILES['pdf_file']
            try:
                # Save the uploaded PDF file
                with open('uploaded_pdf.pdf', 'wb') as destination:
                    for chunk in pdf_file.chunks():
                        destination.write(chunk)
                
                # Read PDF file and extract text
                with open('uploaded_pdf.pdf', 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page_num in range(len(pdf_reader.pages)):
                        text += pdf_reader.pages[page_num].extract_text()
                
                # Convert extracted text to JSON format
                json_data = json.loads(text)

                # Save JSON data to a file
                with open('PDF_to_JSON.json', 'w') as json_file:
                    json.dump(json_data, json_file, indent=4)
                
                return FileResponse(open('PDF_to_JSON.json', 'rb'), as_attachment=True)
            except Exception as e:
                logger.error(f"Conversion failed. Error: {e}")
                logger.error(traceback.format_exc())
                return HttpResponse("Conversion failed. An error occurred during conversion.")
        else:
            return view_func(request, *args, **kwargs)  # Continue with the original view function
    return wrapper_function

@pdf_to_json_logic
def pdf_to_json_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to JSON converter online',
        description='Convert PDF (Portable Document Format) file in to JSON (JavaScript Object Notation) file format online in free.',
        keywords=['pdf', 'json', 'Portable Document Format', 'JavaScript Object Notation'],
        og_title='iLovePdfConverterOnline - PDF to JSON converter online',
        og_description='Convert PDF (Portable Document Format) file in to JSON (JavaScript Object Notation) file format online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_json_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_json.html', context)

@pdf_to_json_logic
def pdf_to_json_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to JSON converter online',
        description='Convert PDF (Portable Document Format) file in to JSON (JavaScript Object Notation) file format online in free.',
        keywords=['pdf', 'json', 'Portable Document Format', 'JavaScript Object Notation'],
        og_title='iLovePdfConverterOnline - PDF to JSON converter online',
        og_description='Convert PDF (Portable Document Format) file in to JSON (JavaScript Object Notation) file format online in free.',
    )
    context = {'meta': meta}
    return render(request, 'tools/pdf_to_json_include.html', context)

# -----------------------------------------================================

def string_to_base64_logic(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        context = {}
        if request.method == "POST":
            original_string = request.POST.get("original_string")
            if original_string:
                base64_string = base64.b64encode(original_string.encode()).decode()
                context['base64_string'] = base64_string
                context['original_string'] = original_string
        return view_func(request, context, *args, **kwargs)
    return wrapper

@string_to_base64_logic
def string_to_base64_view(request, context):
    meta = Meta(
        title='iLovePdfConverterOnline - String to Base64 file converter online',
        description='Convert String into Base64 file format online in free.',
        keywords=['string', 'text', 'base64'],
        og_title='iLovePdfConverterOnline - String to Base64 file converter online',
        og_description='Convert String into Base64 file format online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='string_to_base64_view')
    context ['tool_attachment'] = tool_attachment
    context ['meta'] = meta

    return render(request, 'tools/string_to_base64.html', context)

@string_to_base64_logic
def string_to_base64_include(request, context):
    meta = Meta(
        title='iLovePdfConverterOnline - String to Base64 file converter online',
        description='Convert String into Base64 file format online in free.',
        keywords=['string', 'text', 'base64'],
        og_title='iLovePdfConverterOnline - String to Base64 file converter online',
        og_description='Convert String into Base64 file format online in free.',
    )
    context['meta'] = meta
    return render(request, 'tools/string_to_base64_include.html', context)

# -----------------------------------------================================

def base64_to_pdf_logic(view_func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            # Getting base64 string from the textarea input
            base64_string = request.POST.get('base64_string', '')
            try:
                # Decoding base64 string to bytes
                pdf_data = base64.b64decode(base64_string)
                print(f'pdf data {pdf_data}')

                # Creating a PDF file using reportlab
                buffer = BytesIO()
                c = canvas.Canvas(buffer)

                # Write the decoded data to the PDF
                c.drawString(100, 750, pdf_data.decode('utf-8'))
                c.save()

                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="Base642PDF_ilovepdfconverteronline.com.pdf"'

                return response
            except:
                return HttpResponseBadRequest("Invalid base64 string")
        return view_func(request, *args, **kwargs)
    return wrapper


@base64_to_pdf_logic
def base64_to_pdf_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Base64 to PDF file converter online',
        description='Convert Base64 into PDF (Portable Document Format) file format online in free.',
        keywords=['string', 'pdf', 'base64', 'Portable Document Format'],
        og_title='iLovePdfConverterOnline - Base64 to PDF file converter online',
        og_description='Convert Base64 into PDF (Portable Document Format) file format online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='base64_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/base64_to_pdf.html', context)

@base64_to_pdf_logic
def base64_to_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Base64 to PDF file converter online',
        description='Convert Base64 into PDF (Portable Document Format) file format online in free.',
        keywords=['string', 'pdf', 'base64', 'Portable Document Format'],
        og_title='iLovePdfConverterOnline - Base64 to PDF file converter online',
        og_description='Convert Base64 into PDF (Portable Document Format) file format online in free.',
    )
    context = {'meta': meta}
    return render(request, 'tools/base64_to_pdf_include.html', context)

# ---------------------------------------------====================================================

def pdf_to_base64_logic(template_name):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            base64_string = None
            if request.method == 'POST':
                pdf_file = request.FILES.get('pdf_file')
                if pdf_file:
                    base64_string = base64.b64encode(pdf_file.read()).decode('utf-8')
            context = func(request, base64_string, *args, **kwargs)
            return render(request, template_name, context)
        return wrapper
    return decorator


# Using the decorator for pdf_to_base64_view
@pdf_to_base64_logic('tools/pdf_to_base64.html')
def pdf_to_base64_view(request, base64_string):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to Base64 file converter online',
        description='Convert PDF (Portable Document Format) into Base64 file format online in free.',
        keywords=['string', 'text', 'base64', 'Portable Document Format'],
        og_title='iLovePdfConverterOnline - PDF to Base64 file converter online',
        og_description='Convert PDF (Portable Document Format) into Base64 file format online in free.',
    )
    # tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_base64_view')
    return {'meta': meta, 'base64_string': base64_string}

# Using the decorator for pdf_to_base64_include
@pdf_to_base64_logic('tools/pdf_to_base64_include.html')
def pdf_to_base64_include(request, base64_string):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to Base64 file converter online',
        description='Convert PDF (Portable Document Format) into Base64 file format online in free.',
        keywords=['string', 'text', 'base64', 'Portable Document Format'],
        og_title='iLovePdfConverterOnline - PDF to Base64 file converter online',
        og_description='Convert PDF (Portable Document Format) into Base64 file format online in free.',
    )
    return {'meta': meta, 'base64_string': base64_string}

# ---------------------------------------------====================================================


def tiff_to_pdf_logic(func):
    def wrapper(request, *args, **kwargs):
        if request.method == "POST":
            tiff_file = request.FILES.get('tiff_file')
            if not tiff_file:
                return HttpResponse("No TIFF file uploaded.", status=400)
            
            tiff_path = default_storage.save(tiff_file.name, ContentFile(tiff_file.read()))
            tiff_path_full = default_storage.path(tiff_path)

            try:
                pdf_path_full = tiff_path_full.replace('.tiff', '.pdf').replace('.tif', '.pdf')
                if not os.path.exists(tiff_path_full):
                    raise Exception(f'{tiff_path_full} not found.')

                image = Image.open(tiff_path_full)
                images = []

                for i, page in enumerate(ImageSequence.Iterator(image)):
                    page = page.convert("RGB")
                    images.append(page)

                if len(images) == 1:
                    images[0].save(pdf_path_full)
                else:
                    images[0].save(pdf_path_full, save_all=True, append_images=images[1:])
                
                # Serve the PDF file for download
                with open(pdf_path_full, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(pdf_path_full)}'
                
                # Cleanup temporary files
                try:
                    os.remove(tiff_path_full)
                    os.remove(pdf_path_full)
                except OSError:
                    pass

                return response
            except Exception as e:
                return HttpResponse(f"Error converting TIFF to PDF: {e}", status=500)
        else:
            return func(request, *args, **kwargs)
    return wrapper

@tiff_to_pdf_logic
def tiff_to_pdf_view(request, pdf_url=None):
    meta = Meta(
        title='iLovePdfConverterOnline - TIFF to PDF file converter online',
        description='Convert TIFF (Tag Image File Format) in to PDF (Portable Document Format) file format online in free.',
        keywords=['tiff', 'image', 'pdf', 'Tag Image File Format', 'Portable Document Format'],
        og_title='iLovePdfConverterOnline - TIFF to PDF file converter online',
        og_description='Convert TIFF (Tag Image File Format) in to PDF (Portable Document Format) file format online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='tiff_to_pdf_view')
    context = {'meta': meta, 'pdf_url': pdf_url, 'tool_attachment': tool_attachment}
    return render(request, 'tools/tiff_to_pdf.html', context)


@tiff_to_pdf_logic
def tiff_to_pdf_include(request, pdf_url=None):
    meta = Meta(
        title='iLovePdfConverterOnline - TIFF to PDF file converter online',
        description='Convert TIFF (Tag Image File Format) in to PDF (Portable Document Format) file format online in free.',
        keywords=['tiff', 'image', 'pdf', 'Tag Image File Format', 'Portable Document Format'],
        og_title='iLovePdfConverterOnline - TIFF to PDF file converter online',
        og_description='Convert TIFF (Tag Image File Format) in to PDF (Portable Document Format) file format online in free.',
    )
    context ={'meta': meta, 'pdf_url': pdf_url}
    return render(request, 'tools/tiff_to_pdf_include.html', context)


# ---------------------------------------------====================================================


def pdf_to_tiff_logic(func):
    def wrapper(request, *args, **kwargs):
        if request.method == "POST":
            pdf_file = request.FILES.get('pdf_file')
            if not pdf_file:
                return HttpResponse("No PDF file uploaded.", status=400)
            
            pdf_path = default_storage.save(pdf_file.name, ContentFile(pdf_file.read()))
            pdf_path_full = default_storage.path(pdf_path)

            try:
                tiff_path_full = pdf_path_full.replace('.pdf', '.tiff').replace('.pdf', '.tif')
                if not os.path.exists(pdf_path_full):
                    raise Exception(f'{pdf_path_full} not found.')

                images = pdf2image.convert_from_path(pdf_path_full)
                
                images[0].save(tiff_path_full, save_all=True, append_images=images[1:], compression='tiff_deflate')
                
                tiff_url = default_storage.url(os.path.basename(tiff_path_full))
                print(f'tiff_url {tiff_url}')
                return func(request, tiff_url=tiff_url, *args, **kwargs)
            except Exception as e:
                return HttpResponse(f"Error converting PDF to TIFF: {e}", status=500)
        else:
            return func(request, *args, **kwargs)
    return wrapper

@pdf_to_tiff_logic
def pdf_to_tiff_view(request, tiff_url=None):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to TIFF file converter online',
        description='Convert PDF (Portable Document Format) in to TIFF (Tag Image File Format) file format online in free.',
        keywords=['tiff', 'image', 'pdf', 'Portable Document Format', 'Tag Image File Format'],
        og_title='iLovePdfConverterOnline - PDF to TIFF file converter online',
        og_description='Convert PDF (Portable Document Format) in to TIFF (Tag Image File Format) file format online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_tiff_view')
    context = {'meta': meta, 'tiff_url': tiff_url, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_tiff.html', context)

@pdf_to_tiff_logic
def pdf_to_tiff_include(request, tiff_url=None):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to TIFF file converter online',
        description='Convert PDF (Portable Document Format) in to TIFF (Tag Image File Format) file format online in free.',
        keywords=['tiff', 'image', 'pdf', 'Portable Document Format', 'Tag Image File Format'],
        og_title='iLovePdfConverterOnline - PDF to TIFF file converter online',
        og_description='Convert PDF (Portable Document Format) in to TIFF (Tag Image File Format) file format online in free.',
    )
    context = {'meta': meta, 'tiff_url': tiff_url}
    return render(request, 'tools/pdf_to_tiff_include.html', context)



# -----------------------------------------================================

def xml_to_pdf_logic(view_func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            xml_content = request.POST.get('xml_content', '')

            # If a file is uploaded, read its content
            if 'xml_file' in request.FILES:
                xml_file = request.FILES['xml_file']
                xml_content = xml_file.read().decode('utf-8')

            # Get the option to remove HTML tags from the request (if provided)
            remove_tags = request.POST.get('remove_tags', False) in ['on', 'true', '1']

            # Convert XML to PDF with the chosen option
            pdf_content = convert_to_pdf(xml_content, remove_tags)

            # Send PDF as downloadable response
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="XML_to_PDF_ilovepdfconverteronline.com.pdf"'
            return response

        return view_func(request, *args, **kwargs)
    return wrapper

def convert_to_pdf(xml_content, remove_tags=False):
    """Converts XML content to PDF with an optional flag to remove HTML tags.

    Args:
        xml_content (str): The XML content to be converted.
        remove_tags (bool, optional): If True, removes HTML tags from the output PDF. Defaults to False.

    Returns:
        bytes: The generated PDF content.
    """
    if remove_tags:
        # Escape special characters to prevent them from being interpreted as HTML tags
        escaped_content = xml_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html_content = f"<html><body><pre>{escaped_content}</pre></body></html>"
    else:
        html_content = f"<html><body><pre>{xml_content}</pre></body></html>"

    # Generate PDF using pdfkit
    pdf = pdfkit.from_string(html_content, False)
    return pdf

@xml_to_pdf_logic
def xml_to_pdf_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - XML to PDF converter online',
        description='Convert Extensible Markup Language (XML) file in to PDF (Portable Document Format) online in free.',
        keywords=['pdf', 'xml', 'file', 'Portable Document Format', 'Extensible Markup Language'],
        og_title='iLovePdfConverterOnline - XML to PDF converter online',
        og_description='Convert Extensible Markup Language (XML) file in to PDF (Portable Document Format) online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='xml_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment, 'remove_tags_checked': ''}
    
    # Render the template with an optional checkbox for removing tags
    # context = {
    #     'remove_tags_checked': ''  # Set to 'checked' if desired by default
    # }
    return render(request, 'tools/xml_to_pdf.html', context)

@xml_to_pdf_logic
def xml_to_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - XML to PDF converter online',
        description='Convert Extensible Markup Language (XML) file in to PDF (Portable Document Format) online in free.',
        keywords=['pdf', 'xml', 'file', 'Portable Document Format', 'Extensible Markup Language'],
        og_title='iLovePdfConverterOnline - XML to PDF converter online',
        og_description='Convert Extensible Markup Language (XML) file in to PDF (Portable Document Format) online in free.',
    )
    context = {'meta': meta, 'remove_tags_checked': ''}
    # Render the template with an optional checkbox for removing tags
    # context = {
    #     'remove_tags_checked': ''  # Set to 'checked' if desired by default
    # }
    return render(request, 'tools/xml_to_pdf_include.html', context)

# -----------------------------------------================================


def pdf_to_xml_logic(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method == 'POST':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                pdf_file = request.FILES['file']
                # Create a BytesIO object to store the XML content
                xml_output = BytesIO()

                # Convert the PDF to XML and write it to the BytesIO object
                extract_text_to_fp(pdf_file, xml_output, output_type='xml')

                # Seek to the beginning of the BytesIO object
                xml_output.seek(0)

                # Read the XML content from the BytesIO object
                xml_content = xml_output.read()

                # Close the BytesIO object
                xml_output.close()

                response = HttpResponse(xml_content, content_type='application/xml')
                response['Content-Disposition'] = 'attachment; filename=PDF_to_XML_ilovepdfconverteronline.com.xml'
                return response
        else:
            form = UploadFileForm()
        return view_func(request, form, *args, **kwargs)
    return _wrapped_view

@pdf_to_xml_logic
def pdf_to_xml_view(request, form):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to XML converter online',
        description='Convert PDF (Portable Document Format) to XML (Extensible Markup Language) file online in free.',
        keywords= ['pdf', 'xml', 'file', 'Portable Document Format', 'Extensible Markup Language'],
        og_title='iLovePdfConverterOnline - PDF to XML converter online',
        og_description='Convert PDF (Portable Document Format) to XML (Extensible Markup Language) file online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_xml_view')
    context = {'form': form, 'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_xml.html', context)

@pdf_to_xml_logic
def pdf_to_xml_include(request, form):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to XML converter online',
        description='Convert PDF (Portable Document Format) to XML (Extensible Markup Language) file online in free.',
        keywords= ['pdf', 'xml', 'file', 'Portable Document Format', 'Extensible Markup Language'],
        og_title='iLovePdfConverterOnline - PDF to XML converter online',
        og_description='Convert PDF (Portable Document Format) to XML (Extensible Markup Language) file online in free.',
    )
    context = {'form': form, 'meta': meta}
    return render(request, 'tools/pdf_to_xml_include.html', context )

# -----------------------------------------================================

# working 100%
def html_to_pdf_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - HTML to PDF',
        description='Convert HTML file or URL in to PDF. HyperText Markup Language to Portable Document Format',
        keywords=['html', 'url', 'urls', 'links', 'file', 'download', 'pdf', 'Portable Document Format'],
        og_title='iLovePdfConverterOnline - HTML to PDF',
        og_description='Convert HTML file or URL to PDF. HyperText Markup Language to Portable Document Format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='html_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}

    if request.method == 'POST':
        if 'url' in request.POST:
            url = request.POST['url']
            # Check if the URL is not empty
            if url:
                pdf = pdfkit.from_url(url, False)
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="HTML2PDF_ilovepdfconverteronline.com.pdf"'
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
                    response['Content-Disposition'] = 'attachment; filename="HTML2PDF_ilovepdfconverteronline.com.pdf"'
                    return response
                else:
                    return HttpResponse("Invalid Request")
    else:
        return render(request, 'tools/html_to_pdf.html', context)

def html_to_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - HTML to PDF',
        description='Convert HTML file or URL to PDF.',
        keywords=['html', 'url', 'urls', 'links', 'file', 'download', 'pdf', 'Portable Document Format'],
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
                response['Content-Disposition'] = 'attachment; filename="HTML2PDF_ilovepdfconverteronline.com.pdf"'
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
                    response['Content-Disposition'] = 'attachment; filename="HTML2PDF_ilovepdfconverteronline.com.pdf"'
                    return response
                else:
                    return HttpResponse("Invalid Request")
    else:
        return render(request, 'tools/html_to_pdf_include.html', context)

# -----------------------------------------================================



def count_words(text):
    # Remove punctuation and split by whitespace to count words
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def word_counter_text_logic(template_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            context = view_func(request, *args, **kwargs)
            word_count = 0
            if request.method == 'POST':
                text = request.POST.get('text', '')
                word_count = count_words(text)
            context['word_count'] = word_count
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'word_count': word_count})
            return render(request, template_name, context)
        return _wrapped_view
    return decorator

@word_counter_text_logic('tools/word_counter_text.html')
def word_counter_text_view(request):
    context = {}
    return context

@word_counter_text_logic('tools/word_counter_text_include.html')
def word_counter_text_include(request):
    context = {}
    return context


# .................................................................==================================================

def lorem_ipsum_generator_logic(template_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            context = view_func(request, *args, **kwargs)
            if request.method == 'POST':
                paragraphs = int(request.POST.get('paragraphs', 3))
                lorem_ipsum_text = generate_lorem_ipsum(paragraphs)
                context['lorem_ipsum_text'] = lorem_ipsum_text
            else:
                context['lorem_ipsum_text'] = ""
            return render(request, template_name, context)
        return _wrapped_view
    return decorator


@lorem_ipsum_generator_logic('tools/lorem_ipsum_generator.html')
def lorem_ipsum_generator_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Lorem Ipsum Generator online',
        description='Generate Lorem Ipsum paragraph with random text online in free.',
        keywords= ['pdf', 'xml', 'file'],
        og_title='iLovePdfConverterOnline - Lorem Ipsum Generator online',
        og_description='Generate Lorem Ipsum paragraph with random text online in free.',
    )
    context = {'meta': meta}
    return context

@lorem_ipsum_generator_logic('tools/lorem_ipsum_generator_include.html')
def lorem_ipsum_generator_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Lorem Ipsum Generator online',
        description='Generate Lorem Ipsum paragraph with random text online in free.',
        keywords= ['pdf', 'xml', 'file'],
        og_title='iLovePdfConverterOnline - Lorem Ipsum Generator online',
        og_description='Generate Lorem Ipsum paragraph with random text online in free.',
    )
    context = {'meta': meta}
    return context



# .................................................................==================================================

# views.py
import io
import fitz  # PyMuPDF
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import UploadedFile

def pdf_to_raw_logic(func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('pdf_file'):
            pdf_file: UploadedFile = request.FILES['pdf_file']
            try:
                pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
                raw_image_data = []
                
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    pix = page.get_pixmap()
                    img_bytes = pix.samples  # Raw pixel data
                    raw_image_data.append(img_bytes)

                # For simplicity, we'll return the first page's raw image data
                response = HttpResponse(raw_image_data[0], content_type='application/octet-stream')
                response['Content-Disposition'] = 'attachment; filename="page_1.raw"'
                return response
            except Exception as e:
                return HttpResponseBadRequest(f"Error processing PDF file: {str(e)}")
        return func(request, *args, **kwargs)
    return wrapper

@pdf_to_raw_logic
@require_http_methods(["GET", "POST"])
def pdf_to_raw_view(request):
    return render(request, 'tools/pdf_to_raw.html')



from django.views.decorators.http import require_http_methods
import io
import rawpy
import numpy as np

def raw_to_pdf_logic(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('raw_image'):
            raw_image = request.FILES['raw_image']

            try:
                # Use rawpy to read the RAW image file
                with rawpy.imread(raw_image) as raw:
                    rgb_image = raw.postprocess()

                # Convert numpy array to PIL image
                image = Image.fromarray(rgb_image)
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG')
                buffer.seek(0)

                # Create a PDF file from the image
                pdf_buffer = io.BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=letter)
                c.drawImage(buffer, 0, 0, width=letter[0], height=letter[1])
                c.showPage()
                c.save()
                pdf_buffer.seek(0)

                response = HttpResponse(pdf_buffer, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="converted.pdf"'
                return response

            except rawpy._rawpy.LibRawError:
                return HttpResponse("Invalid RAW image file.", status=400)

        return view_func(request, *args, **kwargs)

    return wrapper

@require_http_methods(["GET", "POST"])
@raw_to_pdf_logic
def raw_to_pdf_view(request):
    return render(request, 'tools/raw_to_pdf.html')



###########################################################################################

####################################################################################################
import shutil

def odp_to_pptx_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('odp_file'):
            try:
                odp_file = request.FILES['odp_file']

                # Save uploaded ODP file to temporary location
                temp_filename = odp_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, odp_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pptx', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_pptx_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.pptx')

                if os.path.exists(output_pptx_path):
                    # Serve the PPTX file for download
                    response = FileResponse(open(output_pptx_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_pptx_path)}'
                    
                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_pptx_path]
                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)
                    return response
                else:
                    return HttpResponse("Error converting file to PPTX")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function


@odp_to_pptx_logic
def odp_to_pptx_view(request):
    meta = Meta(
        title='OpenDocument Presentation (.odp) file to Microsoft PowerPoint (.pptx) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Presentation (.odp) file in to Microsoft PowerPoint (.pptx) file format',
        keywords=['powerpoint', 'microsoft powerpoint', 'ppt', 'pptx', 'OpenDocument', 'Presentation'],
        og_title='OpenDocument Presentation (.odp) file to Microsoft PowerPoint (.pptx) file converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Presentation (.odp) file in to Microsoft PowerPoint (.pptx) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pptx_to_odp_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/odp_to_pptx.html', context)

@odp_to_pptx_logic
def odp_to_pptx_include(request):
    meta = Meta(
        title='OpenDocument Presentation (.odp) file to Microsoft PowerPoint (.pptx) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Presentation (.odp) file in to Microsoft PowerPoint (.pptx) file format',
        keywords=['powerpoint', 'microsoft powerpoint', 'ppt', 'pptx', 'OpenDocument', 'Presentation'],
        og_title='OpenDocument Presentation (.odp) file to Microsoft PowerPoint (.pptx) file converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Presentation (.odp) file in to Microsoft PowerPoint (.pptx) file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/odp_to_pptx_include.html', context)


###########################################################


def ods_to_xlsx_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('ods_file'):
            try:
                ods_file = request.FILES['ods_file']

                # Save uploaded ODS file to temporary location
                temp_filename = ods_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, ods_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'xlsx', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_xlsx_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.xlsx')

                if os.path.exists(output_xlsx_path):
                    # Serve the XLSX file for download
                    response = FileResponse(open(output_xlsx_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_xlsx_path)}'
                    
                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_xlsx_path]
                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)
                    return response
                else:
                    return HttpResponse("Error converting file to XLSX")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@ods_to_xlsx_logic
def ods_to_xlsx_view(request):
    meta = Meta(
        title='OpenDocument Spreadsheet (.ods) file to Microsoft Excel (.xlsx) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.ods) file in to Microsoft Excel (.xlsx) file format',
        keywords=['opendocument spreadsheet', 'microsoft excel', 'ods', 'xlsx', 'xls'],
        og_title='OpenDocument Spreadsheet (.ods) file to Microsoft Excel (.xlsx) file converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.ods) file in to Microsoft Excel (.xlsx) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='ods_to_xlsx_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/ods_to_xlsx.html', context)

@ods_to_xlsx_logic
def ods_to_xlsx_include(request):
    meta = Meta(
        title='OpenDocument Spreadsheet (.ods) file to Microsoft Excel (.xlsx) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.ods) file in to Microsoft Excel (.xlsx) file format',
        keywords=['opendocument spreadsheet', 'microsoft excel', 'ods', 'xlsx', 'xls'],
        og_title='OpenDocument Spreadsheet (.ods) file to Microsoft Excel (.xlsx) file converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.ods) file in to Microsoft Excel (.xlsx) file format',
    )
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/ods_to_xlsx_include.html', context)

########################################################

# import os
# import shutil
# import subprocess
# from django.conf import settings
# from django.core.files.storage import FileSystemStorage
# from django.http import FileResponse, HttpResponse
# from django.shortcuts import render

def odt_to_docx_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('odt_file'):
            try:
                odt_file = request.FILES['odt_file']

                # Save uploaded ODT file to temporary location
                temp_filename = odt_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, odt_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'docx', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_docx_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.docx')

                if os.path.exists(output_docx_path):
                    # Serve the DOCX file for download
                    response = FileResponse(open(output_docx_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_docx_path)}'
                    
                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_docx_path]
                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)
                    return response
                else:
                    return HttpResponse("Error converting file to DOCX")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@odt_to_docx_logic
def odt_to_docx_view(request):
    meta = Meta(
        title='OpenDocument Text (.odt) file to Microsoft Word (.docx) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Text (.odt) file in to Microsoft Word (.docx) file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'odt', 'opendocument', 'text'],
        og_title='OpenDocument Text (.odt) file to Microsoft Word (.docx) file converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Text (.odt) file in to Microsoft Word (.docx) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='odt_to_docx_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/odt_to_docx.html', context)

@odt_to_docx_logic
def odt_to_docx_include(request):
    meta = Meta(
        title='OpenDocument Text (.odt) file to Microsoft Word (.docx) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Text (.odt) file in to Microsoft Word (.docx) file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'odt', 'opendocument', 'text'],
        og_title='OpenDocument Text (.odt) file to Microsoft Word (.docx) file converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Text (.odt) file in to Microsoft Word (.docx) file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/odt_to_docx_include.html', context)


####################################################


def odt_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('odt_file'):
            try:
                odt_file = request.FILES['odt_file']

                # Save uploaded ODT file to temporary location
                temp_filename = odt_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, odt_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_pdf_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.pdf')

                if os.path.exists(output_pdf_path):
                    # Serve the PDF file for download
                    response = FileResponse(open(output_pdf_path, 'rb'), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_pdf_path)}'
                    
                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_pdf_path]
                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)
                    return response
                else:
                    return HttpResponse("Error converting file to PDF")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@odt_to_pdf_logic
def odt_to_pdf_view(request):
    meta = Meta(
        title='OpenDocument Text (.odt) file to Portable Document Format (.pdf) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.odt) file in to Portable Document Format (.pdf) file format',
        keywords=['OpenDocument Text', 'pdf', 'odt', 'Portable Document Format'],
        og_title='OpenDocument Text (.odt) file to Portable Document Format (.pdf) converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Text (.odt) file in to Portable Document Format (.pdf) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='odt_to_pdf_view')
    context = {'meta': meta, 'tool_attachment':tool_attachment}
    return render(request, 'tools/odt_to_pdf.html', context)

@odt_to_pdf_logic
def odt_to_pdf_include(request):
    meta = Meta(
        title='OpenDocument Text (.odt) file to Portable Document Format (.pdf) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.odt) file in to Portable Document Format (.pdf) file format',
        keywords=['OpenDocument Text', 'pdf', 'odt', 'Portable Document Format'],
        og_title='OpenDocument Text (.odt) file to Portable Document Format (.pdf) converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Text (.odt) file in to Portable Document Format (.pdf) file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/odt_to_pdf_include.html', context)

##################################################################

def ods_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('ods_file'):
            try:
                ods_file = request.FILES['ods_file']

                # Save uploaded ODS file to temporary location
                temp_filename = ods_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, ods_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_pdf_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.pdf')

                if os.path.exists(output_pdf_path):
                    # Serve the PDF file for download
                    response = FileResponse(open(output_pdf_path, 'rb'), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_pdf_path)}'
                    
                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_pdf_path]
                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)
                    return response
                else:
                    return HttpResponse("Error converting file to PDF")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function


@ods_to_pdf_logic
def ods_to_pdf_view(request):
    meta = Meta(
        title='OpenDocument Spreadsheet (.ods) file to Portable Document Format (.pdf) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.ods) file in to Portable Document Format (.pdf) file format',
        keywords=['OpenDocument Spreadsheet', 'pdf', 'ods', 'Portable Document Format'],
        og_title='OpenDocument Spreadsheet (.ods) file to Portable Document Format (.pdf) converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.ods) file in to Portable Document Format (.pdf) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='ods_to_pdf_view')
    context = {'meta': meta, 'tool_attachment':tool_attachment}
    return render(request, 'tools/ods_to_pdf.html', context)

@ods_to_pdf_logic
def ods_to_pdf_include(request):
    meta = Meta(
        title='OpenDocument Spreadsheet (.ods) file to Portable Document Format (.pdf) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.ods) file in to Portable Document Format (.pdf) file format',
        keywords=['OpenDocument Spreadsheet', 'pdf', 'ods', 'Portable Document Format'],
        og_title='OpenDocument Spreadsheet (.ods) file to Portable Document Format (.pdf) converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Spreadsheet (.ods) file in to Portable Document Format (.pdf) file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/ods_to_pdf_include.html', context)

########################################################################

def odp_to_pdf_logic(view_func):
    @wraps(view_func)
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('odp_file'):
            try:
                odp_file = request.FILES['odp_file']

                # Save uploaded ODP file to temporary location
                temp_filename = odp_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, odp_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_pdf_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.pdf')

                if os.path.exists(output_pdf_path):
                    # Serve the PDF file for download
                    response = FileResponse(open(output_pdf_path, 'rb'), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_pdf_path)}'
                    
                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_pdf_path]
                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)
                    return response
                else:
                    return HttpResponse("Error converting file to PDF")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@odp_to_pdf_logic
def odp_to_pdf_view(request):
    meta = Meta(
        title='OpenDocument Presentation (.odp) file to Portable Document Format (.pdf) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Presentation (.odp) file in to Portable Document Format (.pdf) file format',
        keywords=['OpenDocument Presentation', 'pdf', 'odp', 'Portable Document Format'],
        og_title='OpenDocument Presentation (.odp) file to Portable Document Format (.pdf) converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Presentation (.odp) file in to Portable Document Format (.pdf) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='odp_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/odp_to_pdf.html', context)

@odp_to_pdf_logic
def odp_to_pdf_include(request):
    meta = Meta(
        title='OpenDocument Presentation (.odp) file to Portable Document Format (.pdf) file converter',
        description='iLovePdfConverterOnline Converts OpenDocument Presentation (.odp) file in to Portable Document Format (.pdf) file format',
        keywords=['OpenDocument Presentation', 'pdf', 'odp', 'Portable Document Format'],
        og_title='OpenDocument Presentation (.odp) file to Portable Document Format (.pdf) converter',
        og_description='iLovePdfConverterOnline Converts OpenDocument Presentation (.odp) file in to Portable Document Format (.pdf) file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/odp_to_pdf_include.html', context)

#################################################################


def rtf_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('rtf_file'):
            try:
                rtf_file = request.FILES['rtf_file']

                # Save uploaded RTF file to temporary location
                temp_filename = rtf_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, rtf_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_pdf_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.pdf')

                if os.path.exists(output_pdf_path):
                    # Serve the PDF file for download
                    response = FileResponse(open(output_pdf_path, 'rb'), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_pdf_path)}'
                    
                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_pdf_path]
                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)
                    return response
                else:
                    return HttpResponse("Error converting file to PDF")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@rtf_to_pdf_logic
def rtf_to_pdf_view(request):
    meta = Meta(
        title='Rich Text Format (.rtf) file to Portable Document Format (.pdf) file converter',
        description='iLovePdfConverterOnline Converts Rich Text Format (.rtf) file in to Portable Document Format (.pdf) file format',
        keywords=['Portable Document Format', 'pdf', 'rtf', 'rich text format', 'text'],
        og_title='Rich Text Format (.rtf) file to Portable Document Format (.pdf) converter',
        og_description='iLovePdfConverterOnline Converts Rich Text Format (.rtf) file in to Portable Document Format (.pdf) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='rtf_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment} 
    return render(request, 'tools/rtf_to_pdf.html', context)

@rtf_to_pdf_logic
def rtf_to_pdf_include(request):
    meta = Meta(
        title='Rich Text Format (.rtf) file to Portable Document Format (.pdf) file converter',
        description='iLovePdfConverterOnline Converts Rich Text Format (.rtf) file in to Portable Document Format (.pdf) file format',
        keywords=['Portable Document Format', 'pdf', 'rtf', 'rich text format', 'text'],
        og_title='Rich Text Format (.rtf) file to Portable Document Format (.pdf) converter',
        og_description='iLovePdfConverterOnline Converts Rich Text Format (.rtf) file in to Portable Document Format (.pdf) file format',
    )
    context = {'meta': meta} 
    return render(request, 'tools/rtf_to_pdf_include.html', context)

##############################################################

def rtf_to_docx_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('rtf_file'):
            try:
                rtf_file = request.FILES['rtf_file']

                # Save uploaded RTF file to temporary location
                temp_filename = rtf_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, rtf_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'docx', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_docx_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.docx')

                if os.path.exists(output_docx_path):
                    # Serve the DOCX file for download
                    response = FileResponse(open(output_docx_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_docx_path)}'

                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_docx_path]

                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)

                    return response
                else:
                    return HttpResponse("Error converting file to DOCX")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@rtf_to_docx_logic
def rtf_to_docx_view(request):
    meta = Meta(
        title='Rich Text Format (.rtf) file to Microsoft Word (.docx) file converter',
        description='iLovePdfConverterOnline Converts Rich Text Format (.rtf) file in to Microsoft Word (.docx) file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'rtf', 'rich text format', 'text'],
        og_title='Rich Text Format (.rtf) file to Microsoft Word (.docx) converter',
        og_description='iLovePdfConverterOnline Converts Rich Text Format (.rtf) file in to Microsoft Word (.docx) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='rtf_to_docx_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment} 
    return render(request, 'tools/rtf_to_docx.html', context)

@rtf_to_docx_logic
def rtf_to_docx_include(request):
    meta = Meta(
        title='Rich Text Format (.rtf) file to Microsoft Word (.docx) file converter',
        description='iLovePdfConverterOnline Converts Rich Text Format (.rtf) file in to Microsoft Word (.docx) file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'rtf', 'rich text format', 'text'],
        og_title='Rich Text Format (.rtf) file to Microsoft Word (.docx) converter',
        og_description='iLovePdfConverterOnline Converts Rich Text Format (.rtf) file in to Microsoft Word (.docx) file format',
    )
    context = {'meta': meta} 
    return render(request, 'tools/rtf_to_docx_include.html', context)

###################################################

def docx_to_rtf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('docx_file'):
            try:
                docx_file = request.FILES['docx_file']

                # Save uploaded DOCX file to temporary location
                temp_filename = docx_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, docx_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'rtf', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_rtf_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.rtf')

                if os.path.exists(output_rtf_path):
                    # Serve the RTF file for download
                    response = FileResponse(open(output_rtf_path, 'rb'), content_type='application/rtf')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_rtf_path)}'

                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_rtf_path]

                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)

                    return response
                else:
                    return HttpResponse("Error converting file to RTF")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@docx_to_rtf_logic
def docx_to_rtf_view(request):
    meta = Meta(
        title='Microsoft Word (.docx) file to Rich Text Format (.rtf) file converter',
        description='iLovePdfConverterOnline Converts Microsoft Word (.docx) file in to Rich Text Format (.rtf) file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'rtf', 'rich text format', 'text'],
        og_title='Microsoft Word (.docx) file to Rich Text Format (.rtf) converter',
        og_description='iLovePdfConverterOnline Converts Microsoft Word (.docx) file in to Rich Text Format (.rtf) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='docx_to_rtf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment} 
    return render(request, 'tools/docx_to_rtf.html', context)

@docx_to_rtf_logic
def docx_to_rtf_include(request):
    meta = Meta(
        title='Microsoft Word (.docx) file to Rich Text Format (.rtf) file converter',
        description='iLovePdfConverterOnline Converts Microsoft Word (.docx) file in to Rich Text Format (.rtf) file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'rtf', 'rich text format', 'text'],
        og_title='Microsoft Word (.docx) file to Rich Text Format (.rtf) converter',
        og_description='iLovePdfConverterOnline Converts Microsoft Word (.docx) file in to Rich Text Format (.rtf) file format',
    )
    context = {'meta': meta} 
    return render(request, 'tools/docx_to_rtf_include.html', context)

################################################################

def docx_to_odt_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('docx_file'):
            try:
                docx_file = request.FILES['docx_file']

                # Save uploaded DOCX file to temporary location
                temp_filename = docx_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, docx_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'odt', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_odt_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.odt')

                if os.path.exists(output_odt_path):
                    # Serve the ODT file for download
                    response = FileResponse(open(output_odt_path, 'rb'), content_type='application/vnd.oasis.opendocument.text')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_odt_path)}'

                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_odt_path]

                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)

                    return response
                else:
                    return HttpResponse("Error converting file to ODT")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@docx_to_odt_logic
def docx_to_odt_view(request):
    meta = Meta(
        title='Microsoft Word (.docx) file to OpenDocument Text (.odt) file converter',
        description='iLovePdfConverterOnline Converts Microsoft Word (.docx) file in to OpenDocument Text (.odt) file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'odt', 'opendocument', 'text'],
        og_title='Microsoft Word (.docx) file to OpenDocument Text (.odt) converter',
        og_description='iLovePdfConverterOnline Converts Microsoft Word (.docx) file in to OpenDocument Text (.odt) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='docx_to_odt_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/docx_to_odt.html', context)

@docx_to_odt_logic
def docx_to_odt_include(request):
    meta = Meta(
        title='Microsoft Word (.docx) file to OpenDocument Text (.odt) file converter',
        description='iLovePdfConverterOnline Converts Microsoft Word (.docx) file in to OpenDocument Text (.odt) file format',
        keywords=['word', 'microsoft word', 'doc', 'docx', 'odt', 'opendocument', 'text'],
        og_title='Microsoft Word (.docx) file to OpenDocument Text (.odt) converter',
        og_description='iLovePdfConverterOnline Converts Microsoft Word (.docx) file in to OpenDocument Text (.odt) file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/docx_to_odt_include.html', context)

##################################################################

def xlsx_to_ods_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('xlsx_file'):
            try:
                xlsx_file = request.FILES['xlsx_file']

                # Save uploaded XLSX file to temporary location
                temp_filename = xlsx_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, xlsx_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                # Convert XLSX to ODS using LibreOffice
                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'ods', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_ods_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.ods')

                if os.path.exists(output_ods_path):
                    # Serve the ODS file for download
                    response = FileResponse(open(output_ods_path, 'rb'), content_type='application/vnd.oasis.opendocument.spreadsheet')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_ods_path)}'

                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_ods_path]

                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)

                    return response
                else:
                    return HttpResponse("Error converting file to ODS")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function

@xlsx_to_ods_logic
def xlsx_to_ods_view(request):
    meta = Meta(
        title='Excel (.xlsx) file to OpenDocument Spreadsheet (.ods) file converter',
        description='iLovePdfConverterOnline Converts Excel (.xlsx) file in to OpenDocument Spreadsheet (.ods) file format',
        keywords=['powerpoint', 'microsoft powerpoint', 'ppt', 'pptx'],
        og_title='Excel (.xlsx) file to OpenDocument Spreadsheet (.ods) converter',
        og_description='iLovePdfConverterOnline Converts Excel (.xlsx) file in to OpenDocument Spreadsheet (.ods) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='xlsx_to_ods_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/xlsx_to_ods.html', context)

@xlsx_to_ods_logic
def xlsx_to_ods_include(request):
    meta = Meta(
        title='Excel (.xlsx) file to OpenDocument Spreadsheet (.ods) file converter',
        description='iLovePdfConverterOnline Converts Excel (.xlsx) file in to OpenDocument Spreadsheet (.ods) file format',
        keywords=['powerpoint', 'microsoft powerpoint', 'ppt', 'pptx'],
        og_title='Excel (.xlsx) file to OpenDocument Spreadsheet (.ods) converter',
        og_description='iLovePdfConverterOnline Converts Excel (.xlsx) file in to OpenDocument Spreadsheet (.ods) file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/xlsx_to_ods_include.html', context)

#########################################################################


def pptx_to_odp_logic(view_func):
    @wraps(view_func)
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('pptx_file'):
            try:
                pptx_file = request.FILES['pptx_file']

                # Save uploaded PPTX file to temporary location
                temp_filename = pptx_file.name
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', temp_filename)

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                temp_file = fs.save(temp_filename, pptx_file)

                out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')

                env = os.environ.copy()
                env['HOME'] = os.path.join(settings.MEDIA_ROOT, 'uploads')

                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'odp', '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Subprocess failed with error: {result.stderr}")

                output_odp_path = os.path.join(out_path, os.path.splitext(temp_filename)[0] + '.odp')

                if os.path.exists(output_odp_path):
                    # Serve the ODP file for download
                    response = FileResponse(open(output_odp_path, 'rb'), content_type='application/vnd.oasis.opendocument.presentation')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_odp_path)}'

                    # Add files to cleanup list
                    response.cleanup_files = [temp_file_path, output_odp_path]

                    # Clean up .cache and .config directories
                    cache_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.cache')
                    config_path = os.path.join(settings.MEDIA_ROOT, 'uploads', '.config')
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                    if os.path.exists(config_path):
                        shutil.rmtree(config_path)

                    return response
                else:
                    return HttpResponse("Error converting file to ODP")
            except Exception as e:
                return HttpResponse(status=500, content=str(e))
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_function


@pptx_to_odp_logic
def pptx_to_odp_view(request):
    meta = Meta(
        title='PowerPoint (.pptx) file in to OpenDocument Presentation (.odp) file converter',
        description='iLovePdfConverterOnline Converts PowerPoint (.pptx) file in to OpenDocument Presentation (.odp) file format',
        keywords=['powerpoint', 'microsoft powerpoint', 'ppt', 'pptx'],
        og_title='PowerPoint (.pptx) to OpenDocument Presentation (.odp) converter',
        og_description='iLovePdfConverterOnline Convert PowerPoint (.pptx) in to OpenDocument Presentation (.odp) file format',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pptx_to_odp_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pptx_to_odp.html', context)

@pptx_to_odp_logic
def pptx_to_odp_include(request):
    meta = Meta(
        title='PowerPoint (.pptx) file to OpenDocument Presentation (.odp) file converter',
        description='iLovePdfConverterOnline Converts PowerPoint (.pptx) file in to OpenDocument Presentation (.odp) file format',
        keywords=['powerpoint', 'microsoft powerpoint', 'ppt', 'pptx'],
        og_title='PowerPoint (.pptx) to OpenDocument Presentation (.odp) converter',
        og_description='iLovePdfConverterOnline Converts PowerPoint (.pptx) in to OpenDocument Presentation (.odp) file format',
    )
    context = {'meta': meta}
    return render(request, 'tools/pptx_to_odp_include.html', context)

#####################################################################

