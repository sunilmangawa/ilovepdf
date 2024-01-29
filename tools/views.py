# converter/views.py
from django.shortcuts import render
from pdf2docx import Converter
from .models import ToolAttachment

from django.http import HttpResponse, JsonResponse
from blog.models import Post
# from blog.views import BlogDetailView
from django.views import View
from django.template import TemplateDoesNotExist

from .pdfto.pdf_to_docx_converter import pdf_to_docx_converter
# from .tools.word_counter import word_counter_text
from .extra.lorem_ipsum_generator import generate_lorem_ipsum


# Create your views here.

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
    return render(request, 'pdf_to_docx_converter.html')


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

