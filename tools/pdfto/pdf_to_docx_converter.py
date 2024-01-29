# tools/pdfto/pdf_to_docx_converter.py

from pdf2docx import Converter, parse
from PyPDF2 import PdfReader, PdfWriter

def pdf_to_docx_converter(pdf_file_path, output_docx_path):
    try:
        # Convert the PDF file to DOCX
        cv = Converter(pdf_file_path)
        cv.convert(output_docx_path)
        cv.close()
        return True, None
    except Exception as e:
        return False, str(e)
