from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    # path('pdf_to_docx_converter/', views.pdf_to_docx_converter_View, name='pdf_to_docx_converter'),
    
    # path('convert-pdf-to-jpg/', views.convert_pdf_to_jpg_view, name='convert_pdf_to_jpg'),
    # path('convert-pdf-to-ppt-pptx/', views.convert_pdf_to_ppt_pptx_view, name='convert_pdf_to_ppt_pptx'),



    path('merge-pdf/', views.merge_pdf_View, name='merge_pdf'),
    path('merge-pdf-files/', views.merge_pdf_include, name='merge_pdf_include'),
    
    path('split-pdf/', views.split_pdf_view, name='split_pdf'),
    path('split-pdf-file/', views.split_pdf_include, name='split_pdf_include'),

    path('compress-pdf/', views.compress_pdf_View, name='compress_pdf'),


    # To PDF ...Conversion 
    path('jpg-to-pdf/', views.image_to_pdf_view, name='image_to_pdf'),
    path('image-to-pdf-file/', views.image_to_pdf_include, name='image_to_pdf_include'),

    # path('download/<int:pdf_id>/', views.download_pdf, name='download_pdf'),
    path('word-to-pdf/', views.word_to_pdf_view, name='word_to_pdf'),
    path('word-to-pdf-file/', views.word_to_pdf_include, name='word_to_pdf_include'),

    # path('docx-to-pdf/', views.word_to_pdf_view, name='word_to_pdf'),



    path('powerpoint_to_pdf/', views.powerpoint_to_pdf_View, name='powerpoint_to_pdf'), 
    path('excel-to-pdf/', views.excel_to_pdf_View, name='excel_to_pdf'),

    path('html-to-pdf/', views.html_to_pdf_view, name='html_to_pdf'),
    path('html-to-pdf-file/', views.html_to_pdf_include, name='html_to_pdf_include'),


    # PDF to ...Conversion 
    path('pdf-to-jpg/', views.pdf_to_image_view, name='pdf_to_image'),
    path('pdf-to-jpg-file/', views.pdf_to_image_include, name='pdf_to_image_include'),

    path('pdf-to-word/', views.pdf_to_word_view, name='pdf_to_word'),
    path('pdf-to-word-file/', views.pdf_to_word_include, name='pdf_to_word_include'),

    # not working yet
    path('pdf_to_powerpoint/', views.pdf_to_powerpoint_View, name='pdf_to_powerpoint'),
    path('pdf-to-excel/', views.pdf_to_excel_View, name='pdf_to_excel'),
    path('rotate_pdf/', views.rotate_pdf_View, name='rotate_pdf'),

    # Extra tools PDF and Others
    path('lorem_ipsum_generator/', views.lorem_ipsum_generator, name='lorem_ipsum_generator'),

]

