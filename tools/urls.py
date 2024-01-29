from django.urls import path
from . import views

# app_name = 'tools'

urlpatterns = [
    path('pdf_to_docx_converter/', views.pdf_to_docx_converter_View, name='pdf_to_docx_converter'),
    path('lorem_ipsum_generator/', views.lorem_ipsum_generator, name='lorem_ipsum_generator'),
]

