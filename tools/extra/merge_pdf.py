# tools/merger_pdf.py

from PyPDF2 import PdfReader, PdfWriter
import io

def merge_pdfs(paths):
    pdf_writer = PdfWriter()
    
    for path in paths:
        pdf_reader = PdfReader(path)
        for page in range(pdf_reader.getNumPages()):
            pdf_writer.addPage(pdf_reader.getPage(page))
    
    output = io.BytesIO()
    pdf_writer.write(output)
    return output
