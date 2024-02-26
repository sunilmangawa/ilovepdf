from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('pdf_to_docx_converter/', views.pdf_to_docx_converter_View, name='pdf_to_docx_converter'),
    
    path('lorem_ipsum_generator/', views.lorem_ipsum_generator, name='lorem_ipsum_generator'),

    path('convert-pdf-to-jpg/', views.convert_pdf_to_jpg_view, name='convert_pdf_to_jpg'),

    path('convert-pdf-to-ppt-pptx/', views.convert_pdf_to_ppt_pptx_view, name='convert_pdf_to_ppt_pptx'),


    path('merge-pdf/', views.merge_pdf_view, name='merge_pdf'),



    path('split-pdf/', views.split_pdf_View, name='split_pdf'),
    path('compress-pdf/', views.compress_pdf_View, name='compress_pdf'),

    # To PDF ...Conversion 
    path('jpg-to-pdf/', views.jpg_to_pdf_View, name='jpg_to_pdf'),
    path('image-to-pdf/', views.img_to_pdf, name='img_to_pdf'),

    # path('download/<int:pdf_id>/', views.download_pdf, name='download_pdf'),


    path('word-to-pdf/', views.word_to_pdf_View, name='word_to_pdf'),

    path('powerpoint_to_pdf/', views.powerpoint_to_pdf_View, name='powerpoint_to_pdf'),


    
    path('excel-to-pdf/', views.excel_to_pdf_View, name='excel_to_pdf'),

    path('html-to-pdf/', views.html_to_pdf_view, name='html_to_pdf'),

    # PDF to ...Conversion 
    path('pdf-to-jpg/', views.pdf_to_jpg_View, name='pdf_to_jpg'),

    path('pdf-to-word/', views.pdf_to_word_View, name='pdf_to_word'),

    path('pdf_to_powerpoint/', views.pdf_to_powerpoint_View, name='pdf_to_powerpoint'),
    path('pdf_to_excel/', views.pdf_to_excel_View, name='pdf_to_excel'),
    path('pdf_to_html/', views.pdf_to_html_View, name='pdf_to_html'),

    
]

