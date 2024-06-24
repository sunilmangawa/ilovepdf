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
import docxtopdf
import img2pdf
import pdfkit
import requests
import subprocess
import tempfile
import zipfile

from io import BytesIO
from openpyxl import load_workbook
from pdf2docx import Converter
from pypdf import PdfWriter
from meta.views import Meta
from PyPDF2 import PdfMerger

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

from PyPDF2 import PdfReader, PdfWriter

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

def word_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('word_file'):
            word_file = request.FILES['word_file']

            # Generate unique temporary file name
            temp_filename = f"{uuid.uuid4()}.docx"
            temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename)

            # Save uploaded Word file to temporary location
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'word_to_pdf'))
            temp_file = fs.save(temp_filename, word_file)
            
            word_filename = word_file.name

            out_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')
            # subprocess.call(['lowriter', '--headless', '--convert-to', 'pdf', '--outdir', out_path, temp_file_path])
            subprocess.call(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_path, temp_file_path])
 
            output_pdf_filename = os.path.splitext(word_filename)[0] + '.pdf'
            output_pdf_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename.replace(temp_filename.split('.')[1],'pdf'))
            
            if output_pdf_path:
                # Serve the PDF file for download
                with open(output_pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_pdf_path)}'
                    return response
            else:
                return HttpResponse("Error converting file to PDF")
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
                # Save the uploaded PDF file
                with open('uploaded_pdf.pdf', 'wb') as destination:
                    for chunk in pdf_file.chunks():
                        destination.write(chunk)
                # Define paths for converted files
                output_docx_path = 'converted_doc.docx'
                # Call the pdf_to_docx_converter function
                success, error_message = pdf_to_docx_converter('uploaded_pdf.pdf', output_docx_path)
                if success:
                    with open(output_docx_path, 'rb') as docx_file:
                        response = HttpResponse(docx_file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                        response['Content-Disposition'] = 'attachment; filename="PDF_to_Word_iLovePDFconverteronline.com.docx"'
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

def html_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST":
            if 'url' in request.POST:
                url = request.POST['url']
                if url:
                    pdf = pdfkit.from_url(url, False)
                    response = HttpResponse(pdf, content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename="HTML2PDF_iLovePDFconverteronline.com.pdf"'
                    return response
            elif 'html_file' in request.FILES:
                html_file = request.FILES['html_file']
                html_content = html_file.read().decode('utf-8')                
                pdf = pdfkit.from_string(html_content, options={"enable-local-file-access": ""})
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="HTML2PDF_iLovePDFconverteronline.com.pdf"'
                return response
            else:
                return HttpResponse("Invalid Request")
        else:
            return view_func(request, *args, **kwargs)  
    return wrapper_function

@html_to_pdf_logic
def html_to_pdf_view(request):
    meta = Meta(
        title='HTML to PDF converter online',
        description='Convert HTML file or URL to PDF. This tool converts URL/HTML frontend to PDF file',
        keywords=['html', 'url', 'urls', 'links', 'file', 'download'],
        og_title='HTML to PDF converter online',
        og_description='Convert HTML file or URL to PDF. This tool converts URL/HTML frontend to PDF file',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='html_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/html_to_pdf.html', context) 

@html_to_pdf_logic
def html_to_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - HTML | URLs to PDF file',
        description='Convert HTML file or URL to PDF file.',
        keywords=['html', 'url', 'urls', 'links', 'file', 'download'],
        og_title='iLovePdfConverterOnline - HTML | URLs to PDF file',
        og_description='Convert HTML file or URL to PDF file.',
    )
    context = {'meta': meta}
    return render(request, 'tools/html_to_pdf_include.html')

# -----------------------------------------================================

# import os
# import subprocess
# from django.shortcuts import render
# from django.http import HttpResponse, Http404
# from django.core.files.storage import FileSystemStorage
# from django.conf import settings

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
            print(f'filename: {filename}')
            print(f'uploaded_file_path: {uploaded_file_path}')
            
            # Define the output HTML file path
            output_html_path = os.path.splitext(uploaded_file_path)[0] + ".html"
            print(f'output_html_path: {output_html_path}')
            
            # Convert the PDF to HTML using pdf2htmlEX
            try:
                p = subprocess.Popen(['pdf2htmlEX', '--dest-dir', fs.location, uploaded_file_path])
                p.wait()
            except subprocess.CalledProcessError:
                raise Http404("Error in converting PDF to HTML")
            
            # Create an HTTP response with the HTML content
            with open(output_html_path, 'r', encoding='utf-8') as html_file:
                html_content = html_file.read()
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = 'attachment; filename="converted.html"'
            
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
                response['Content-Disposition'] = 'attachment; filename="JPG_to_PDF_iLovePDFconverteronline.com.pdf"'
                
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

def pdf_to_image_decorator(view_func):
    def wrapper_function(request, *args, **kwargs):
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
                zip_file_path = os.path.join(output_folder, "PDF_to_Image_iLovePDFconverteronline.com.zip")
                create_zip_archive(jpg_paths, zip_file_path)

                # Clean up temporary JPG files
                clean_up_jpg_files(jpg_paths)

                # Serve the zip file for download
                with open(zip_file_path, 'rb') as zip_file:
                    response = HttpResponse(zip_file.read(), content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_file_path)}'
                    return response
        # Render the template for GET requests
        # meta = Meta(
        #     title='PDF to JPEG Converter Online',
        #     description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
        #     keywords=['png', 'image', 'jpg', 'jpeg'],
        #     og_title='PDF to JPEG Converter Online',
        #     og_description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
        # )
        # tool_attachment = ToolAttachment.objects.get(function_name='html_to_pdf_view')
        # context = {'meta': meta, 'tool_attachment': tool_attachment}
        # return render(request, 'tools/pdf_to_image.html', context)
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


# -----------------------------------------================================





# -----------------------------------------================================

def powerpoint_to_pdf_logic(func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES['ppt_file']:
            ppt_file = request.FILES['ppt_file']
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
            filename = fs.save(ppt_file.name, ppt_file)
            file_path = fs.path(filename)

            # Convert the PPT/PPTX file to PDF using LibreOffice
            output_dir = fs.location
            out_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
            output_file_path = os.path.join(out_path, os.path.splitext(filename)[0] + '.pdf')

            subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_path, file_path])


            with open(output_file_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_file_path)}'
                return response

        return func(request, *args, **kwargs)
    return wrapper

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
# from pdf2pptx import pdf2pptx
# from io import BytesIO
# import tempfile

def pdf_to_pptx_logic(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and 'pdf_file' in request.FILES:
            pdf_file = request.FILES['pdf_file']
            pdf_bytes = pdf_file.read()
            
            # Save PDF file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(pdf_bytes)
                temp_pdf_path = temp_pdf.name

            # Convert PDF to PPTX using pdf2pptx
            pptx_stream = BytesIO()
            pdf2pptx(temp_pdf_path, pptx_stream)
            pptx_stream.seek(0)

            # Clean up temporary PDF file
            os.remove(temp_pdf_path)

            response = HttpResponse(pptx_stream, content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
            response['Content-Disposition'] = 'attachment; filename="converted_presentation.pptx"'
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
    
    return render(request, 'tools/pdf_to_pptx.html')

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
    return render(request, 'tools/pdf_to_pptx_include.html')





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
                response['Content-Disposition'] = 'attachment; filename=output.pdf'
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
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('pdf_file'):
            print("Post condition working")
            pdf_file = request.FILES['pdf_file']
            print(f"file is : {pdf_file}")
            # Assuming the uploaded file is saved in MEDIA_ROOT
            file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.name)
            with open(file_path, 'wb') as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)

            # Convert PDF to CSV using tabula
            csv_file_path = os.path.join(settings.MEDIA_ROOT, 'output.csv')
            tabula.convert_into(input_path=file_path, output_path=csv_file_path, output_format='csv', pages='all', stream=True)

            # Convert CSV to XLSX using pandas
            xlsx_file_path = os.path.join(settings.MEDIA_ROOT, 'output.xlsx')
            read_file = pd.read_csv(csv_file_path)
            read_file.to_excel(xlsx_file_path, index=None, header=True)

            # Provide the xlsx file for download
            with open(xlsx_file_path, 'rb') as excel_file:
                response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=output.xlsx'
                return response
        else:
            print("Get condition working")
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
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('pdf_file'):
            print("Post condition working")
            pdf_file = request.FILES['pdf_file']
            print(f"file is : {pdf_file}")
            # Assuming the uploaded file is saved in MEDIA_ROOT
            file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.name)
            with open(file_path, 'wb') as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)

            # Convert PDF to DataFrame
            df = tabula.read_pdf(input_path=file_path, pages='all')
            # Convert DataFrame to Excel
            excel_file_path = os.path.join(settings.MEDIA_ROOT, 'output.csv')
            tabula.convert_into(input_path=file_path, output_path=excel_file_path, output_format='csv', pages='all', stream=True)

            # Provide the excel file for download
            with open(excel_file_path, 'rb') as excel_file:
                response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=output.csv'
                return response
        else:
            print("Get condition working")
        return func(request, *args, **kwargs)
    return wrapper

@pdf_to_csv_logic
def pdf_to_csv_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to CSV file converter online',
        description='Convert PDF to CSV file online in free.',
        keywords= ['pdf', 'file', 'excel', 'csv', 'comma-separated values'],
        og_title='iLovePdfConverterOnline - PDF to CSV file converter online',
        og_description='Convert PDF to CSV file online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_csv_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_csv.html')

@pdf_to_csv_logic
def pdf_to_csv_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to CSV file converter online',
        description='Convert PDF to CSV file online in free.',
        keywords= ['pdf', 'file', 'excel', 'csv', 'comma-separated values'],
        og_title='iLovePdfConverterOnline - PDF to CSV file converter online',
        og_description='Convert PDF to CSV file online in free.',
    )
    context = {'meta': meta}
    return render(request, 'tools/pdf_to_csv_include.html')

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
        description='Convert JSON file in to PDF online in free.',
        keywords=['pdf', 'json'],
        og_title='iLovePdfConverterOnline - JSON to PDF converter online',
        og_description='Convert JSON file in to PDF online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='json_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/json_to_pdf.html', context)

def json_to_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - JSON to PDF converter online',
        description='Convert JSON file in to PDF online in free.',
        keywords=['pdf', 'json'],
        og_title='iLovePdfConverterOnline - JSON to PDF converter online',
        og_description='Convert JSON file in to PDF online in free.',
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
        description='Convert PDF file in to JSON file format online in free.',
        keywords=['pdf', 'json'],
        og_title='iLovePdfConverterOnline - PDF to JSON converter online',
        og_description='Convert PDF file in to JSON file format online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_json_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_json.html', context)

@pdf_to_json_logic
def pdf_to_json_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to JSON converter online',
        description='Convert PDF file in to JSON file format online in free.',
        keywords=['pdf', 'json'],
        og_title='iLovePdfConverterOnline - PDF to JSON converter online',
        og_description='Convert PDF file in to JSON file format online in free.',
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
    context = {'meta': meta, 'tool_attachment': tool_attachment}
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
                response['Content-Disposition'] = 'attachment; filename="converted_pdf.pdf"'

                return response
            except:
                return HttpResponseBadRequest("Invalid base64 string")
        return view_func(request, *args, **kwargs)
    return wrapper


@base64_to_pdf_logic
def base64_to_pdf_view(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Base64 to PDF file converter online',
        description='Convert Base64 into PDF file format online in free.',
        keywords=['string', 'pdf', 'base64'],
        og_title='iLovePdfConverterOnline - Base64 to PDF file converter online',
        og_description='Convert Base64 into PDF file format online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='base64_to_pdf_view')
    context = {'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/base64_to_pdf.html', context)

@base64_to_pdf_logic
def base64_to_pdf_include(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Base64 to PDF file converter online',
        description='Convert Base64 into PDF file format online in free.',
        keywords=['string', 'pdf', 'base64'],
        og_title='iLovePdfConverterOnline - Base64 to PDF file converter online',
        og_description='Convert Base64 into PDF file format online in free.',
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
        description='Convert PDF into Base64 file format online in free.',
        keywords=['string', 'text', 'base64'],
        og_title='iLovePdfConverterOnline - PDF to Base64 file converter online',
        og_description='Convert PDF into Base64 file format online in free.',
    )
    # tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_base64_view')
    return {'meta': meta, 'base64_string': base64_string}

# Using the decorator for pdf_to_base64_include
@pdf_to_base64_logic('tools/pdf_to_base64_include.html')
def pdf_to_base64_include(request, base64_string):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to Base64 file converter online',
        description='Convert PDF into Base64 file format online in free.',
        keywords=['string', 'text', 'base64'],
        og_title='iLovePdfConverterOnline - PDF to Base64 file converter online',
        og_description='Convert PDF into Base64 file format online in free.',
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
                
                pdf_url = default_storage.url(os.path.basename(pdf_path_full))
                return func(request, pdf_url=pdf_url, *args, **kwargs)
            except Exception as e:
                return HttpResponse(f"Error converting TIFF to PDF: {e}", status=500)
        else:
            return func(request, *args, **kwargs)
    return wrapper

@tiff_to_pdf_logic
def tiff_to_pdf_view(request, pdf_url=None):
    meta = Meta(
        title='iLovePdfConverterOnline - TIFF to PDF file converter online',
        description='Convert TIFF in to PDF file format online in free.',
        keywords=['tiff', 'image', 'pdf'],
        og_title='iLovePdfConverterOnline - TIFF to PDF file converter online',
        og_description='Convert TIFF in to PDF file format online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='tiff_to_pdf_view')
    context = {'meta': meta, 'pdf_url': pdf_url, 'tool_attachment': tool_attachment}
    return render(request, 'tools/tiff_to_pdf.html', context)


@tiff_to_pdf_logic
def tiff_to_pdf_include(request, pdf_url=None):
    meta = Meta(
        title='iLovePdfConverterOnline - TIFF to PDF file converter online',
        description='Convert TIFF in to PDF file format online in free.',
        keywords=['tiff', 'image', 'pdf'],
        og_title='iLovePdfConverterOnline - TIFF to PDF file converter online',
        og_description='Convert TIFF in to PDF file format online in free.',
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
        description='Convert PDF in to TIFF file format online in free.',
        keywords=['tiff', 'image', 'pdf'],
        og_title='iLovePdfConverterOnline - PDF to TIFF file converter online',
        og_description='Convert PDF in to TIFF file format online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='powerpoint_to_pdf_view')
    context = {'meta': meta, 'tiff_url': tiff_url, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_tiff.html', context)

@pdf_to_tiff_logic
def pdf_to_tiff_include(request, tiff_url=None):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to TIFF file converter online',
        description='Convert PDF in to TIFF file format online in free.',
        keywords=['tiff', 'image', 'pdf'],
        og_title='iLovePdfConverterOnline - PDF to TIFF file converter online',
        og_description='Convert PDF in to TIFF file format online in free.',
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
            response['Content-Disposition'] = 'attachment; filename="XML_to_PDF.pdf"'
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
        description='Convert Extensible Markup Language (XML) file in to PDF online in free.',
        keywords=['pdf', 'xml'],
        og_title='iLovePdfConverterOnline - XML to PDF converter online',
        og_description='Convert Extensible Markup Language (XML) file in to PDF online in free.',
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
        description='Convert Extensible Markup Language (XML) file in to PDF online in free.',
        keywords=['pdf', 'xml'],
        og_title='iLovePdfConverterOnline - XML to PDF converter online',
        og_description='Convert Extensible Markup Language (XML) file in to PDF online in free.',
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
                response['Content-Disposition'] = 'attachment; filename=PDF_to_XML.xml'
                return response
        else:
            form = UploadFileForm()
        return view_func(request, form, *args, **kwargs)
    return _wrapped_view

@pdf_to_xml_logic
def pdf_to_xml_view(request, form):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to XML converter online',
        description='Convert PDF to XML (Extensible Markup Language) file online in free.',
        keywords= ['pdf', 'xml', 'file'],
        og_title='iLovePdfConverterOnline - PDF to XML converter online',
        og_description='Convert PDF to XML (Extensible Markup Language) file online in free.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='pdf_to_xml_view')
    context = {'form': form, 'meta': meta, 'tool_attachment': tool_attachment}
    return render(request, 'tools/pdf_to_xml.html', context)

@pdf_to_xml_logic
def pdf_to_xml_include(request, form):
    meta = Meta(
        title='iLovePdfConverterOnline - PDF to XML converter online',
        description='Convert PDF to XML (Extensible Markup Language) file online in free.',
        keywords= ['pdf', 'xml', 'file'],
        og_title='iLovePdfConverterOnline - PDF to XML converter online',
        og_description='Convert PDF to XML (Extensible Markup Language) file online in free.',
    )
    context = {'form': form, 'meta': meta}
    return render(request, 'tools/pdf_to_xml_include.html', context )

# -----------------------------------------================================


# from functools import wraps
# from django.http import HttpResponse
# from pptx import Presentation
# from pdf2image import convert_from_bytes
# from io import BytesIO

# def pdf_to_pptx_logic(func):
#     @wraps(func)
#     def wrapper(request, *args, **kwargs):
#         if request.method == 'POST' and 'pdf_file' in request.FILES:
#             pdf_file = request.FILES['pdf_file']
#             pdf_bytes = pdf_file.read()
#             images = convert_from_bytes(pdf_bytes)
            
#             prs = Presentation()
#             blank_slide_layout = prs.slide_layouts[6]  # Choosing a blank slide layout

#             for image in images:
#                 slide = prs.slides.add_slide(blank_slide_layout)
#                 image_stream = BytesIO()
#                 image.save(image_stream, format='PNG')
#                 image_stream.seek(0)
                
#                 slide.shapes.add_picture(image_stream, 0, 0, width=prs.slide_width, height=prs.slide_height)

#             pptx_stream = BytesIO()
#             prs.save(pptx_stream)
#             pptx_stream.seek(0)

#             response = HttpResponse(pptx_stream, content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
#             response['Content-Disposition'] = 'attachment; filename="converted_presentation.pptx"'
#             return response
        
#         return func(request, *args, **kwargs)
#     return wrapper


# ------------------------------------------------------------

# def pdf_to_html(request):
#     if request.method == 'POST' and request.FILES['pdf_file']:
#         pdf_file = request.FILES['pdf_file']
        
#         # Save the uploaded PDF file
#         fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
#         filename = fs.save(pdf_file.name, pdf_file)
#         uploaded_file_path = fs.path(filename)
#         print(f'filename: {filename}')
#         print(f'uploaded_file_path: {uploaded_file_path}')
        
#         # Define the output HTML file path
#         output_html_path = os.path.splitext(uploaded_file_path)[0] + ".html"
#         print(f'output_html_path: {output_html_path}')
        
#         # Convert the PDF to HTML using pdf2htmlEX
#         try:
#             # subprocess.run(['pdf2htmlEX', '--dest-dir', fs.location, uploaded_file_path], check=True)
#             p=subprocess.Popen(['pdf2htmlEX', '--dest-dir', fs.location, uploaded_file_path])
#             p.wait()
#         except subprocess.CalledProcessError:
#             raise Http404("Error in converting PDF to HTML")
        
#         # Create an HTTP response with the HTML content
#         with open(output_html_path, 'r', encoding='utf-8') as html_file:
#             html_content = html_file.read()
        
#         response = HttpResponse(html_content, content_type='text/html')
#         response['Content-Disposition'] = 'attachment; filename="converted.html"'
        
#         return response
    
#     return render(request, 'tools/pdf_to_html.html')


# .................................................................==================================================

# def word_counter_text_view(request):
#     word_count = 0

#     if request.method == 'POST':
#         text = request.POST.get('text', '')  # Assuming the text input field has the name 'text'
#         word_count = word_counter_text(text)
#     # return render(request, 'converter/word_counter_text.html', {'word_count': word_count}) #working but redirect
#     return JsonResponse({'word_count': word_count})

import re

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





# working 100%
# def html_to_pdf_view(request):
#     meta = Meta(
#         title='iLovePdfConverterOnline - HTML to PDF',
#         description='Convert HTML file or URL to PDF.',
#         keywords=['html', 'url', 'urls', 'links', 'file', 'download'],
#         og_title='iLovePdfConverterOnline - HTML to PDF',
#         og_description='Convert HTML file or URL to PDF.',
#     )

#     context = {'meta': meta}

#     if request.method == 'POST':
#         if 'url' in request.POST:
#             url = request.POST['url']
#             # Check if the URL is not empty
#             if url:
#                 pdf = pdfkit.from_url(url, False)
#                 response = HttpResponse(pdf, content_type='application/pdf')
#                 response['Content-Disposition'] = 'attachment; filename="download.pdf"'
#                 return response
#             else:
#                 # return HttpResponse("URL is empty")
#                 if 'html_file' in request.FILES:
#                     html_file = request.FILES['html_file']
#                     # Read content of HTML file
#                     html_content = html_file.read().decode('utf-8')
#                     # print(html_content)
#                     # Convert HTML content to PDF
#                     pdf = pdfkit.from_string(html_content, options={"enable-local-file-access": ""})
#                     response = HttpResponse(pdf, content_type='application/pdf')
#                     response['Content-Disposition'] = 'attachment; filename="download.pdf"'
#                     return response
#                 else:
#                     return HttpResponse("Invalid Request")
#     else:
#         return render(request, 'tools/html_to_pdf.html', context)


# def jpg_to_pdf_view(request):
#     if request.method == 'POST' and request.FILES.getlist('images'):
#         image_files = request.FILES.getlist('images')

#         # Temporary directory to store uploaded images
#         # temp_directory = '/media/temporary/'
#         temp_directory = os.path.join(settings.MEDIA_ROOT, 'temporary')  # Use project-specific directory
#         os.makedirs(temp_directory, exist_ok=True)
        
#         # Save uploaded images to the temporary directory
#         image_paths = []
#         for img_file in image_files:
#             image_path = os.path.join(temp_directory, img_file.name)
#             with open(image_path, 'wb') as f:
#                 for chunk in img_file.chunks():
#                     f.write(chunk)
#             image_paths.append(image_path)

#         # Convert images to PDF
#         pdf_data = img2pdf.convert(image_paths)

#         # Create an HTTP response with PDF content to force download
#         response = HttpResponse(pdf_data, content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename="JPG_to_PDF_iLovePDFconverteronline.com.pdf"'
        
#         # Clean up: remove temporary image files and directory
#         for image_path in image_paths:
#             os.remove(image_path)
#         os.rmdir(temp_directory)

#         return response
#     meta = Meta(
#         title='iLovePdfConverterOnline - JPG/JPEG Image to PDF',
#         description='Convert JPG/JPEG Image file in to PDF. Image will be converted to PDF.',
#         keywords=['png', 'image', 'jpg', 'jpeg'],
#         og_title='iLovePdfConverterOnline - JPG/JPEG Image to PDF',
#         og_description='Convert JPG/JPEG Image file in to PDF. Image will be converted to PDF',

#     )

#     context = {'meta': meta}

#     return render(request, 'tools/jpg_to_pdf.html')



# def pdf_to_jpg_view(request):
#     if request.method == 'POST':
#         pdf_file = request.FILES.get('pdf_file')

#         if pdf_file:
#             # Define your desired output folder
#             output_folder = "media/pdf_to_jpg/"

#             # Read the content of the uploaded PDF file
#             pdf_content = pdf_file.read()

#             # Convert PDF to JPG
#             jpg_paths = convert_pdf_to_jpg(BytesIO(pdf_content), output_folder)

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
#     meta = Meta(
#         title='iLovePdfConverterOnline - PDF to JPEG',
#         description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
#         keywords=['png', 'image', 'jpg', 'jpeg'],
#         og_title='iLovePdfConverterOnline - PDF to JPEG',
#         og_description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',

#     )

#     context = {'meta': meta}

#     return render(request, 'tools/pdf_to_jpg.html', context)







# 100% Working for static url with post detail
# def pdf_to_word_view(request):
#     if request.method == 'POST' and 'pdf_file' in request.FILES:
#         pdf_file = request.FILES['pdf_file']
#         try:
#             # Save the uploaded PDF file
#             with open('uploaded_pdf.pdf', 'wb') as destination:
#                 for chunk in pdf_file.chunks():
#                     destination.write(chunk)
#             # Define paths for converted files
#             output_docx_path = 'converted_doc.docx'
#             # Call the pdf_to_docx_converter function
#             # success, error_message = pdf_to_docx_converter('uploaded_pdf.pdf', 'converted_doc.docx')
#             success, error_message = pdf_to_docx_converter('uploaded_pdf.pdf', output_docx_path)
#             if success:
#                 with open(output_docx_path, 'rb') as docx_file:
#                     response = HttpResponse(docx_file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#                     response['Content-Disposition'] = 'attachment; filename="converted_doc.docx"'
#                     return response
#             else:
#                 return HttpResponse(f"Conversion failed. Error: {error_message}")
#         except Exception as e:
#             return HttpResponse(f"Conversion failed. Error: {str(e)}")
#     return render(request, 'tools/pdf_to_docx_converter.html')




#.............................................................




# -------------------     PDF TO PSD      ----------------
# from pdf2image import convert_from_path

# def pdf_to_psd(request):
#     if request.method == 'POST' and request.FILES['pdf_file']:
#         pdf_file = request.FILES['pdf_file']
        
#         # Save the uploaded PDF to a temporary location
#         fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
#         temp_pdf_path = fs.save(pdf_file.name, pdf_file)
#         temp_pdf_full_path = fs.path(temp_pdf_path)
        
#         # Convert PDF to images
#         images = convert_from_path(temp_pdf_full_path)

#         # Create a PSD file
#         with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_psd_file:
#             temp_psd_path = temp_psd_file.name
            
#             # Create a blank PSD file using Pillow
#             psd_image = Image.new('RGBA', images[0].size)
            
#             for img in images:
#                 psd_image.paste(img, (0, 0))

#             psd_image.save(temp_psd_path, 'PSD')

#         # Clean up the temporary PDF file
#         os.remove(temp_pdf_full_path)
        
#         # Serve the PSD file as a downloadable response
#         with open(temp_psd_path, 'rb') as f:
#             response = HttpResponse(f.read(), content_type='image/vnd.adobe.photoshop')
#             response['Content-Disposition'] = f'attachment; filename="{os.path.basename(temp_psd_path)}"'
        
#         # Clean up the temporary PSD file
#         os.remove(temp_psd_path)

#         return response
    
#     return render(request, 'tools/pdf_to_psd.html')



# from pdf2image import convert_from_path
# from psd_tools import PSDImage

# def pdf_to_psd(request):
#     if request.method == 'POST' and request.FILES['pdf_file']:
#         pdf_file = request.FILES['pdf_file']
        
#         # Save the uploaded PDF to a temporary location
#         fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
#         temp_pdf_path = fs.save(pdf_file.name, pdf_file)
#         temp_pdf_full_path = fs.path(temp_pdf_path)
        
#         # Convert PDF to images
#         images = convert_from_path(temp_pdf_full_path)

#         # Create a new PSD file
#         layers = []
#         for img in images:
#             with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img_file:
#                 img.save(temp_img_file.name, 'PNG')
#                 layer = Layer.from_image(temp_img_file.name)
#                 layers.append(layer)
#                 os.remove(temp_img_file.name)
        
#         psd_image = PSDImage(layers=layers)

#         with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_psd_file:
#             temp_psd_path = temp_psd_file.name
#             psd_image.save(temp_psd_path)
        
#         # Clean up the temporary PDF file
#         os.remove(temp_pdf_full_path)
        
#         # Serve the PSD file as a downloadable response
#         with open(temp_psd_path, 'rb') as f:
#             response = HttpResponse(f.read(), content_type='image/vnd.adobe.photoshop')
#             response['Content-Disposition'] = f'attachment; filename="{os.path.basename(temp_psd_path)}"'
        
#         # Clean up the temporary PSD file
#         os.remove(temp_psd_path)

#         return response
    
#     return render(request, 'tools/pdf_to_psd.html')


# from psd_tools import PSDImage

# def pdf_to_psd(request):
#     if request.method == 'POST' and 'pdf_file' in request.FILES:
#         pdf_file = request.FILES['pdf_file']
#         # Convert the PDF to PSD using your preferred method or library
#         psd_path = convert_pdf_to_psd(pdf_file)
        
#         # Load the PSD file
#         psd = PSDImage.open(psd_path)
        
#         # Example: Process the layers
#         layers_info = []
#         for layer in psd:
#             if layer.is_group():
#                 for child_layer in layer:
#                     layer_info = {
#                         'name': child_layer.name,
#                         'visible': child_layer.visible,
#                         'opacity': child_layer.opacity,
#                         'blend_mode': child_layer.blend_mode,
#                     }
#                     layers_info.append(layer_info)
#             else:
#                 layer_info = {
#                     'name': layer.name,
#                     'visible': layer.visible,
#                     'opacity': layer.opacity,
#                     'blend_mode': layer.blend_mode,
#                 }
#                 layers_info.append(layer_info)
        
#         # You can save layers or the merged image as needed
#         merged_image = psd.as_PIL()
#         merged_image.save('path_to_save_merged_image.png')

#         context = {
#             'layers_info': layers_info,
#             'psd_file': psd_path,
#         }
#         return render(request, 'tools/pdf_to_psd.html', context)
#     else:
#         return render(request, 'tools/pdf_to_psd.html')

# def convert_pdf_to_psd(pdf_file):
#     # Implement the logic to convert a PDF to a PSD file and return the PSD file path
#     # This is a placeholder function, replace with actual implementation
#     psd_path = 'media/uploads/'
#     return psd_path
# #         fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
# #         temp_pdf_path = fs.save(pdf_file.name, pdf_file)
# #         temp_pdf_full_path = fs.path(temp_pdf_path)






#  100% working
# def word_to_pdf_logic(view_func):
#     def wrapper_function(request, *args, **kwargs):
#         if request.method == "POST" and request.FILES.get('word_file'):
#             word_file = request.FILES['word_file']

#             # Generate unique temporary file name
#             temp_filename = f"{uuid.uuid4()}.docx"
#             temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename)

#             # Save uploaded Word file to temporary location
#             fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'word_to_pdf'))
#             temp_file = fs.save(temp_filename, word_file)
            
#             word_filename = word_file.name
#             print(f'word_filename : {word_filename}')
#             print(f'temp_filename : {temp_filename}')
#             # subprocess.run(['doc2pdf', temp_file_path], capture_output=True) #working
#             # subprocess.run(['unoconv', '-f', 'pdf', temp_file_path], check=True) # Not working
#             out_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')
#             # subprocess.call(['soffice', '--convert-to', 'pdf', '--outdir', out_path, temp_file_path]) #Working
#             p = subprocess.Popen(['soffice', '--convert-to', 'pdf', '--outdir', out_path, temp_file_path])
#             p.wait()
#             output_pdf_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename.replace(temp_filename.split('.')[1],'pdf'))
            

#             output_pdf_filename = os.path.splitext(word_filename)[0] + '.pdf'
#             print(f'output_pdf_filename : {output_pdf_filename}')
#             print(f'output_pdf_path : {output_pdf_path}')
            
            
#             if output_pdf_path:
#                 # Serve the PDF file for download
#                 with open(output_pdf_path, 'rb') as pdf_file:
#                     print(f'Pdf_file {pdf_file.name}')

#                     response = HttpResponse(pdf_file.read(), content_type='application/pdf')
#                     response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_pdf_path)}'
#                     return response
#             else:
#                 return HttpResponse("Error converting file to PDF")
#         else:
#             return view_func(request, *args, **kwargs)  
#     return wrapper_function    


## Finally 100% working
# def word_to_pdf_logic(view_func):
#     def wrapper_function(request, *args, **kwargs):
#         if request.method == "POST" and request.FILES.get('word_file'):
#             word_file = request.FILES['word_file']

#             # Generate unique temporary file name for the Word file
#             temp_filename = f"{uuid.uuid4()}.docx"
#             temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename)

#             # Save uploaded Word file to temporary location
#             fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'word_to_pdf'))
#             temp_file = fs.save(temp_filename, word_file)

#             # Extract filename from the uploaded Word file
#             word_filename = word_file.name
#             print(f'word_filename : {word_filename}')
#             print(f'temp_filename : {temp_filename}')

#             # Construct the output PDF path with the same filename as the Word file
#             output_pdf_filename = os.path.splitext(word_filename)[0] + '.pdf'
#             output_pdf_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename.replace(temp_filename.split('.')[1],'pdf'))
#             print(f'output_pdf_filename : {output_pdf_filename}')
#             print(f'output_pdf_path : {output_pdf_path}')

#             # Convert Word file to PDF
#             subprocess.run(['doc2pdf', temp_file_path], capture_output=True)

#             # Check if the PDF file was created
#             if os.path.exists(output_pdf_path):
#                 # Serve the PDF file for download
#                 with open(output_pdf_path, 'rb') as pdf_file:
#                     print(f'Pdf_file {pdf_file.name}')
#                     response = HttpResponse(pdf_file.read(), content_type='application/pdf')
#                     response['Content-Disposition'] = f'attachment; filename={pdf_file.name.replace(pdf_file.name,output_pdf_filename)}'
#                     return response
#             else:
#                 return HttpResponse("Error converting file to PDF")
#         else:
#             return view_func(request, *args, **kwargs)  
#     return wrapper_function


# #Working with Windows not linux
# def word_to_pdf_logic(view_func):
#     def wrapper_function(request, *args, **kwargs):
#         if request.method == "POST" and request.FILES.get('word_file'):
#             word_file = request.FILES['word_file']

#             # ... (Your temp file generation and validation)
#             # Generate a unique temporary file name (optional)
#             temp_filename = f"{uuid.uuid4()}.docx"
#             temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename)

#             # Save the uploaded Word file to the media directory
#             with open(temp_file_path, 'wb') as temp_file:
#                 for chunk in word_file.chunks():
#                     temp_file.write(chunk)

#             # Generate the output PDF file name (with renaming)
#             output_file_name = word_file.name.replace(' ', '_').replace('.docx', '.pdf').replace('.doc', '.pdf').replace('.txt', '.pdf')
#             print(f'output_file_name: {output_file_name}')
#             output_pdf_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', output_file_name)
#             print(f'output_pdf_path: {output_pdf_path}')

#             # Convert the Word file to PDF
#             convert_word_to_pdf(temp_file_path, output_pdf_path)
#             # if not os.path.exists(output_pdf_path):
#             #     print(f"Output PDF file not created: {output_pdf_path}")
#             # else:
#             #     print(f"Pdf File created {output_pdf_path}")
#             # # Clean up temporary file
#             # clean_temp_files(temp_file_path)

#             # Serve the PDF file for download
#             with open(output_pdf_path, 'rb') as pdf_file:
#                 response = HttpResponse(pdf_file.read(), content_type='application/pdf')
#                 response['Content-Disposition'] = f'attachment; filename={output_file_name}'
#                 return response
#         else:
#             return view_func(request, *args, **kwargs)  
#     return wrapper_function    



# def excel_to_pdf_view(request):
#     if request.method == 'POST' and request.FILES['excel_file']:
#         excel_file = request.FILES['excel_file']
#         print("excel_file: ", excel_file)
#         print("excel_file Type: ", type(excel_file))
#         workbook = load_workbook(excel_file, data_only=True)
#         worksheet = workbook.active

#         pw = PdfWriter('converted_pdf.pdf')
#         # pw.setFont('Courier', 12)
#         # pw.setHeader('Excel to PDF Converter - Converted from XLSX data')
#         # pw.setFooter('Generated using openpyxl and xtopdf')

#         ws_range = worksheet.iter_rows(values_only=True)
#         for row in ws_range:
#             s = ''
#             for cell in row:
#                 if cell is None:
#                     s += ' ' * 11
#                 else:
#                     s += str(cell).rjust(10) + ' '
#             pw.writeLine(s)
        
#         pw.savePage()
#         pw.close()

#         # Serve the PDF for download
#         with open('converted_pdf.pdf', 'rb') as f:
#             response = HttpResponse(f.read(), content_type='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename="converted_pdf.pdf"'
#             return response
    
#     return render(request, 'tools/excel_to_pdf.html')


# def excel_to_pdf(request):
#     if request.method == 'POST' and request.FILES['excel_file']:
#         excel_file = request.FILES['excel_file']
#         # Assuming the uploaded file is saved in MEDIA_ROOT
#         file_path = os.path.join(settings.MEDIA_ROOT, excel_file.name)
#         with open(file_path, 'wb') as destination:
#             for chunk in excel_file.chunks():
#                 destination.write(chunk)

#         # Create PDF
#         pdf_path = os.path.join(settings.MEDIA_ROOT, 'output.pdf')
#         workbook = load_workbook(file_path)
#         worksheet = workbook.active
#         max_row = worksheet.max_row
#         print(f'max_row :{max_row}')
#         max_column = worksheet.max_column
#         print(f'max_column :{max_column}')

#         c = canvas.Canvas(pdf_path, pagesize=landscape(legal))

#         top_margin = 1 * inch
#         left_margin = 0.75 * inch
#         bottom_margin = 0.75 * inch
#         right_margin = 0.75 * inch

#         cell_width = (11 * inch - left_margin - right_margin) / max_column
#         cell_height = (8.5 * inch - top_margin - bottom_margin) / max_row

#         for row in range(1, max_row + 1):
#             for column in range(1, max_column + 1):
#                 cell = worksheet.cell(row=row, column=column)
#                 text = str(cell.value)
#                 x = left_margin + (column - 1) * cell_width
#                 y = 11 * inch - (top_margin + row * cell_height)
#                 c.drawString(x, y, text)

#         c.save()

#         # Provide the PDF file for download
#         with open(pdf_path, 'rb') as pdf_file:
#             response = HttpResponse(pdf_file.read(), content_type='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename=excel2pdf.pdf'
#             return response

#     return render(request, 'tools/excel_to_pdf.html')



#100% working for image to pdf ------------------------CHECKED
# def image_to_pdf_include(request):
#     if request.method == 'POST' and request.FILES.getlist('images'):
#         image_files = request.FILES.getlist('images')

#         # Temporary directory to store uploaded images
#         # temp_directory = '/media/temporary/'
#         temp_directory = os.path.join(settings.MEDIA_ROOT, 'temporary')  # Use project-specific directory
#         os.makedirs(temp_directory, exist_ok=True)
        
#         # Save uploaded images to the temporary directory
#         image_paths = []
#         for img_file in image_files:
#             image_path = os.path.join(temp_directory, img_file.name)
#             with open(image_path, 'wb') as f:
#                 for chunk in img_file.chunks():
#                     f.write(chunk)
#             image_paths.append(image_path)

#         # Convert images to PDF
#         pdf_data = img2pdf.convert(image_paths)

#         # Create an HTTP response with PDF content to force download
#         response = HttpResponse(pdf_data, content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename="Image_to_PDF_iLovePDFconverteronline.com.pdf"'
        
#         # Clean up: remove temporary image files and directory
#         for image_path in image_paths:
#             os.remove(image_path)
#         os.rmdir(temp_directory)

#         return response
#     meta = Meta(
#         title='iLovePdfConverterOnline - Image to PDF',
#         description='Convert image file (jpg, jpeg, png) to PDF file format',
#         keywords=['png', 'image', 'jpg', 'jpeg'],
#         og_title='iLovePdfConverterOnline - Image to PDF',
#         og_description='Convert image file (jpg, jpeg, png) to PDF file format',

#     )

#     context = {'meta': meta}

#     return render(request, 'tools/image_to_pdf_include.html')



# function used with rotate_pdf_view
# def parse_page_numbers(pages):
#     page_numbers = set()
#     for part in pages.split(','):
#         if '-' in part:
#             start, end = part.split('-')
#             page_numbers.update(range(int(start) - 1, int(end)))  # Pages are 0-indexed internally
#         else:
#             page_numbers.add(int(part) - 1)  # Pages are 0-indexed internally
#     return page_numbers


# 100% working for Full PDF Rotation and Specific pages
# def rotate_pdf(request):
#     if request.method == 'POST':
#         form = RotatePDFForm(request.POST, request.FILES)
#         if form.is_valid():
#             pdf_file = request.FILES['pdf_file']
#             rotation_angle = int(form.cleaned_data['rotation_angle'])  # Convert to integer
#             pages_to_rotate = form.cleaned_data['pages']  # Get the pages field

#             reader = PdfReader(pdf_file)
#             writer = PdfWriter()

#             # Parse the pages to rotate
#             if pages_to_rotate:
#                 pages_to_rotate = parse_page_numbers(pages_to_rotate)
#             else:
#                 print(f'Page Length {range(len(reader.pages))}')
#                 pages_to_rotate = range(len(reader.pages))

#             for i, page in enumerate(reader.pages):
#                 if i in pages_to_rotate:
#                     # page = PageObject(page)
#                     page.rotate(rotation_angle)
#                 writer.addPage(page)

#             response = HttpResponse(content_type='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename="rotated.pdf"'
            
#             writer.write(response)  # Write the PDF to the response
            
#             return response
#     else:
#         form = RotatePDFForm()

#     context = {'form': form}
#     return render(request, 'tools/rotate_pdf.html', context)



# Working Level 1
# from django.shortcuts import render
# from django.http import HttpResponse
# from PyPDF2 import PdfReader, PdfWriter
# from .forms import RotatePDFForm

# def rotate_pdf_view(request):
#     if request.method == 'POST':
#         form = RotatePDFForm(request.POST, request.FILES)
#         if form.is_valid():
#             pdf_file = request.FILES['pdf_file']
#             rotation_angle = int(form.cleaned_data['rotation_angle'])  # Convert to integer

#             reader = PdfReader(pdf_file)
#             writer = PdfWriter()

#             for page in reader.pages:
#                 page.rotate(rotation_angle)  # Use rotate_clockwise method
#                 writer.add_page(page)

#             response = HttpResponse(content_type='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename="rotated.pdf"'
            
#             writer.write(response)  # Write the PDF to the response
            
#             return response
#     else:
#         form = RotatePDFForm()

#     context = {'form': form}
#     return render(request, 'tools/rotate_pdf.html', context)


# Working Level 2
# from django.shortcuts import render
# from django.http import HttpResponse
# from .forms import RotatePDFForm

# def rotate_pdf_view(request):
#     if request.method == 'POST':
#         form = RotatePDFForm(request.POST, request.FILES)
#         if form.is_valid():
#             pdf_file = request.FILES['pdf_file']
#             rotation_angle = int(form.cleaned_data['rotation_angle'])  # Convert to integer
#             pages_to_rotate = form.cleaned_data['pages']  # Get the pages field

#             reader = PdfReader(pdf_file)
#             writer = PdfWriter()

#             # Parse the pages to rotate
#             if pages_to_rotate:
#                 pages_to_rotate = parse_page_numbers(pages_to_rotate)
#             else:
#                 pages_to_rotate = range(len(reader.pages))

#             for i, page in enumerate(reader.pages):
#                 if i in pages_to_rotate:
#                     page.rotate(rotation_angle)
#                 writer.add_page(page)

#             response = HttpResponse(content_type='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename="rotated.pdf"'
            
#             writer.write(response)  # Write the PDF to the response
            
#             return response
#     else:
#         form = RotatePDFForm()

#     context = {'form': form}
#     return render(request, 'tools/rotate_pdf.html', context)

# # def rotate_pdf_logic(view_func):
# #     def wrapper_function(request, *args, **kwargs):
# #         if request.method == 'POST':
# #             form = RotatePDFForm(request.POST, request.FILES)
# #             if form.is_valid():
# #                 pdf_file = request.FILES['pdf_file']
# #                 rotation_angle = int(form.cleaned_data['rotation_angle'])
# #                 pages_to_rotate = form.cleaned_data['pages']

# #                 reader = PdfReader(pdf_file)
# #                 writer = PdfWriter()

# #                 if pages_to_rotate:
# #                     pages_to_rotate = parse_page_numbers(pages_to_rotate)
# #                 else:
# #                     pages_to_rotate = range(len(reader.pages))

# #                 for i, page in enumerate(reader.pages):
# #                     if i in pages_to_rotate:
# #                         page.rotate(rotation_angle)
# #                     writer.add_page(page)

# #                 response = HttpResponse(content_type='application/pdf')
# #                 response['Content-Disposition'] = 'attachment; filename="rotated.pdf"'
# #                 writer.write(response)

# #                 return response
# #         else:
# #             form = RotatePDFForm()

# #         context = {'form': form}
# #         return render(request, 'tools/rotate_pdf.html', context)
# #     return wrapper_function





# @rotate_pdf_logic
# def rotate_pdf_view(request):
#     tool_attachment = ToolAttachment.objects.get(function_name='rotate_pdf_view')
#     context = {'tool_attachment': tool_attachment}
#     return render(request, 'tools/rotate_pdf.html', context)

# @rotate_pdf_logic
# def rotate_pdf_include(request):
#     return render(request, 'tools/rotate_pdf_include.html')


# #Working for XLSX, XLSM, XLTX XLTM
# def excel_to_pdf_logic(view_func):
#     def wrapper_function(request, *args, **kwargs):
#         if request.method == 'POST' and request.FILES.get('excel_file'):
#             excel_file = request.FILES['excel_file']
#             # Assuming the uploaded file is saved in MEDIA_ROOT
#             file_path = os.path.join(settings.MEDIA_ROOT, excel_file.name)
#             with open(file_path, 'wb') as destination:
#                 for chunk in excel_file.chunks():
#                     destination.write(chunk)

#             # Create PDF
#             pdf_path = os.path.join(settings.MEDIA_ROOT, 'output.pdf')
#             workbook = load_workbook(file_path)
#             worksheet = workbook.active
#             max_row = worksheet.max_row
#             max_column = worksheet.max_column

#             c = canvas.Canvas(pdf_path, pagesize=landscape(letter))

#             top_margin = 0.5 * inch
#             left_margin = 0.5 * inch
#             bottom_margin = 0.5 * inch
#             right_margin = 0.5 * inch

#             page_width, page_height = landscape(letter)

#             cell_width = (page_width - left_margin - right_margin) / max_column
#             cell_height = 20

#             max_text_width = cell_width - 2  # Subtracting a bit for padding

#             font_size = 10  # Starting font size
#             font = 'Helvetica'  # Font family

#             y = page_height - top_margin  # Initial y position

#             for row in range(1, max_row + 1):
#                 for column in range(1, max_column + 1):
#                     x = left_margin + (column - 1) * cell_width
#                     cell = worksheet.cell(row=row, column=column)
#                     text = str(cell.value)
                    
#                     # Adjust font size to fit the cell width
#                     current_font_size = font_size
#                     while c.stringWidth(text, font, current_font_size) > max_text_width and current_font_size > 1:
#                         current_font_size -= 1
                    
#                     c.setFont(font, current_font_size)
#                     c.drawString(x, y, text)
                
#                 y -= cell_height
                
#                 # Check if the content exceeds the page height, then create a new page
#                 if y < bottom_margin:
#                     c.showPage()
#                     y = page_height - top_margin

#             c.save()

#             # Provide the PDF file for download
#             with open(pdf_path, 'rb') as pdf_file:
#                 response = HttpResponse(pdf_file.read(), content_type='application/pdf')
#                 response['Content-Disposition'] = 'attachment; filename=Excel2pdf.pdf'
#                 return response

#         return view_func(request, *args, **kwargs)  # Continue with the original view function

#     return wrapper_function

# @excel_to_pdf_logic
# def excel_to_pdf_view(request):
#     meta = Meta(
#         title='iLovePdfConverterOnline - Excel to PDF file Converter',
#         description='Convert Excel file in to JPEG image. PDF pages will be converted to images.',
#         keywords=['png', 'image', 'jpg', 'jpeg'],
#         og_title='iLovePdfConverterOnline - PDF to JPG|JPEG|PNG Image',
#         og_description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
#     )
#     context = {'meta': meta}
    
#     return render(request, 'tools/excel_to_pdf.html', context)

# @excel_to_pdf_logic
# def excel_to_pdf_include(request):

#     return render(request, 'tools/excel_to_pdf_include.html', context)



#Working for XLSX, XLSM, XLTX XLTM including XLS & CSV (created with Excel but not Downloaded)
# def excel_to_pdf_logic(view_func):
#     def wrapper_function(request, *args, **kwargs):
#         if request.method == 'POST' and request.FILES.get('excel_file'):
#             excel_file = request.FILES['excel_file']
#             file_name = excel_file.name.lower()
#             file_extension = os.path.splitext(file_name)[1]

#             # Save uploaded file to MEDIA_ROOT
#             file_path = os.path.join(settings.MEDIA_ROOT, excel_file.name)
#             with open(file_path, 'wb') as destination:
#                 for chunk in excel_file.chunks():
#                     destination.write(chunk)

#             # Create PDF
#             pdf_path = os.path.join(settings.MEDIA_ROOT, 'output.pdf')
#             c = canvas.Canvas(pdf_path, pagesize=landscape(letter))

#             top_margin = 0.5 * inch
#             left_margin = 0.5 * inch
#             bottom_margin = 0.5 * inch
#             right_margin = 0.5 * inch

#             page_width, page_height = landscape(letter)

#             cell_height = 20
#             font_size = 10  # Starting font size
#             font = 'Helvetica'  # Font family

#             if file_extension in ['.xlsx', '.xlsm', '.xltx', '.xltm']:
#                 workbook = load_workbook(file_path)
#                 worksheet = workbook.active
#                 max_row = worksheet.max_row
#                 max_column = worksheet.max_column
#                 ws_range = worksheet.iter_rows(values_only=True)
#             elif file_extension == '.xls':
#                 workbook = open_workbook(file_path)
#                 worksheet = workbook.sheet_by_index(0)
#                 max_row = worksheet.nrows
#                 max_column = worksheet.ncols
#                 ws_range = (worksheet.row_values(row) for row in range(max_row))
#             elif file_extension == '.csv':
#                 with open(file_path, newline='') as csvfile:
#                     reader = csv.reader(csvfile)
#                     data = list(reader)
#                     max_row = len(data)
#                     max_column = len(data[0]) if max_row > 0 else 0
#                     ws_range = iter(data)
#             else:
#                 return HttpResponse("Unsupported file type.", content_type="text/plain")

#             cell_width = (page_width - left_margin - right_margin) / max_column
#             max_text_width = cell_width - 2  # Subtracting a bit for padding

#             y = page_height - top_margin  # Initial y position

#             for row in ws_range:
#                 for col_num, cell in enumerate(row):
#                     x = left_margin + col_num * cell_width
#                     text = str(cell)
#                     current_font_size = font_size
#                     while c.stringWidth(text, font, current_font_size) > max_text_width and current_font_size > 1:
#                         current_font_size -= 1
#                     c.setFont(font, current_font_size)
#                     c.drawString(x, y, text)
                
#                 y -= cell_height
                
#                 if y < bottom_margin:
#                     c.showPage()
#                     y = page_height - top_margin

#             c.save()

#             # Provide the PDF file for download
#             with open(pdf_path, 'rb') as pdf_file:
#                 response = HttpResponse(pdf_file.read(), content_type='application/pdf')
#                 response['Content-Disposition'] = 'attachment; filename=output.pdf'
#                 return response

#         return view_func(request, *args, **kwargs)  # Continue with the original view function

#     return wrapper_function

# @excel_to_pdf_logic
# def excel_to_pdf_view(request):
#     return render(request, 'tools/excel_to_pdf.html')

# @excel_to_pdf_logic
# def excel_to_pdf_include(request):
#     return render(request, 'tools/excel_to_pdf_include.html')


# def convert_to_pdf(xml_content, remove_tags=False):
#     """Converts XML content to PDF with an optional flag to remove HTML tags.

#     Args:
#         xml_content (str): The XML content to be converted.
#         remove_tags (bool, optional): If True, removes HTML tags from the output PDF. Defaults to False.

#     Returns:
#         bytes: The generated PDF content.
#     """

#     if remove_tags:
#         # Escape special characters to prevent them from being interpreted as HTML tags
#         escaped_content = xml_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
#         html_content = f"<html><body><pre>{escaped_content}</pre></body></html>"
#     else:
#         html_content = f"<html><body><pre>{xml_content}</pre></body></html>"

#     # Generate PDF using pdfkit
#     pdf = pdfkit.from_string(html_content, False)
#     return pdf



# def xml_to_pdf(request):
#     if request.method == 'POST':
#         xml_content = request.POST.get('xml_content', '')

#         # If a file is uploaded, read its content
#         if 'xml_file' in request.FILES:
#             xml_file = request.FILES['xml_file']
#             xml_content = xml_file.read().decode('utf-8')

#         # Get the option to remove HTML tags from the request (if provided)
#         remove_tags = request.POST.get('remove_tags', False) in ['on', 'true', '1']

#         # Convert XML to PDF with the chosen option
#         pdf_content = convert_to_pdf(xml_content, remove_tags)
#         # Send PDF as downloadable response
#         response = HttpResponse(pdf_content, content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename="XML_to_PDF.pdf"'
#         return response

#     else:
#         # Render the template with an optional checkbox for removing tags
#         context = {
#             'remove_tags_checked': ''  # Set to 'checked' if desired by default
#         }
#         return render(request, 'tools/xml_to_pdf.html', context)




# views.py


# def pdf_to_xml(request):
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             pdf_file = request.FILES['file']
#             # Create a BytesIO object to store the XML content
#             xml_output = BytesIO()

#             # Convert the PDF to XML and write it to the BytesIO object
#             extract_text_to_fp(pdf_file, xml_output, output_type='xml')

#             # Seek to the beginning of the BytesIO object
#             xml_output.seek(0)

#             # Read the XML content from the BytesIO object
#             xml_content = xml_output.read()

#             # Close the BytesIO object
#             xml_output.close()

#             response = HttpResponse(xml_content, content_type='application/xml')
#             response['Content-Disposition'] = 'attachment; filename=PDF_to_XML.xml'
#             return response
#     else:
#         form = UploadFileForm()
#     return render(request, 'tools/pdf_to_xml.html', {'form': form})



# def pdf_to_json(request):
#     if request.method == 'POST' and 'pdf_file' in request.FILES:
#         pdf_file = request.FILES['pdf_file']
#         try:
#             # Save the uploaded PDF file
#             with open('uploaded_pdf.pdf', 'wb') as destination:
#                 for chunk in pdf_file.chunks():
#                     destination.write(chunk)
            
#             # Read PDF file and extract text
#             with open('uploaded_pdf.pdf', 'rb') as file:
#                 pdf_reader = PyPDF2.PdfReader(file)
#                 text = ""
#                 for page_num in range(len(pdf_reader.pages)):
#                     text += pdf_reader.pages[page_num].extract_text()
            
#             # Convert extracted text to JSON format
#             json_data = json.loads(text)

#             # Save JSON data to a file
#             with open('PDF_to_JSON.json', 'w') as json_file:
#                 json.dump(json_data, json_file, indent=4)
#             return FileResponse(open('PDF_to_JSON.json', 'rb'), as_attachment=True)
#             #return HttpResponse("PDF file converted to JSON successfully. <a href='/output_json.json' download>Download JSON file</a>")
#         except Exception as e:
#             logger.error(f"Conversion failed. Error: {e}")
#             logger.error(traceback.format_exc())
#             return HttpResponse("Conversion failed. An error occurred during conversion.")
#     else:
#         return render(request, 'tools/pdf_to_json.html')



# def string_to_base64_view(request):
#     context = {}
    
#     if request.method == "POST":
#         original_string = request.POST.get("original_string")
#         if original_string:
#             base64_string = base64.b64encode(original_string.encode()).decode()
#             context['base64_string'] = base64_string
#             context['original_string'] = original_string
    
#     return render(request, 'tools/string_to_base64.html', context)

