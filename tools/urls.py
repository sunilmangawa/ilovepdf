from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [

    path('merge-pdf/', views.merge_pdf_view, name='merge_pdf'),
    path('merge-pdf-files/', views.merge_pdf_include, name='merge_pdf_include'),
    
    path('split-pdf/', views.split_pdf_view, name='split_pdf'),
    path('split-pdf-file/', views.split_pdf_include, name='split_pdf_include'),

    path('compress-pdf/', views.compress_pdf_view, name='compress_pdf'),
    path('compress-pdf-file/', views.compress_pdf_include, name='compress_pdf_include'),

    path('rotate-pdf/', views.rotate_pdf_view, name='rotate_pdf'),
    path('rotate-pdf-file/', views.rotate_pdf_include, name='rotate_pdf_include'),

    # To PDF ...Conversion 
    path('jpg-to-pdf/', views.image_to_pdf_view, name='image_to_pdf'),
    path('jpg-to-pdf-file/', views.image_to_pdf_include, name='image_to_pdf_include'),
    # path('image-to-pdf-file/', views.image_to_pdf_include, name='image_to_pdf_include'),

    path('word-to-pdf/', views.word_to_pdf_view, name='word_to_pdf'),
    path('word-to-pdf-file/', views.word_to_pdf_include, name='word_to_pdf_include'),

    path('powerpoint-to-pdf/', views.powerpoint_to_pdf_view, name='powerpoint_to_pdf'),
    path('powerpoint-to-pdf-file/', views.powerpoint_to_pdf_include, name='powerpoint_to_pdf_include'),

    path('excel-to-pdf/', views.excel_to_pdf_view, name='excel_to_pdf'),
    path('excel-to-pdf-file/', views.excel_to_pdf_include, name='excel_to_pdf_include'),

    path('html-to-pdf/', views.html_to_pdf_view, name='html_to_pdf'),
    path('html-to-pdf-file/', views.html_to_pdf_include, name='html_to_pdf_include'),
    
    path('json-to-pdf/', views.json_to_pdf_view, name='json_to_pdf'),
    path('json-to-pdf-file/', views.json_to_pdf_include, name='json_to_pdf_include'),

    path('xml-to-pdf/', views.xml_to_pdf_view, name='xml_to_pdf'),
    path('xml-to-pdf-file/', views.xml_to_pdf_include, name='xml_to_pdf_include'),

    path('base64-to-pdf/', views.base64_to_pdf_view, name='base64_to_pdf'),
    path('base64-to-pdf-file/', views.base64_to_pdf_include, name='base64_to_pdf_include'),

    path('tiff-to-pdf/', views.tiff_to_pdf_view, name='tiff_to_pdf'),
    path('tiff-to-pdf-file/', views.tiff_to_pdf_include, name='tiff_to_pdf_include'),


    # PDF to ...Conversion 
    path('pdf-to-jpg/', views.pdf_to_image_view, name='pdf_to_image'),
    path('pdf-to-jpg-file/', views.pdf_to_image_include, name='pdf_to_image_include'),

    path('pdf-to-word/', views.pdf_to_word_view, name='pdf_to_word'),
    path('pdf-to-word-file/', views.pdf_to_word_include, name='pdf_to_word_include'),

    path('pdf-to-pptx/', views.pdf_to_pptx_view, name='pdf_to_pptx'),
    path('pdf-to-pptx-file/', views.pdf_to_pptx_include, name='pdf_to_pptx_include'),


    path('pdf-to-excel/', views.pdf_to_excel_view, name='pdf_to_excel'),
    path('pdf-to-excel-file/', views.pdf_to_excel_include, name='pdf_to_excel_include'),

    path('pdf-to-csv/', views.pdf_to_csv_view, name='pdf_to_csv'),
    path('pdf-to-csv-file/', views.pdf_to_csv_include, name='pdf_to_csv_include'),

    path('pdf-to-html/', views.pdf_to_html_view, name='pdf_to_html'),
    path('pdf-to-html-file/', views.pdf_to_html_include, name='pdf_to_html_include'),

    path('pdf-to-json/', views.pdf_to_json_view, name='pdf_to_json'),
    path('pdf-to-json-file/', views.pdf_to_json_include, name='pdf_to_json_include'),

    path('pdf-to-xml/', views.pdf_to_xml_view, name='pdf_to_xml'),
    path('pdf-to-xml-file/', views.pdf_to_xml_include, name='pdf_to_xml_include'),

    path('string-to-base64/', views.string_to_base64_view, name='string_to_base64'),
    path('string-to-base64-string/', views.string_to_base64_include, name='string_to_base64_include'),

    path('pdf-to-base64/', views.pdf_to_base64_view, name='pdf_to_base64'),
    path('pdf-to-base64-string/', views.pdf_to_base64_include, name='pdf_to_base64_include'),
    
    path('pdf-to-tiff/', views.pdf_to_tiff_view, name='pdf_to_tiff'),
    path('pdf-to-tiff-file/', views.pdf_to_tiff_include, name='pdf_to_tiff_include'),

    # Extra tools PDF and Others
    path('lorem-ipsum-generator/', views.lorem_ipsum_generator_view, name='lorem_ipsum_generator'),
    path('lorem-ipsum-generator-online/', views.lorem_ipsum_generator_include, name='lorem_ipsum_generator_include'),

    path('word-counter/', views.word_counter_text_view, name='word_counter_text'),
    path('word-counter-tool/', views.word_counter_text_include, name='word_counter_text_include'),

    # Work pending
    # path('pdf-to-psd/', views.pdf_to_psd, name='pdf_to_psd'),

    # path('pdf-to-raw/', views.pdf_to_raw_view, name='pdf_to_raw'),
    # path('raw-to-pdf/', views.raw_to_pdf_view, name='raw_to_pdf'),

    path('odt-to-pdf/', views.odt_to_pdf_view, name='odt_to_pdf_view'),
    path('odt-to-pdf-file/', views.odt_to_pdf_include, name='odt_to_pdf_include'),

    path('ods-to-pdf/', views.ods_to_pdf_view, name='ods_to_pdf'),
    path('ods-to-pdf-file/', views.ods_to_pdf_include, name='ods_to_pdf_include'),

    path('odp-to-pdf/', views.odp_to_pdf_view, name='odp_to_pdf_view'),
    path('odp-to-pdf-file/', views.odp_to_pdf_include, name='odp_to_pdf_include'),

    path('rtf-to-pdf/', views.rtf_to_pdf_view, name='rtf_to_pdf_view'),
    path('rtf-to-pdf-file/', views.rtf_to_pdf_include, name='rtf_to_pdf_include'),

    path('odt-to-docx/', views.odt_to_docx_view, name='odt_to_docx_view'),
    path('odt-to-docx-file/', views.odt_to_docx_include, name='odt_to_docx_include'),

    path('ods-to-xlsx/', views.ods_to_xlsx_view, name='ods_to_xlsx_view'),
    path('ods-to-xlsx-file/', views.ods_to_xlsx_include, name='ods_to_xlsx_include'),

    path('odp-to-pptx/', views.odp_to_pptx_view, name='odp_to_pptx_view'),
    path('odp-to-pptx-file/', views.odp_to_pptx_include, name='odp_to_pptx_include'),

    path('rtf-to-docx/', views.rtf_to_docx_view, name='rtf_to_docx_view'),
    path('rtf-to-docx-file/', views.rtf_to_docx_include, name='rtf_to_docx_include'),

    path('docx-to-rtf/', views.docx_to_rtf_view, name='docx_to_rtf_view'),
    path('docx-to-rtf-file/', views.docx_to_rtf_include, name='docx_to_rtf_include'),

    path('docx-to-odt/', views.docx_to_odt_view, name='docx_to_odt_view'),
    path('docx-to-odt-file/', views.docx_to_odt_include, name='docx_to_odt_include'),

    path('xlsx-to-ods/', views.xlsx_to_ods_view, name='xlsx_to_ods_view'),
    path('xlsx-to-ods-file/', views.xlsx_to_ods_include, name='xlsx_to_ods_include'),

    path('pptx-to-odp/', views.pptx_to_odp_view, name='pptx_to_odp_view'),
    path('pptx-to-odp-include/', views.pptx_to_odp_include, name='pptx_to_odp_include'),




]

