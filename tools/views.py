# tools/views.py

# Django default libraries import
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.signals import request_finished
from django.dispatch import receiver
from django.forms import Form
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseBadRequest, Http404, HttpResponseServerError
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

import base64
import binascii
import docxtopdf
import ghostscript

import img2pdf
import json
import locale
import logging
import pandas as pd
import pdf2image
import pdfkit
import PyPDF2

import os
import re
import requests
import shutil
import subprocess
import tabula
import tempfile
import traceback
import uuid
import warnings
import zipfile



from io import BytesIO
from openpyxl import load_workbook
from pdf2docx import Converter
from pypdf import PdfWriter
from meta.views import Meta
from PyPDF2 import PdfMerger

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.http import require_POST, require_http_methods
from pathlib import Path

from pdfminer.high_level import extract_text_to_fp
from PIL import Image, ImageSequence, ImageOps, UnidentifiedImageError

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, legal
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from functools import wraps

from .topdf.word_to_pdf_converter import convert_to_pdf#, LibreOfficeError, sanitize_filename

# HTML to PDF conversion import
from django.utils.translation import gettext_lazy as _
from .forms import HtmlToPdfForm
from .services.html_to_pdf import PdfConversionError, convert_html_to_pdf, convert_url_to_pdf


#-----
import platform
logger = logging.getLogger(__name__)

# Maximum upload size: 30 MB
MAX_UPLOAD_SIZE = 30 * 1024 * 1024


def get_libreoffice_path():
    """Find the LibreOffice executable path across different OS."""
    if platform.system() == 'Windows':
        # Common Windows installation paths
        candidates = [
            r'C:\Program Files\LibreOffice\program\soffice.exe',
            r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
            os.path.expandvars(r'%PROGRAMFILES%\LibreOffice\program\soffice.exe'),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        # Fall back to command name (might be in PATH)
        return 'soffice'
    else:
        # Linux/macOS — libreoffice is typically in PATH
        return 'libreoffice'




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


# def get_pdf_settings(compress_level):
#     """Returns the Ghostscript PDFSETTINGS parameter based on the compression level."""
#     if compress_level <= 25:
#         return "screen"  # Low quality
#     elif compress_level <= 50:
#         return "ebook"  # Medium quality
#     elif compress_level <= 75:
#         return "printer"  # High quality
#     else:
#         return "prepress"  # Maximum quality

# def compress_pdf_logic(view_func):
#     """Decorator to handle PDF compression via Ghostscript."""
#     def wrapper_function(request, *args, **kwargs):
#         if request.method == 'POST':
#             pdf_file = request.FILES.get('pdf_file')
#             compress_level = int(request.POST.get('compress_level', 50))

#             if pdf_file:
#                 # Use unique filename to avoid conflicts
#                 unique_id = uuid.uuid4().hex
#                 temp_pdf_path = default_storage.save(
#                     f'temp_upload_{unique_id}.pdf',
#                     ContentFile(pdf_file.read())
#                 )
#                 temp_pdf_full_path = os.path.join(
#                     default_storage.location, temp_pdf_path
#                 )
#                 compressed_pdf_path = os.path.join(
#                     settings.MEDIA_ROOT,
#                     f'compressed_{unique_id}.pdf'
#                 )

#                 cargs = [
#                     "ps2pdf",
#                     "-dNOPAUSE", "-dBATCH", "-dSAFER",
#                     "-sDEVICE=pdfwrite",
#                     f"-dCompatibilityLevel=1.4",
#                     f"-dPDFSETTINGS=/{get_pdf_settings(compress_level)}",
#                     f"-sOutputFile={compressed_pdf_path}",
#                     temp_pdf_full_path
#                 ]

#                 encoding = locale.getpreferredencoding()
#                 cargs = [a.encode(encoding) for a in cargs]

#                 try:
#                     ghostscript.Ghostscript(*cargs)
#                 except ghostscript.GhostscriptError as e:
#                     # Clean up temp file on error
#                     default_storage.delete(temp_pdf_path)
#                     return HttpResponse(
#                         f"Error processing file with Ghostscript: {e}",
#                         status=500
#                     )

#                 # Clean up uploaded temp file
#                 default_storage.delete(temp_pdf_path)

#                 # Read compressed file into memory, then delete
#                 try:
#                     with open(compressed_pdf_path, 'rb') as pdf:
#                         pdf_data = pdf.read()
#                     response = HttpResponse(
#                         pdf_data, content_type='application/pdf'
#                     )
#                     response['Content-Disposition'] = (
#                         'attachment; filename="compressed_output.pdf"'
#                     )
#                     return response
#                 finally:
#                     # Delete file after reading into memory
#                     try:
#                         os.remove(compressed_pdf_path)
#                     except OSError:
#                         pass
#         else:
#             return view_func(request, *args, **kwargs)
#     return wrapper_function

# @compress_pdf_logic
# def compress_pdf_view(request):
#     meta = Meta(
#         title='Compress PDF file online',
#         description='Compress PDF to reduce the file size with percentage level.',
#         keywords=['compress', 'reduce', 'small'],
#         og_title='Compress PDF file online',
#         og_description='Compress PDF file online in percentage level you want just within clicks.',
#     )    
#     tool_attachment = ToolAttachment.objects.get(function_name='compress_pdf_view')
#     context = {'meta': meta, 'tool_attachment': tool_attachment}
#     return render(request, 'tools/compress_pdf.html', context)

# @compress_pdf_logic
# def compress_pdf_include(request):
#     meta = Meta(
#         title='Compress PDF file online',
#         description='Compress PDF to reduce the file size with percentage level.',
#         keywords=['compress', 'reduce', 'small'],
#         og_title='Compress PDF file online',
#         og_description='Compress PDF file online in percentage level you want just within clicks.',
#     ) 
#     context = {'meta': meta}
#     return render(request, 'tools/compress_pdf_include.html', context)


# Set this in settings.py as well (shown below).
MAX_PDF_UPLOAD_SIZE = getattr(
    settings,
    "MAX_PDF_UPLOAD_SIZE",
    150 * 1024 * 1024,  # 150 MB
)

PDF_COMPRESSION_TIMEOUT_SECONDS = getattr(
    settings,
    "PDF_COMPRESSION_TIMEOUT_SECONDS",
    180,  # 3 minutes
)

GHOSTSCRIPT_COMMAND = getattr(settings, "GHOSTSCRIPT_COMMAND", "gs")


def get_compression_profile(compress_level: int) -> dict:
    """
    Map UI quality level (10-100) to a Ghostscript profile.

    Lower level = smaller output / lower visual quality.
    Higher level = better visual quality / less compression.
    """
    if compress_level <= 25:
        return {
            "preset": "screen",
            "dpi": 72,
            "jpeg_quality": 40,
        }

    if compress_level <= 50:
        return {
            "preset": "ebook",
            "dpi": 110,
            "jpeg_quality": 55,
        }

    if compress_level <= 75:
        return {
            "preset": "printer",
            "dpi": 150,
            "jpeg_quality": 70,
        }

    return {
        "preset": "prepress",
        "dpi": 220,
        "jpeg_quality": 85,
    }


def is_probably_pdf(uploaded_file) -> bool:
    """
    Basic PDF signature check. This is not a replacement for a malware scanner,
    but it rejects common incorrect uploads before Ghostscript is called.
    """
    try:
        header = uploaded_file.read(1024)
        uploaded_file.seek(0)
        return b"%PDF-" in header
    except Exception:
        return False


def make_download_filename(original_name: str) -> str:
    """
    Make a safe, predictable filename for download.
    """
    stem = Path(original_name).stem or "document"
    safe_stem = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in stem
    ).strip("_")

    return f"{safe_stem or 'document'}_compressed.pdf"


def build_ghostscript_command(input_path: str, output_path: str, level: int) -> list[str]:
    """
    Build Ghostscript command with image compression settings.
    """
    profile = get_compression_profile(level)
    dpi = profile["dpi"]
    jpeg_quality = profile["jpeg_quality"]

    return [
        GHOSTSCRIPT_COMMAND,
        "-dSAFER",
        "-dBATCH",
        "-dNOPAUSE",
        "-dQUIET",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.5",

        # Ghostscript's general preset.
        f"-dPDFSETTINGS=/{profile['preset']}",

        # General PDF optimization.
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        "-dNOPAUSE",
        "-dBATCH",

        # Color images.
        "-dDownsampleColorImages=true",
        "-dColorImageDownsampleType=/Bicubic",
        f"-dColorImageResolution={dpi}",
        f"-dColorImageDownsampleThreshold={dpi / 1.5}",
        f"-dJPEGQ={jpeg_quality}",

        # Grayscale images.
        "-dDownsampleGrayImages=true",
        "-dGrayImageDownsampleType=/Bicubic",
        f"-dGrayImageResolution={dpi}",
        f"-dGrayImageDownsampleThreshold={dpi / 1.5}",

        # Monochrome images.
        "-dDownsampleMonoImages=true",
        "-dMonoImageDownsampleType=/Subsample",
        f"-dMonoImageResolution={min(dpi * 2, 300)}",
        f"-dMonoImageDownsampleThreshold={dpi}",

        f"-sOutputFile={output_path}",
        input_path,
    ]


def compress_uploaded_pdf(uploaded_file, compress_level: int) -> tuple[bytes, bool]:
    """
    Compress a PDF and return:
        (pdf_content, was_compressed)

    Critical behavior:
    If Ghostscript output is not smaller than the input, return the original.
    """
    original_size = uploaded_file.size

    with tempfile.TemporaryDirectory(prefix="pdf_compress_") as temporary_dir:
        input_path = os.path.join(temporary_dir, "input.pdf")
        output_path = os.path.join(temporary_dir, "output.pdf")

        # Stream upload to disk rather than reading the whole PDF into memory.
        with open(input_path, "wb") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        command = build_ghostscript_command(
            input_path=input_path,
            output_path=output_path,
            level=compress_level,
        )

        try:
            completed_process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=PDF_COMPRESSION_TIMEOUT_SECONDS,
                check=False,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Ghostscript is not installed or GHOSTSCRIPT_COMMAND is incorrect."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "Compression took too long. Please try a smaller PDF."
            )

        if completed_process.returncode != 0:
            logger.error(
                "Ghostscript PDF compression failed. Return code: %s. Error: %s",
                completed_process.returncode,
                completed_process.stderr.decode("utf-8", errors="replace")[:2000],
            )
            raise RuntimeError(
                "The PDF could not be processed. It may be corrupted, encrypted, "
                "or contain unsupported content."
            )

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Compression did not produce a valid output file.")

        with open(input_path, "rb") as original_file:
            original_data = original_file.read()

        with open(output_path, "rb") as compressed_file:
            compressed_data = compressed_file.read()

        # Never return a larger file. This is the most important safeguard.
        if len(compressed_data) >= original_size:
            return original_data, False

        return compressed_data, True


def compress_pdf_logic(view_func):
    """
    Reusable decorator for both compress_pdf_view and compress_pdf_include.
    GET renders the normal page; POST returns a PDF download.
    """
    @wraps(view_func)
    def wrapper_function(request, *args, **kwargs):
        if request.method != "POST":
            return view_func(request, *args, **kwargs)

        uploaded_file = request.FILES.get("pdf_file")

        if not uploaded_file:
            return HttpResponseBadRequest("Please select a PDF file.")

        if uploaded_file.size <= 0:
            return HttpResponseBadRequest("The uploaded file is empty.")

        if uploaded_file.size > MAX_PDF_UPLOAD_SIZE:
            return HttpResponseBadRequest(
                f"File is too large. Maximum allowed size is "
                f"{MAX_PDF_UPLOAD_SIZE // (1024 * 1024)} MB."
            )

        if not uploaded_file.name.lower().endswith(".pdf") or not is_probably_pdf(uploaded_file):
            return HttpResponseBadRequest("Only valid PDF files are allowed.")

        try:
            compress_level = int(request.POST.get("compress_level", 50))
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Invalid compression level.")

        compress_level = max(10, min(compress_level, 100))

        original_size = uploaded_file.size

        try:
            pdf_data, was_compressed = compress_uploaded_pdf(
                uploaded_file=uploaded_file,
                compress_level=compress_level,
            )
        except RuntimeError as error:
            return HttpResponseServerError(str(error))
        except Exception:
            logger.exception("Unexpected PDF compression error")
            return HttpResponseServerError(
                "An unexpected error occurred while processing the PDF."
            )

        output_size = len(pdf_data)
        saved_bytes = max(0, original_size - output_size)
        saved_percent = (
            round((saved_bytes / original_size) * 100, 1)
            if original_size
            else 0
        )

        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{make_download_filename(uploaded_file.name)}"'
        )
        response["Content-Length"] = str(output_size)

        # These are used by compress_pdf.html.
        response["X-Original-Size"] = str(original_size)
        response["X-Output-Size"] = str(output_size)
        response["X-Compression-Saved-Bytes"] = str(saved_bytes)
        response["X-Compression-Saved-Percent"] = str(saved_percent)
        response["X-Compression-Status"] = (
            "compressed" if was_compressed else "original-retained"
        )

        return response

    return wrapper_function


@compress_pdf_logic
def compress_pdf_view(request):
    meta = Meta(
        title="Compress PDF file online",
        description="Compress PDF files safely while preserving the original if no reduction is possible.",
        keywords=["compress", "reduce", "small", "pdf"],
        og_title="Compress PDF file online",
        og_description="Reduce PDF file size while preserving quality.",
    )

    tool_attachment = ToolAttachment.objects.filter(
        function_name="compress_pdf_view"
    ).first()

    context = {
        "meta": meta,
        "tool_attachment": tool_attachment,
        "max_upload_mb": MAX_PDF_UPLOAD_SIZE // (1024 * 1024),
    }
    return render(request, "tools/compress_pdf.html", context)


@compress_pdf_logic
def compress_pdf_include(request):
    meta = Meta(
        title="Compress PDF file online",
        description="Compress PDF files safely while preserving the original if no reduction is possible.",
        keywords=["compress", "reduce", "small", "pdf"],
        og_title="Compress PDF file online",
        og_description="Reduce PDF file size while preserving quality.",
    )

    return render(request, "tools/compress_pdf_include.html", {"meta": meta})


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
    """Decorator to handle PDF rotation using PyPDF2."""
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST':
            form = RotatePDFForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    pdf_file = request.FILES['pdf_file']
                    rotation_angle = int(
                        form.cleaned_data['rotation_angle']
                    )
                    pages_to_rotate = form.cleaned_data['pages']

                    # Use PyPDF2 consistently for both reader and writer
                    reader = PyPDF2.PdfReader(pdf_file)
                    writer = PyPDF2.PdfWriter()

                    if pages_to_rotate:
                        pages_to_rotate = parse_page_numbers(
                            pages_to_rotate
                        )
                    else:
                        pages_to_rotate = range(len(reader.pages))

                    for i, page in enumerate(reader.pages):
                        if i in pages_to_rotate:
                            page.rotate(rotation_angle)
                        writer.add_page(page)

                    response = HttpResponse(
                        content_type='application/pdf'
                    )
                    response['Content-Disposition'] = (
                        'attachment; filename="rotated.pdf"'
                    )
                    writer.write(response)
                    return response
                except Exception as e:
                    logger.error(f"Rotate PDF error: {e}")
                    return HttpResponse(
                        f"Error rotating PDF: {str(e)}",
                        status=500
                    )
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

# Working on Server — uses get_libreoffice_path() for cross-platform support

def word_to_pdf_logic(view_func):
    """Decorator to handle Word to PDF conversion via LibreOffice."""
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('word_file'):
            try:
                word_file = request.FILES['word_file']
                
                # Get the original name and strip extension
                original_name = word_file.name
                base_name = os.path.splitext(original_name)[0]
                
                # Use a unique prefix to prevent overwriting files with the same name
                unique_prefix = uuid.uuid4().hex[:8]
                temp_filename = f"{unique_prefix}_{original_name}"
                
                out_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')
                os.makedirs(out_path, exist_ok=True)
                temp_file_path = os.path.join(out_path, temp_filename)

                # Save file
                fs = FileSystemStorage(location=out_path)
                fs.save(temp_filename, word_file)

                env = os.environ.copy()
                env['HOME'] = out_path

                lo_path = get_libreoffice_path()
                subprocess.run(
                    [lo_path, '--headless', '--convert-to', 'pdf',
                     '--outdir', out_path, temp_file_path],
                    env=env, capture_output=True, text=True, check=True
                )

                # The output PDF will match the saved temp_filename but with .pdf
                output_pdf_path = os.path.join(out_path, f"{os.path.splitext(temp_filename)[0]}.pdf")

                if os.path.exists(output_pdf_path):
                    response = FileResponse(
                        open(output_pdf_path, 'rb'),
                        content_type='application/pdf'
                    )
                    # Set the download name back to the original base name + .pdf
                    response['Content-Disposition'] = f'attachment; filename="{base_name}.pdf"'
                    
                    response.cleanup_files = [temp_file_path, output_pdf_path]
                    return response
                else:
                    return HttpResponse("Conversion failed.", status=500)
                    
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
                #for server
                pdf2htmlEX_path = '/usr/local/bin/pdf2htmlEX'  # Full path to pdf2htmlEX
                p = subprocess.run([pdf2htmlEX_path, '--dest-dir', fs.location, uploaded_file_path], check=True)
                
                # for localhost
                # p = subprocess.run(['pdf2htmlEX', '--dest-dir', fs.location, uploaded_file_path])
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

# def image_to_pdf_logic(view_func):
#     def wrapper_function(request, *args, **kwargs):
#         pdf_data=False
#         if request.method == "POST" and request.FILES.getlist('images'):
#             image_files = request.FILES.getlist('images')         
#             temp_directory = os.path.join(settings.MEDIA_ROOT, 'temporary')
#             os.makedirs(temp_directory, exist_ok=True)
            
#             image_paths = []
#             for img_file in image_files:
#                 image_path = os.path.join(temp_directory, img_file.name)
#                 with open(image_path, 'wb') as f:
#                     for chunk in img_file.chunks():
#                         f.write(chunk)
#                 image_paths.append(image_path)
#                 # pdf_data = img2pdf.convert(image_paths)
#             try:
#                 pdf_data = img2pdf.convert(image_paths)
#             except:
#                 os.remove(image_path)
#                 os.rmdir(temp_directory)
#             if pdf_data:
#                 response = HttpResponse(pdf_data, content_type='application/pdf')
#                 response['Content-Disposition'] = 'attachment; filename="Image_to_PDF_iLovePDFconverteronline.com.pdf"'
                
#                 for image_path in image_paths:
#                     os.remove(image_path)
#                 os.rmdir(temp_directory)

#                 return response
#             else:
#                 return render(request, 'tools/image_to_pdf.html')
#         else:
#             return view_func(request, *args, **kwargs)  
#     return wrapper_function

# @image_to_pdf_logic
# def image_to_pdf_view(request):
#     meta = Meta(
#         title='JPG|JPEG|PNG Image to PDF',
#         description='Convert JPG/JPEG Image file in to PDF. Image will be converted to PDF.',
#         keywords=['png', 'image', 'jpg', 'jpeg'],
#         og_title='JPG|JPEG|PNG Image to PDF',
#         og_description='Convert JPG/JPEG Image file in to PDF. Image will be converted to PDF',
#     )
#     tool_attachment = ToolAttachment.objects.get(function_name='image_to_pdf_view')
#     context = {'meta': meta, 'tool_attachment':tool_attachment}
#     return render(request, 'tools/image_to_pdf.html', context) 

# @image_to_pdf_logic
# def image_to_pdf_include(request):
#     meta = Meta(
#         title='Image to PDF',
#         description='Convert image file (jpg, jpeg, png) to PDF file format',
#         keywords=['png', 'image', 'jpg', 'jpeg'],
#         og_title='Image to PDF',
#         og_description='Convert image file (jpg, jpeg, png) to PDF file format',
#     )
#     context = {'meta': meta}
#     return render(request, 'tools/image_to_pdf_include.html')  

# Image to PDF Tool
ALLOWED_IMAGE_TYPES = {"JPEG", "PNG"}
MAX_IMAGE_COUNT = 50
MAX_FILE_SIZE = 50 * 1024 * 1024          # 50 MB per uploaded image
MAX_TOTAL_UPLOAD_SIZE = 250 * 1024 * 1024 # 250 MB per request
MAX_OUTPUT_DIMENSION = 12_000              # pixels, longest edge
MAX_IMAGE_PIXELS = 80_000_000              # reject decompression bombs
JPEG_QUALITY = 90

class ImageToPdfError(Exception):
    """A validation/conversion error that can safely be shown to a visitor."""
    


def _temporary_root():
    """Return a controlled, writable temporary root outside user file names."""
    root = os.path.join(settings.MEDIA_ROOT, "temporary", "image-to-pdf")
    os.makedirs(root, exist_ok=True)
    return root


def _save_upload(upload, destination):
    """Write an UploadedFile in chunks so a source file is never loaded at once."""
    with open(destination, "wb") as target:
        for chunk in upload.chunks(chunk_size=1024 * 1024):
            target.write(chunk)


def _normalise_image(source_path, destination_path):
    """Create a compatible 8-bit JPEG for img2pdf without retaining large RAM.

    img2pdf correctly rejects 16-bit PNGs with alpha channels. Pillow converts
    all accepted input to a standard 8-bit RGB JPEG, flattens transparency onto
    white, applies EXIF rotation, and bounds excessive dimensions.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source_path) as opened:
                if opened.format not in ALLOWED_IMAGE_TYPES:
                    raise ImageToPdfError("Only JPG, JPEG, and PNG images are supported.")
                if opened.width * opened.height > MAX_IMAGE_PIXELS:
                    raise ImageToPdfError("An image is too large to process safely.")

                # load() is deliberate: it exposes malformed/truncated images now,
                # while this one image is the only decoded image in memory.
                opened.load()
                image = ImageOps.exif_transpose(opened)

                # Any alpha channel (including a palette PNG with transparency) is
                # composited instead of being passed to img2pdf as 16-bit alpha.
                has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
                if has_alpha:
                    rgba = image.convert("RGBA")
                    background = Image.new("RGB", rgba.size, "white")
                    background.paste(rgba, mask=rgba.getchannel("A"))
                    image = background
                else:
                    image = image.convert("RGB")

                # Avoid enormous PDF pages and control peak memory for huge photos.
                image.thumbnail(
                    (MAX_OUTPUT_DIMENSION, MAX_OUTPUT_DIMENSION),
                    Image.Resampling.LANCZOS,
                )
                image.save(
                    destination_path,
                    format="JPEG",
                    quality=JPEG_QUALITY,
                    optimize=True,
                    progressive=True,
                )
    except Image.DecompressionBombError as exc:
        raise ImageToPdfError("An image is too large to process safely.") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageToPdfError("One of the uploaded files is not a valid JPG, JPEG, or PNG image.") from exc


def _make_download_response(output_path, download_name, content_type):
    """Stream a disk file and remove it only after Django finishes sending it."""
    response = FileResponse(
        open(output_path, "rb"),
        as_attachment=True,
        filename=download_name,
        content_type=content_type,
    )
    # FileResponse closes its file first. The extra closer then removes this
    # request's output; no periodic cleanup job is required for successful jobs.
    response._resource_closers.append(lambda: os.path.exists(output_path) and os.unlink(output_path))
    return response


def _convert_images_to_response(uploaded_images, conversion_mode):
    """Create a single PDF or a ZIP of individual PDFs using disk, not RAM."""
    if not uploaded_images:
        raise ImageToPdfError("Choose at least one image.")
    if len(uploaded_images) > MAX_IMAGE_COUNT:
        raise ImageToPdfError(f"You can convert up to {MAX_IMAGE_COUNT} images at once.")

    total_size = sum(upload.size for upload in uploaded_images)
    if total_size > MAX_TOTAL_UPLOAD_SIZE:
        raise ImageToPdfError("The combined upload size is too large. Please use 250 MB or less.")

    for upload in uploaded_images:
        if upload.size > MAX_FILE_SIZE:
            raise ImageToPdfError(f'"{upload.name}" is larger than 50 MB.')

    if conversion_mode not in {"single", "multiple"}:
        raise ImageToPdfError("Choose either Single PDF or Multiple PDFs.")

    temporary_root = _temporary_root()
    job_directory = tempfile.mkdtemp(prefix="job-", dir=temporary_root)
    output_path = None

    try:
        normalised_paths = []
        for position, upload in enumerate(uploaded_images, start=1):
            source_path = os.path.join(job_directory, f"source-{position}-{uuid.uuid4().hex}")
            normalised_path = os.path.join(job_directory, f"page-{position}.jpg")
            _save_upload(upload, source_path)
            _normalise_image(source_path, normalised_path)
            normalised_paths.append(normalised_path)

        suffix = ".zip" if conversion_mode == "multiple" else ".pdf"
        descriptor, output_path = tempfile.mkstemp(prefix="image-to-pdf-", suffix=suffix, dir=temporary_root)
        os.close(descriptor)

        if conversion_mode == "single":
            # outputstream avoids img2pdf returning the complete PDF as bytes.
            with open(output_path, "wb") as output_file:
                img2pdf.convert(*normalised_paths, outputstream=output_file)
            return _make_download_response(
                output_path,
                "images-to-pdf.pdf",
                "application/pdf",
            )

        # A browser downloads one file per response, so Multiple PDFs are delivered
        # as one ZIP. Each intermediate PDF is written to disk and released before
        # the next image, which remains stable for large batches.
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for position, normalised_path in enumerate(normalised_paths, start=1):
                individual_pdf = os.path.join(job_directory, f"image-{position}.pdf")
                with open(individual_pdf, "wb") as pdf_file:
                    img2pdf.convert(normalised_path, outputstream=pdf_file)
                archive.write(individual_pdf, arcname=f"image-{position}.pdf")
                os.remove(individual_pdf)

        return _make_download_response(
            output_path,
            "images-to-pdf.zip",
            "application/zip",
        )

    except ImageToPdfError:
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        raise
    except Exception as exc:
        # Keep the diagnostic in server logs; never expose an internal traceback.
        logger.exception("Image-to-PDF conversion failed")
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        raise ImageToPdfError("We could not convert these images. Try fewer or smaller files.") from exc
    finally:
        # Input and normalized files are no longer needed once img2pdf has finished.
        shutil.rmtree(job_directory, ignore_errors=True)


def image_to_pdf_logic(template_name, context_builder):
    """Shared POST handler while preserving separate main/include views."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper_function(request, *args, **kwargs):
            if request.method == "POST":
                try:
                    return _convert_images_to_response(
                        request.FILES.getlist("images"),
                        request.POST.get("conversion_mode", "single"),
                    )
                except ImageToPdfError as exc:
                    context = context_builder()
                    context["conversion_error"] = str(exc)
                    return render(request, template_name, context, status=400)
            return view_func(request, *args, **kwargs)
        return wrapper_function
    return decorator


def _main_image_to_pdf_context():
    meta = Meta(
        title="JPG|JPEG|PNG Image to PDF",
        description="Convert JPG, JPEG, or PNG image files to PDF.",
        keywords=["png", "image", "jpg", "jpeg", "pdf"],
        og_title="JPG|JPEG|PNG Image to PDF",
        og_description="Convert JPG, JPEG, or PNG images to PDF.",
    )
    return {
        "meta": meta,
        "tool_attachment": ToolAttachment.objects.get(function_name="image_to_pdf_view"),
    }


def _include_image_to_pdf_context():
    return {
        "meta": Meta(
            title="Image to PDF",
            description="Convert JPG, JPEG, or PNG image files to PDF.",
            keywords=["png", "image", "jpg", "jpeg", "pdf"],
            og_title="Image to PDF",
            og_description="Convert JPG, JPEG, or PNG images to PDF.",
        )
    }


@image_to_pdf_logic("tools/image_to_pdf.html", _main_image_to_pdf_context)
def image_to_pdf_view(request):
    return render(request, "tools/image_to_pdf.html", _main_image_to_pdf_context())


@image_to_pdf_logic("tools/image_to_pdf_include.html", _include_image_to_pdf_context)
def image_to_pdf_include(request):
    return render(request, "tools/image_to_pdf_include.html", _include_image_to_pdf_context())









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
    """Decorator to handle PDF to Image conversion with JSON response."""
    def wrapper_function(request, *args, **kwargs):
        if request.method == 'POST':
            pdf_file = request.FILES.get('pdf_file')

            if pdf_file:
                try:
                    # Define output folder
                    output_folder = os.path.join(
                        settings.MEDIA_ROOT, "pdf_to_jpg"
                    )
                    os.makedirs(output_folder, exist_ok=True)

                    # Read the uploaded PDF content
                    pdf_content = pdf_file.read()

                    # Convert PDF to JPG images
                    jpg_paths = convert_pdf_to_jpg(
                        BytesIO(pdf_content), output_folder
                    )
                    logger.info(
                        f'Converted PDF to {len(jpg_paths)} images'
                    )

                    image_urls = []
                    for jpg_path in jpg_paths:
                        image_urls.append(
                            request.build_absolute_uri(
                                os.path.join(
                                    settings.MEDIA_URL,
                                    "pdf_to_jpg",
                                    os.path.basename(jpg_path)
                                )
                            )
                        )

                    response = JsonResponse(
                        {'image_urls': image_urls}
                    )
                    # Schedule cleanup after 60 seconds
                    schedule_cleanup(jpg_paths)
                    return response

                except Exception as e:
                    logger.error(f"PDF to Image error: {e}")
                    return JsonResponse(
                        {'error': str(e)},
                        status=500
                    )

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

# Working for server — uses get_libreoffice_path() for cross-platform
def powerpoint_to_pdf_logic(func):
    """Decorator to handle PowerPoint to PDF conversion via LibreOffice."""
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('ppt_file'):
            try:
                ppt_file = request.FILES['ppt_file']
                out_path = os.path.join(
                    settings.MEDIA_ROOT, 'uploads'
                )
                os.makedirs(out_path, exist_ok=True)
                fs = FileSystemStorage(location=out_path)
                filename = fs.save(ppt_file.name, ppt_file)
                file_path = fs.path(filename)

                output_file_path = os.path.join(
                    out_path,
                    os.path.splitext(filename)[0] + '.pdf'
                )

                env = os.environ.copy()
                if platform.system() == 'Windows':
                    env['HOME'] = out_path
                else:
                    env['HOME'] = '/tmp'

                lo_path = get_libreoffice_path()
                result = subprocess.run(
                    [lo_path, '--headless', '--convert-to',
                     'pdf', '--outdir', out_path, file_path],
                    env=env, capture_output=True, text=True
                )
                if result.returncode != 0:
                    raise Exception(
                        f"LibreOffice conversion failed: "
                        f"{result.stderr}"
                    )

                with open(output_file_path, 'rb') as pdf_file:
                    response = HttpResponse(
                        pdf_file.read(),
                        content_type='application/pdf'
                    )
                    response['Content-Disposition'] = (
                        f'attachment; filename='
                        f'{os.path.basename(output_file_path)}'
                    )
                    response.cleanup_files = [
                        file_path, output_file_path
                    ]
                    return response
            except FileNotFoundError:
                return HttpResponse(
                    "LibreOffice is not installed. "
                    "See INSTALL_DEPENDENCIES.md for setup.",
                    status=500
                )
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
#                 try:
#                     with open(file_path, newline='', encoding='utf-8') as csvfile:
#                         reader = csv.reader(csvfile)
#                         data = list(reader)
#                 except UnicodeDecodeError:
#                     return HttpResponse("Unable to decode the CSV file. Please ensure it is encoded in UTF-8.", content_type="text/plain")

#                 max_row = len(data)
#                 max_column = len(data[0]) if max_row > 0 else 0
#                 ws_range = iter(data)
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
#                 response['Content-Disposition'] = 'attachment; filename=Excel2PDF_ilovepdfconverteronline.com.pdf'
#                 response.cleanup_files = [file_path, pdf_path]
#                 return response

#         return view_func(request, *args, **kwargs)  # Continue with the original view function

#     return wrapper_function

# @excel_to_pdf_logic
# def excel_to_pdf_view(request):
#     meta = Meta(
#         title='iLovePdfConverterOnline - Excel to PDF converter',
#         description='Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV file in to PDF file format.',
#         keywords=['XLSX', 'XLSM', 'XLTX', 'XLTM', 'XLS'  'CSV', 'pdf'],
#         og_title='iLovePdfConverterOnline - Excel to PDF converter',
#         og_description='Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV file in to PDF file format.',
#     )    
#     tool_attachment = ToolAttachment.objects.get(function_name='excel_to_pdf_view')
#     context = {'meta': meta, 'tool_attachment': tool_attachment}
#     return render(request, 'tools/excel_to_pdf.html', context)

# @excel_to_pdf_logic
# def excel_to_pdf_include(request):
#     meta = Meta(
#         title='iLovePdfConverterOnline - Excel to PDF converter',
#         description='Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV file in to PDF file format.',
#         keywords=['XLSX', 'XLSM', 'XLTX', 'XLTM', 'XLS'  'CSV', 'pdf'],
#         og_title='iLovePdfConverterOnline - Excel to PDF converter',
#         og_description='Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV file in to PDF file format.',
#     )    
#     context = {'meta': meta}
#     return render(request, 'tools/excel_to_pdf_include.html')


import os
import logging
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

# Import converter (adjust module path based on your folder structure)
try:
    from .topdf.excel_to_pdf_converter import convert_excel_to_pdf
except ImportError:
    from .Topdf.excel_to_pdf_converter import convert_excel_to_pdf

logger = logging.getLogger(__name__)


def excel_to_pdf_logic(view_func):
    """
    Decorator for Excel to PDF conversion views.
    Handles form submission, processes files in-memory without saving temporary files to disk,
    and returns a direct PDF download attachment.
    """
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get("excel_file"):
            excel_file = request.FILES["excel_file"]

            # Extract user configuration options
            options = {
                "orientation": request.POST.get("orientation", "auto"),
                "page_size": request.POST.get("page_size", "letter"),
                "sheet_mode": request.POST.get("sheet_mode", "all"),
                "gridlines": request.POST.get("gridlines", "true").lower() in ["true", "1", "on", "yes"],
                "engine": request.POST.get("engine", "auto"),
            }

            try:
                # Convert completely in-memory (zero files created in MEDIA_ROOT or disk)
                pdf_bytes, output_filename = convert_excel_to_pdf(
                    file_input=excel_file,
                    filename=excel_file.name,
                    options=options
                )

                # Return PDF download response directly
                response = HttpResponse(pdf_bytes, content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="{output_filename}"'
                response["Content-Length"] = len(pdf_bytes)
                return response

            except Exception as e:
                logger.exception("Excel to PDF conversion failed: %s", e)
                # Store error message on request to display alert banner to user
                request.conversion_error = str(e)

        return view_func(request, *args, **kwargs)

    return wrapper_function


@excel_to_pdf_logic
def excel_to_pdf_view(request):
    meta = Meta(
        title="iLovePdfConverterOnline - Excel to PDF converter",
        description="Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV files to high-quality PDF format.",
        keywords=["XLSX", "XLSM", "XLTX", "XLTM", "XLS", "CSV", "TSV", "pdf"],
        og_title="iLovePdfConverterOnline - Excel to PDF converter",
        og_description="Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV files to high-quality PDF format.",
    )
    try:
        tool_attachment = ToolAttachment.objects.get(function_name="excel_to_pdf_view")
    except Exception:
        tool_attachment = None

    context = {
        "meta": meta,
        "tool_attachment": tool_attachment,
        "error": getattr(request, "conversion_error", None),
    }
    return render(request, "tools/excel_to_pdf.html", context)


@excel_to_pdf_logic
def excel_to_pdf_include(request):
    meta = Meta(
        title="iLovePdfConverterOnline - Excel to PDF converter",
        description="Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV files to high-quality PDF format.",
        keywords=["XLSX", "XLSM", "XLTX", "XLTM", "XLS", "CSV", "TSV", "pdf"],
        og_title="iLovePdfConverterOnline - Excel to PDF converter",
        og_description="Convert XLSX, XLSM, XLTX, XLTM, XLS & CSV files to high-quality PDF format.",
    )
    context = {
        "meta": meta,
        "error": getattr(request, "conversion_error", None),
    }
    return render(request, "tools/excel_to_pdf_include.html", context)





# -----------------------------------------================================


# By Gemini 3.8
import io
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pdfplumber
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.utils.text import get_valid_filename
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

PDF_MIME_TYPES = {"application/pdf", "application/x-pdf"}
MAX_PDF_UPLOAD_BYTES = getattr(settings, "PDF_TO_EXCEL_MAX_UPLOAD_BYTES", 25 * 1024 * 1024)

DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%Y/%m/%d",
)

# Common header keywords used to recognize table column headers across business documents
HEADER_KEYWORDS = {
    "id", "no", "num", "number", "code", "name", "title", "desc", "description",
    "item", "product", "qty", "quantity", "rate", "price", "cost", "amount",
    "total", "subtotal", "date", "time", "status", "type", "category", "unit",
    "address", "city", "state", "zip", "country", "phone", "email", "tax",
    "notes", "remarks", "comment", "balance", "debit", "credit", "percent", "%",
    "lead", "budget", "population", "salary", "department", "customer", "sku", "warehouse"
}


class PdfConversionError(Exception):
    """Expected, user-safe PDF-to-Excel conversion error."""


def _pdf_to_excel_context(include=False):
    meta = Meta(
        title="iLovePdfConverterOnline - PDF to XLSX file converter online",
        description="Convert PDF tables to XLSX online.",
        keywords=["pdf", "table", "excel", "xlsx"],
        og_title="iLovePdfConverterOnline - PDF to XLSX file converter online",
        og_description="Convert PDF tables to XLSX online.",
    )
    context = {
        "meta": meta,
        "max_upload_mb": MAX_PDF_UPLOAD_BYTES // (1024 * 1024),
    }
    if not include:
        context["tool_attachment"] = ToolAttachment.objects.filter(
            function_name="pdf_to_excel_view"
        ).first()
    return context


def pdf_to_excel_view(request):
    """Normal PDF-to-Excel page and POST endpoint used by `tools.urls`."""
    if request.method == "POST":
        return handle_pdf_to_excel_upload(request)
    return render(request, "tools/pdf_to_excel.html", _pdf_to_excel_context())


def pdf_to_excel_include(request):
    """Embedded PDF-to-Excel page; uses the same upload handler."""
    if request.method == "POST":
        return handle_pdf_to_excel_upload(request)
    return render(
        request,
        "tools/pdf_to_excel_include.html",
        _pdf_to_excel_context(include=True),
    )


def handle_pdf_to_excel_upload(request):
    """Handle PDF upload, convert tables, and stream XLSX response without leaving temp files."""
    pdf_file = request.FILES.get("pdf_file")
    if not pdf_file:
        return _conversion_error(request, "Choose a PDF file first.")
    if Path(pdf_file.name).suffix.lower() != ".pdf":
        return _conversion_error(request, "Only .pdf files can be converted.")
    if pdf_file.size == 0:
        return _conversion_error(request, "The uploaded file is empty.")
    if pdf_file.size > MAX_PDF_UPLOAD_BYTES:
        limit = MAX_PDF_UPLOAD_BYTES // (1024 * 1024)
        return _conversion_error(request, f"The PDF is too large. The current limit is {limit} MB.")

    try:
        # In-memory buffer: avoids creating any temporary files on disk inside the project
        pdf_stream = io.BytesIO()
        for chunk in pdf_file.chunks():
            pdf_stream.write(chunk)
        pdf_stream.seek(0)

        # Validate PDF magic header
        header = pdf_stream.read(5)
        if not header.startswith(b"%PDF-"):
            raise PdfConversionError("This file is not a valid PDF document.")
        pdf_stream.seek(0)

        # Perform advanced table conversion
        workbook_stream = convert_pdf_to_excel_advanced(pdf_stream)
        safe_stem = get_valid_filename(Path(pdf_file.name).stem) or "converted"
        return FileResponse(
            workbook_stream,
            as_attachment=True,
            filename=f"{safe_stem}.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except PdfConversionError as exc:
        logger.info("PDF-to-Excel conversion rejected: %s", exc)
        return _conversion_error(request, str(exc))
    except Exception:
        logger.exception("Unexpected PDF-to-Excel conversion error")
        return _conversion_error(
            request,
            "We could not convert this PDF. It may be encrypted, damaged, or image-only.",
        )


def _conversion_error(request, message):
    messages.error(request, message)
    return redirect(request.path)


def convert_pdf_to_excel_advanced(pdf_source: Union[str, Path, io.BytesIO, bytes]) -> io.BytesIO:
    """Convert PDF tables to Excel workbook (.xlsx).

    Behavior:
    1. If the table structure is identical across pages (same columns/geometry or matching headers,
       or continuous data like sample-heavy-1.pdf), all rows are merged into ONE single worksheet.
    2. If the PDF contains multiple different table structures (different column counts or different
       headers), each distinct table is saved to its own dedicated worksheet ('Table 1', 'Table 2', etc.).
    3. Repeated headers across continuation pages are automatically deduplicated.
    4. Data types (integers, floats, currency, dates, percentages) are automatically coerced into native
       Excel values, while preserving leading zeros for IDs and postal codes.
    5. Clean professional styling is applied (header fill, freeze pane, auto-filter, auto column widths,
       and grid lines enabled).
    6. Operates entirely in memory or via clean streams with no temporary files left on disk.
    """
    if isinstance(pdf_source, bytes):
        pdf_source = io.BytesIO(pdf_source)

    workbook = Workbook()
    workbook.remove(workbook.active)  # Remove default blank sheet

    # Buckets track distinct table structures across the entire document
    buckets: List[Dict[str, Any]] = []

    try:
        with pdfplumber.open(pdf_source) as pdf:
            if not pdf.pages:
                raise PdfConversionError("The uploaded PDF contains no pages.")

            for page_num, page in enumerate(pdf.pages, start=1):
                extracted_tables = []

                # Strategy 1: Ruled / bordered tables (fast vector line & border analysis)
                tables = page.find_tables()
                if tables:
                    for t in tables:
                        raw_rows = t.extract()
                        if raw_rows:
                            cleaned = [_normalize_row(r) for r in raw_rows if any(c.strip() for c in r)]
                            if cleaned and len(cleaned[0]) >= 2:
                                col_pos = tuple(round(c.bbox[0], 1) for c in t.columns) + (round(t.columns[-1].bbox[2], 1),)
                                extracted_tables.append((cleaned, col_pos))

                # Strategy 2: Borderless / whitespace-aligned tables fallback
                if not extracted_tables:
                    text_tables = page.extract_tables({"vertical_strategy": "text", "horizontal_strategy": "text"})
                    for raw_rows in text_tables:
                        cleaned = [_normalize_row(r) for r in raw_rows if any(c.strip() for c in r)]
                        if cleaned and len(cleaned) >= 2 and len(cleaned[0]) >= 2:
                            extracted_tables.append((cleaned, None))

                # Process all tables detected on this page
                for rows, col_positions in extracted_tables:
                    col_count = len(rows[0])
                    # Pad rows to consistent column count
                    rows = [r + [""] * (col_count - len(r)) for r in rows]
                    has_h, header = _detect_header(rows)

                    # Match with existing table bucket
                    matched = None
                    for b in buckets:
                        if b["col_count"] != col_count:
                            continue

                        # Header match takes highest precedence
                        if has_h and b["has_header"]:
                            if header == b["header"]:
                                matched = b
                                break
                        # Continuation table where continuation page omitted repeated header
                        elif not has_h and b["has_header"]:
                            if (col_positions and _col_positions_match(col_positions, b["col_positions"])) or page_num == b["last_page"] + 1:
                                matched = b
                                break
                        # Both data-only tables without headers (e.g. continuous data tables)
                        elif not has_h and not b["has_header"]:
                            if (col_positions and _col_positions_match(col_positions, b["col_positions"])) or page_num == b["last_page"] + 1:
                                matched = b
                                break

                    # If no matching table structure exists, create a new worksheet bucket
                    if matched is None:
                        table_number = len(buckets) + 1
                        sheet_name = _unique_sheet_name(workbook, f"Table {table_number}")
                        ws = workbook.create_sheet(title=sheet_name)
                        matched = {
                            "ws": ws,
                            "col_count": col_count,
                            "has_header": has_h,
                            "header": header,
                            "col_positions": col_positions,
                            "last_page": page_num,
                            "total_rows": 0,
                        }
                        buckets.append(matched)

                    # Deduplicate repeated header row on continuation pages
                    rows_to_write = rows[1:] if (
                        has_h and matched["has_header"] and matched["total_rows"] > 0 and header == matched["header"]
                    ) else rows

                    # Append coerced cell data to the worksheet
                    for row in rows_to_write:
                        matched["ws"].append([_coerce_cell_value(c) for c in row])

                    matched["total_rows"] += len(rows_to_write)
                    matched["last_page"] = page_num

                # Flush page layout cache to keep memory low during long document processing
                page.flush_cache()

    except PdfConversionError:
        raise
    except Exception as exc:
        logger.exception("Failed to parse PDF document")
        raise PdfConversionError("Could not read or parse this PDF document.") from exc

    # If no tables were detected in the entire document, fall back to extracting selectable text
    if not buckets:
        ws = workbook.create_sheet(title="Extracted Text")
        ws.append(["Page", "Text"])
        with pdfplumber.open(pdf_source) as pdf:
            has_text = False
            for p_num, p in enumerate(pdf.pages, start=1):
                txt = (p.extract_text() or "").strip()
                if txt:
                    ws.append([p_num, txt])
                    has_text = True
        if not has_text:
            raise PdfConversionError(
                "No selectable text or tables were found. This document may be scanned or image-only. Please run OCR first."
            )
        _format_worksheet(ws, has_header=True)
    else:
        for b in buckets:
            _format_worksheet(b["ws"], has_header=b["has_header"])

    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream


def _is_numeric_string(val: Any) -> bool:
    """Check whether a string represents a number (currency, commas, percent stripped)."""
    if not val:
        return False
    s = str(val).strip().replace(",", "").replace("$", "").replace("€", "").replace("£", "").replace("¥", "").replace("₹", "").replace("%", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1].strip()
    try:
        float(s)
        return True
    except ValueError:
        return False


def _coerce_cell_value(val: Any) -> Any:
    """Coerce string values into native Python/Excel types (int, float, date, bool)."""
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""

    s_lower = s.lower()
    if s_lower == "true":
        return True
    if s_lower == "false":
        return False

    # Keep leading-zero numeric strings as text (preserves zip codes, account IDs, serials)
    if re.fullmatch(r"0\d+", s):
        return s

    # Integer
    if re.fullmatch(r"[-+]?\d+", s):
        try:
            val_int = int(s)
            if len(s) < 16:  # Avoid scientific notation overflow for large numeric identifiers
                return val_int
        except ValueError:
            pass

    # Clean currency/commas for numeric float parsing
    clean_num = s.replace(",", "").replace("$", "").replace("€", "").replace("£", "").replace("¥", "").replace("₹", "").strip()
    if clean_num.startswith("(") and clean_num.endswith(")"):
        clean_num = "-" + clean_num[1:-1].strip()

    # Float / Decimal
    if re.fullmatch(r"[-+]?\d+\.\d+", clean_num):
        try:
            return float(clean_num)
        except ValueError:
            pass

    # Percentage: e.g. 15.5% -> 0.155
    if s.endswith("%"):
        pct_clean = s[:-1].strip().replace(",", "")
        if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", pct_clean):
            try:
                return float(pct_clean) / 100.0
            except ValueError:
                pass

    # Date
    if len(s) in (8, 9, 10):
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue

    return s


def _normalize_cell(cell: Any) -> str:
    s = str(cell or "").strip()
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in s.splitlines()]
    return "\n".join(line for line in lines if line)


def _normalize_row(row: List[Any]) -> List[str]:
    return [_normalize_cell(c) for c in row]


def _detect_header(rows: List[List[str]]) -> Tuple[bool, Tuple[str, ...]]:
    """Determine accurately whether rows[0] is a table header or just data.

    Prevents the critical flaw where data rows with text columns (like names or codes)
    are mistakenly treated as headers.
    """
    if not rows or len(rows) < 2:
        return False, ()

    first = rows[0]
    subsequent = rows[1:min(len(rows), 15)]
    first_clean = [re.sub(r"\W+", "", str(c or "")).lower() for c in first]
    kw_matches = sum(1 for c in first_clean if any(k in c for k in HEADER_KEYWORDS))

    type_discrepancy = 0
    identical_type_count = 0

    for col_idx in range(len(first)):
        col_0_num = _is_numeric_string(first[col_idx])
        sub_num = sum(1 for r in subsequent if len(r) > col_idx and _is_numeric_string(r[col_idx]))
        sub_total = len(subsequent)

        # If row 0 is text but subsequent data rows are numeric/dates, strong header indicator
        if not col_0_num and sub_num >= max(1, int(sub_total * 0.7)):
            type_discrepancy += 1
        elif col_0_num and sub_num >= max(1, int(sub_total * 0.7)):
            identical_type_count += 1

    # If row 0 shares the exact same numeric pattern as data rows and no keywords match, it's data
    if identical_type_count > 0 and type_discrepancy == 0 and kw_matches == 0:
        return False, ()

    if type_discrepancy >= 1 or kw_matches >= max(1, len(first) // 2):
        return True, tuple(first_clean)

    return False, ()


def _col_positions_match(pos1: Optional[Tuple[float, ...]], pos2: Optional[Tuple[float, ...]], tol: float = 18.0) -> bool:
    """Compare horizontal column boundaries to verify identical layout structure."""
    if not pos1 or not pos2 or len(pos1) != len(pos2):
        return False
    diffs = [abs(p1 - p2) for p1, p2 in zip(pos1, pos2)]
    return (sum(diffs) / len(diffs)) <= tol


def _unique_sheet_name(workbook: Workbook, preferred: str) -> str:
    """Generate a clean, Excel-compatible unique sheet title (max 31 chars)."""
    cleaned = re.sub(r"[\[\]\*\/\\:]", "", preferred).strip() or "Table"
    base = cleaned[:28]
    candidate = base
    number = 2
    while candidate in workbook.sheetnames:
        suffix = f" ({number})"
        candidate = f"{base[:31 - len(suffix)]}{suffix}"
        number += 1
    return candidate


def _format_worksheet(ws, has_header: bool = False):
    """Apply clean professional Excel styling and auto column widths."""
    ws.views.sheetView[0].showGridLines = True
    if has_header and ws.max_row >= 1:
        ws.freeze_panes = "A2"
        if ws.max_column:
            ws.auto_filter.ref = ws.dimensions

        # Professional navy header
        header_fill = PatternFill("solid", fgColor="1F4E78")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="1F4E78"),
            bottom=Side(style="medium", color="1F4E78"),
        )
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_align
            cell.border = thin_border
        ws.row_dimensions[1].height = 26

    # Efficient column width auto-fitting using sample rows
    sample_limit = min(ws.max_row, 60)
    for col_idx in range(1, ws.max_column + 1):
        col_letter = get_column_letter(col_idx)
        max_len = 10
        for row_idx in range(1, sample_limit + 1):
            val_str = str(ws.cell(row_idx, col_idx).value or "")
            line_max = max((len(line) for line in val_str.splitlines()), default=0)
            if line_max > max_len:
                max_len = line_max
        ws.column_dimensions[col_letter].width = min(max_len + 3, 50)




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
    """Put decoded text (or a validation error) in the template context."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        context = {}

        if request.method == "POST":
            base64_string = request.POST.get("base64_string", "").strip()
            context["base64_string"] = base64_string

            try:
                # Accept Base64 pasted over several lines and optional data-URL prefixes.
                if base64_string.startswith("data:") and "," in base64_string:
                    base64_string = base64_string.split(",", 1)[1]
                normalized_base64 = "".join(base64_string.split())
                padding = "=" * (-len(normalized_base64) % 4)
                decoded_bytes = base64.b64decode(normalized_base64 + padding, validate=True)
                context["decoded_string"] = decoded_bytes.decode("utf-8")
            except (binascii.Error, UnicodeDecodeError, ValueError):
                context["error"] = (
                    "Please enter a valid Base64 value that contains UTF-8 text."
                )

        return view_func(request, context, *args, **kwargs)

    return wrapper


@base64_to_pdf_logic
def base64_to_pdf_view(request, context):
    meta = Meta(
        title="iLovePdfConverterOnline - Base64 to text and PDF converter online",
        description="Decode Base64 text and export the decoded text as a PDF.",
        keywords=["string", "pdf", "base64", "text"],
        og_title="iLovePdfConverterOnline - Base64 to text and PDF converter online",
        og_description="Decode Base64 text and export the decoded text as a PDF.",
    )
    context["meta"] = meta
    context["tool_attachment"] = ToolAttachment.objects.get(
        function_name="base64_to_pdf_view"
    )
    return render(request, "tools/base64_to_pdf.html", context)


@base64_to_pdf_logic
def base64_to_pdf_include(request, context):
    meta = Meta(
        title="iLovePdfConverterOnline - Base64 to text and PDF converter online",
        description="Decode Base64 text and export the decoded text as a PDF.",
        keywords=["string", "pdf", "base64", "text"],
        og_title="iLovePdfConverterOnline - Base64 to text and PDF converter online",
        og_description="Decode Base64 text and export the decoded text as a PDF.",
    )
    context["meta"] = meta
    return render(request, "tools/base64_to_pdf_include.html", context)

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

# HTML to PDF conversion views

def _download_response(pdf: bytes) -> FileResponse:
    from io import BytesIO

    response = FileResponse(
        BytesIO(pdf),
        as_attachment=True,
        filename=settings.HTML_TO_PDF_OUTPUT_FILENAME,
        content_type="application/pdf",
    )
    response["Content-Length"] = len(pdf)
    response["X-Content-Type-Options"] = "nosniff"
    return response


def _render_html_to_pdf(request, template_name: str, include_attachment: bool = False):
    meta = Meta(
        title="iLovePdfConverterOnline - HTML to PDF",
        description="Convert an HTML file or public URL to PDF.",
        keywords=["html", "url", "file", "download", "pdf"],
        og_title="iLovePdfConverterOnline - HTML to PDF",
        og_description="Convert an HTML file or public URL to PDF.",
    )
    context = {"meta": meta, "form": HtmlToPdfForm()}
    if include_attachment:
        context["tool_attachment"] = ToolAttachment.objects.filter(function_name="html_to_pdf_view").first()

    if request.method == "POST":
        form = HtmlToPdfForm(request.POST, request.FILES)
        context["form"] = form
        if form.is_valid():
            try:
                if form.cleaned_data["url"]:
                    pdf = convert_url_to_pdf(form.cleaned_data["url"])
                else:
                    raw_html = form.cleaned_data["html_file"].read()
                    html = raw_html.decode("utf-8-sig")
                    pdf = convert_html_to_pdf(html)
                return _download_response(pdf)
            except UnicodeDecodeError:
                form.add_error("html_file", _("The file must be UTF-8 encoded HTML."))
            except PdfConversionError as exc:
                form.add_error(None, str(exc))

    return render(request, template_name, context)


@require_http_methods(["GET", "POST"])
def html_to_pdf_view(request):
    return _render_html_to_pdf(request, "tools/html_to_pdf.html", include_attachment=True)


@require_http_methods(["GET", "POST"])
def html_to_pdf_include(request):
    return _render_html_to_pdf(request, "tools/html_to_pdf_include.html")


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
    tool_attachment = ToolAttachment.objects.get(function_name='odp_to_pptx_view')
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

# from django.core.files.storage import FileSystemStorage

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

