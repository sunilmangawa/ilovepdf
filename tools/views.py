# tools/views.py

# Django default libraries import
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.signals import request_finished
from django.dispatch import receiver
from django.forms import Form
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import render, redirect
from django.template import TemplateDoesNotExist
from django.utils.text import slugify
from django.urls import reverse
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from PyPDF2 import PdfReader, PdfWriter
# Models Import
from .models import ToolAttachment#, ConvertedPDF
from blog.models import Post

# Forms Import
from .forms import PDFUploadForm, RotatePDFForm

# from .tools.word_counter import word_counter_text
from .extra.split_pdf import split_pdf_by_page
from .extra.lorem_ipsum_generator import generate_lorem_ipsum

from .pdfto.pdf_to_docx_converter import pdf_to_docx_converter
from .pdfto.pdf_to_jpg_converter import convert_pdf_to_jpg, clean_up_jpg_files, create_zip_archive
# from .pdfto.pdf_to_ppt_pptx_converter import convert_pdf_to_pptx, create_ppt_slide, clean_up_temp_files, create_zip_archives

from .topdf.excel_to_pdf_converter import convert_excel_to_pdf
from .topdf.imgtopdf import convert_to_pdf
from .topdf.powerpoint_to_pdf_converter import convert_ppt_to_pdf
from .topdf.word_to_pdf_converter import convert_word_to_pdf, clean_temp_files

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
def merge_pdf_View(request):
    meta = Meta(
        title='Merge PDF files free online',
        description='Merge PDF or Combine PDF in Order you want just within clicks.',
        keywords=['merge', 'combine', 'join', 'add'],
        og_title='Merge PDF files free online',
        og_description='Merge PDF or Combine PDF in Order you want just within clicks.',
    )
    tool_attachment = ToolAttachment.objects.get(function_name='merge_pdf_View')
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

# def download_pdf(request):
#     # This view will serve the merged PDF; 
#     # implement according to how you store or pass the merged PDF file
#     pass


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


def word_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
        if request.method == "POST" and request.FILES.get('word_file'):
            word_file = request.FILES['word_file']

            # ... (Your temp file generation and validation)
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
            print(f'output_file_name: {output_file_name}')
            output_pdf_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', output_file_name)
            print(f'output_pdf_path: {output_pdf_path}')

            # Convert the Word file to PDF 
            convert_word_to_pdf(temp_file_path, output_pdf_path) 
            if not os.path.exists(output_pdf_path):
                print(f"Output PDF file not created: {output_pdf_path}")
            # Clean up temporary file
            clean_temp_files(temp_file_path)

            # Serve the PDF file for download
            with open(output_pdf_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={output_file_name}'
                return response
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
    tool_attachment = ToolAttachment.objects.get(function_name='word_to_pdf_View')
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
    return render(request, 'tools/word_to_pdf_include.html')



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
    context = {'meta': meta}
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


def image_to_pdf_logic(view_func):
    def wrapper_function(request, *args, **kwargs):
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

            pdf_data = img2pdf.convert(image_paths)
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="JPG_to_PDF_iLovePDFconverteronline.com.pdf"'
            
            for image_path in image_paths:
                os.remove(image_path)
            os.rmdir(temp_directory)

            return response
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
        meta = Meta(
            title='PDF to JPEG Converter Online',
            description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
            keywords=['png', 'image', 'jpg', 'jpeg'],
            og_title='PDF to JPEG Converter Online',
            og_description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
        )
        context = {'meta': meta}
        return render(request, 'tools/pdf_to_image.html', context)

    return wrapper_function

@pdf_to_image_decorator
def pdf_to_image_view(request):
    # meta = Meta(
    #     title='iLovePdfConverterOnline - PDF to JPG|JPEG|PNG Image',
    #     description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
    #     keywords=['png', 'image', 'jpg', 'jpeg'],
    #     og_title='iLovePdfConverterOnline - PDF to JPG|JPEG|PNG Image',
    #     og_description='Convert PDF file in to JPEG image. PDF pages will be converted to images.',
    # )
    # context = {'meta': meta}
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

    context = {'meta': meta}
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




# ------------------------CHECKED


def compress_pdf_View(request):
    context = {
    }
    return render(request, template_name='tools/compress_pdf.html')




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



# def convert_pdf_to_ppt_pptx_view(request):


#     return render(request, 'tools/pdf_to_ppt_pptx.html')




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


# def powerpoint_to_pdf_View(request):
#     return render(request, template_name='tools/powerpoint_to_pdf.html')

# not working
def powerpoint_to_pdf_View(request):
    if request.method == 'POST' and request.FILES.get('ppt_file'):
        ppt_file = request.FILES['ppt_file']

        # Save the uploaded file temporarily
        with open(os.path.join(settings.MEDIA_ROOT, 'temp.pptx'), 'wb+') as temp_file:
            for chunk in ppt_file.chunks():
                temp_file.write(chunk)

        # Inside your view, before calling convert_ppt_to_pdf
        temp_file_path = os.path.join(settings.MEDIA_ROOT, 'temp.pptx')
        print(f"Saving uploaded file to: {temp_file_path}")  # Verify this path is correct

        with open(temp_file_path, 'wb+') as temp_file:
            for chunk in ppt_file.chunks():
                temp_file.write(chunk)

        # Verify the file exists
        assert os.path.exists(temp_file_path), f"File does not exist at {temp_file_path}"
        print(f"File successfully saved at {temp_file_path}, proceeding to conversion.")

        # Convert the temporary file to PDF
        pdf_path = convert_ppt_to_pdf(os.path.join(settings.MEDIA_ROOT, 'temp.pptx'))


        # Return the PDF file as a response
        with open(pdf_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="converted.pdf"'
            return response

        # Delete the temporary file
        os.remove(os.path.join(settings.MEDIA_ROOT, 'temp.pptx'))

    return render(request, 'tools/powerpoint_to_pdf.html')

def excel_to_pdf_View(request):
    return render(request, template_name='tools/excel_to_pdf.html')

# def excel_to_pdf_View(request):
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

# def pdf_to_powerpoint_View(request):
#     if request.method == 'POST':
#         pdf_file = request.FILES.get('pdf_file')
#         output_folder = "media/pdf_to_ppt_pptx/"

#         # Read the content of the uploaded PDF file
#         pdf_content = pdf_file.read()

#         # Convert PDF to PPT/PPTX
#         ppt_paths = convert_pdf_to_ppt_pptx(BytesIO(pdf_content), output_folder)

#         # Create a zip file containing all PowerPoint files
#         zip_file_path = os.path.join(output_folder, "output_slides.zip")
#         create_zip_archives(ppt_paths, zip_file_path)

#         # Clean up temporary PowerPoint files
#         clean_up_temp_files(ppt_paths)

#         # Use FileResponse directly without manually opening the file
#         response = FileResponse(open(zip_file_path, 'rb'))
#         response['Content-Disposition'] = 'attachment; filename="output_slides.zip"'
#         return response

#     meta = Meta(
#         title='iLovePdfConverterOnline - PDF to JPG| JPEG Image',
#         description='Convert PDF in to JPG| JPEG Image file. PDF will be converted to Image.',
#         keywords=['png', 'image', 'jpg', 'jpeg'],
#         og_title='iLovePdfConverterOnline - PDF to JPG| JPEG Image',
#         og_description='Convert PDF in to JPG| JPEG Image file. PDF will be converted to Image.',

#     )

#     context = {'meta': meta}
#     return render(request, template_name='tools/pdf_to_powerpoint.html')

def pdf_to_powerpoint_View(request):
    # if request.method == 'POST':
    #     pdf_file = request.FILES.get('pdf_file')
    #     output_folder = "media/pdf_to_ppt_pptx/"

    #     # Read the content of the uploaded PDF file
    #     pdf_content = pdf_file.read()

    #     # Convert PDF to PPT/PPTX
    #     ppt_paths = convert_pdf_to_pptx(pdf_content, output_folder)

    #     # Create a zip file containing all PowerPoint files
    #     zip_file_path = os.path.join(output_folder, "output_slides.zip")
    #     create_zip_archives(ppt_paths, zip_file_path)

    #     # Clean up temporary PowerPoint files
    #     clean_up_temp_files(ppt_paths)

    #     # Use FileResponse directly without manually opening the file
    #     response = FileResponse(open(zip_file_path, 'rb'))
    #     response['Content-Disposition'] = 'attachment; filename="output_slides.zip"'
    #     return response

    # meta = Meta(
    #     title='iLovePdfConverterOnline - PDF to ppt | pptx Powerpoint slide',
    #     description='Convert PDF to ppt | pptx Powerpoint slide file. PDF will be converted to Powerpoint slide.',
    #     keywords=['pdf', 'ppt', 'pptx', 'powerpoint', 'power point'],
    #     og_title='iLovePdfConverterOnline - PDF to ppt | pptx Powerpoint slide',
    #     og_description='Convert PDF to ppt | pptx Powerpoint slide. PDF will be converted to Powerpoint slide.',

    # )

    # context = {'meta': meta}
    return render(request, template_name='tools/pdf_to_powerpoint.html')

def pdf_to_excel_View(request):
    return render(request, template_name='tools/pdf_to_excel.html')

# def rotate_pdf_View(request):
#     return render(request, template_name='tools/rotate_pdf.html')


# def rotatePDF(request):
#     if request.method == 'POST' and request.FILES['pdf_file']:
#         pdf_file = request.FILES['pdf_file']

#         # Check if uploaded file is PDF
#         if not pdf_file.name.endswith('.pdf'):
#             return HttpResponse('Please upload a PDF file.')

#         # Read uploaded PDF file
#         pdf_reader = PdfReader(pdf_file)
#         pdf_writer = PdfWriter()

#         # Get rotation angle from form
#         rotation = request.POST.get('rotation', '0')
#         rotation = int(rotation)

#         # Get page ranges to rotate
#         page_ranges = request.POST.get('page_ranges', '').split(',')
#         pages_to_rotate = set()
#         for page_range in page_ranges:
#             if '-' in page_range:
#                 start, end = map(int, page_range.split('-'))
#                 pages_to_rotate.update(range(start - 1, end))
#             else:
#                 pages_to_rotate.add(int(page_range) - 1)

#         # Rotate specified pages
#         for page_num in range(pdf_reader.numPages):
#             page = pdf_reader.getPage(page_num)
#             if page_num in pages_to_rotate:
#                 page.rotateClockwise(rotation)
#             pdf_writer.addPage(page)

#         # Save rotated PDF to BytesIO buffer
#         output_buffer = BytesIO()
#         pdf_writer.write(output_buffer)
#         output_buffer.seek(0)

#         # Return rotated PDF as response
#         response = HttpResponse(output_buffer.read(), content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{pdf_file.name}"'
#         return response

#     return render(request, 'rotate_pdf.html')


# def rotate_pdf_View(request):
#     if request.method == 'POST' and request.FILES['pdf_file']:
#         pdf_file = request.FILES['pdf_file']

#         # Check if uploaded file is PDF
#         if not pdf_file.name.endswith('.pdf'):
#             return HttpResponse('Please upload a PDF file.')

#         # Read uploaded PDF file
#         pdf_reader = PdfReader(pdf_file)
#         pdf_writer = PdfWriter()

#         # Get rotation angle from form
#         rotation = request.POST.get('rotation', '0')
#         rotation = int(rotation)

#         # Get page ranges to rotate
#         page_ranges = request.POST.get('page_ranges', '').split(',')
#         pages_to_rotate = set()
#         for page_range in page_ranges:
#             if '-' in page_range:
#                 start, end = map(int, page_range.split('-'))
#                 pages_to_rotate.update(range(start - 1, end))
#             else:
#                 pages_to_rotate.add(int(page_range) - 1)

#         # Rotate specified pages
#         for page_num in range(pdf_reader.numPages):
#             page = pdf_reader.getPage(page_num)
#             if page_num in pages_to_rotate:
#                 page.rotateClockwise(rotation)
#             pdf_writer.addPage(page)

#         # Save rotated PDF to BytesIO buffer
#         output_buffer = BytesIO()
#         pdf_writer.write(output_buffer)
#         output_buffer.seek(0)

#         # Return rotated PDF as response
#         response = HttpResponse(output_buffer.read(), content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{pdf_file.name}"'
#         return response

#     return render(request, 'tools/rotate_pdf.html')


def rotate_pdf_View(request):
    if request.method == 'POST':
        form = RotatePDFForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES['pdf_file']
            rotation = request.POST.get('rotation')
            page_ranges = request.POST.get('page_ranges')

            pdf_pages = PdfReader(pdf_file)
            output_pdf = PdfWriter()

            if not page_ranges:  # If page_ranges is empty, rotate all pages
                pages_to_rotate = range(pdf_pages.numPages)
            else:
                pages_to_rotate = set()
                for page_range in page_ranges.split(','):
                    if '-' in page_range:
                        start, end = map(int, page_range.split('-'))
                        pages_to_rotate.update(range(start - 1, end))
                    else:
                        pages_to_rotate.add(int(page_range) - 1)

            for page_number in range(pdf_pages.numPages):
                page = pdf_pages.getPage(page_number)
                if page_number in pages_to_rotate:
                    if rotation == 'clockwise':
                        page.rotateClockwise(90)
                    elif rotation == 'anticlockwise':
                        page.rotateCounterClockwise(90)
                    elif rotation == '180':
                        page.rotateClockwise(180)
                output_pdf.addPage(page)

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="rotated_pdf.pdf"'
            output_pdf.write(response)
            return response
    else:
        form = RotatePDFForm()
    return render(request, 'tools/rotate_pdf.html', {'form': form})









# def merge_pdf_view(request):
#     if request.method == "POST":
#         files = request.FILES.getlist('pdf_files')
#         if len(files) == 0:
#             return HttpResponse("No files uploaded.", status=400)

#         merger = PdfMerger()
#         try:
#             # Iterate through files in the order they were uploaded
#             for file in files:
#                 merger.append(file)

#             # Create a response
#             response = HttpResponse(content_type='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename="merged_file.pdf"'

#             # Write the merged PDF to the response
#             merger.write(response)
#             merger.close()

#             return response

#         except Exception as e:
#             # Handle errors if something goes wrong
#             return HttpResponse(str(e), status=500)

#     else:
#         return render(request, 'tools/merge_pdf.html')


# 100% working
# def split_pdf_View(request):
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             file = request.FILES['file']
#             page_numbers = request.POST.get('page_numbers', '')
#             output_files = split_pdf_by_page(file, page_numbers)
#             # Serve the files for download
#             response = HttpResponse(content_type='application/zip')
#             zip_file = zipfile.ZipFile(response, 'w')
#             for output_file in output_files:
#                 zip_file.write(output_file, os.path.basename(output_file))
#             zip_file.close()
#             response['Content-Disposition'] = f'attachment; filename={smart_str(file.name)}.zip'
#             return response
#     else:
#         form = UploadFileForm()
#     meta = Meta(
#         title='iLovePdfConverterOnline - Split PDF',
#         description='Split PDF or Unmerge PDF in Order you want just within clicks.',
#         keywords=['split', 'unmerge', 'remove'],
#         og_title='iLovePdfConverterOnline - Split PDF',
#         og_description='Split PDF or Unmerge PDF in Order you want just within clicks.',

#     )
#     context = {'meta': meta}

#     return render(request, 'tools/split_pdf.html', {'form': form})

# def word_to_pdf_View(request):
#     if request.method == 'POST' and request.FILES.get('word_file'):
#         word_file = request.FILES['word_file']

#         # Generate a unique temporary file name (optional)
#         import uuid 
#         temp_filename = f"{uuid.uuid4()}.docx"
#         temp_file_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', temp_filename)

#         # Save the uploaded Word file to the media directory
#         with open(temp_file_path, 'wb') as temp_file:
#             for chunk in word_file.chunks():
#                 temp_file.write(chunk)

#         # Generate the output PDF file name (with renaming)
#         output_file_name = word_file.name.replace(' ', '_').replace('.docx', '.pdf').replace('.doc', '.pdf').replace('.txt', '.pdf')
#         output_pdf_path = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf', output_file_name)

#         # Convert the Word file to PDF 
#         convert_word_to_pdf(temp_file_path, output_pdf_path) 

#         # Clean up temporary file
#         clean_temp_files(temp_file_path)

#         # Serve the PDF file for download
#         with open(output_pdf_path, 'rb') as pdf_file:
#             response = HttpResponse(pdf_file.read(), content_type='application/pdf')
#             response['Content-Disposition'] = f'attachment; filename={output_file_name}'
#             return response

#     # all_keywords = ['word', 'pdf',  'convert', 'doc', 'docx', 'online converter']
#     meta = Meta(
#         title='Word to PDF converter',
#         description='iLovePdfConverterOnline Convert word document file (doc, docx) to PDF file format',
#         keywords=['word', 'microsoft word', 'doc', 'docx', 'docxtopdf'],
#         # keywords=', '.join(all_keywords),
#         og_title='Word to PDF converter',
#         og_description='iLovePdfConverterOnline Convert word document file (doc, docx) to PDF file format',

#     )

#     tool_attachment = ToolAttachment.objects.get(function_name='word_to_pdf_View')
#     context = {'meta': meta, 'tool_attachment': tool_attachment}     
#     return render(request, 'tools/word_to_pdf.html', context)


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


# def jpg_to_pdf_View(request):
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



# def pdf_to_jpg_View(request):
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





# def pdf_to_word_View(request):
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
    
#     meta = Meta(
#         title='iLovePdfConverterOnline - PDF to Word Document',
#         description='Convert PDF file in to to Word Document. PDF pages will be converted to editable text with same Formatting.',
#         keywords=['word', 'ms word', 'doc', 'docx'],
#         og_title='iLovePdfConverterOnline - PDF to Word Document',
#         og_description='Convert PDF file in to to Word Document. PDF pages will be converted to editable text with same Formatting.',

#     )

#     context = {'meta': meta}

#     return render(request, 'tools/pdf_to_word.html', context)



# 100% Working for static url with post detail
# def pdf_to_word_View(request):
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



# def convert_pdf_to_jpg_view(request):
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
#         title='iLovePdfConverterOnline - PDF to JPG| JPEG Image',
#         description='Convert PDF in to JPG| JPEG Image file. PDF will be converted to Image.',
#         keywords=['png', 'image', 'jpg', 'jpeg'],
#         og_title='iLovePdfConverterOnline - PDF to JPG| JPEG Image',
#         og_description='Convert PDF in to JPG| JPEG Image file. PDF will be converted to Image.',

#     )

#     context = {'meta': meta}

#     return render(request, 'convert_pdf_to_jpg.html')

