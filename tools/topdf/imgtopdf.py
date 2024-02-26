# tools/imgtopdf.py

from PIL import Image
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO

def convert_to_pdf(image_files):
    pdf_writer = PdfWriter()
    
    for img_file in image_files:
        img = Image.open(img_file)
        img_bytes = BytesIO()
        img.save(img_bytes, format='PDF')
        img_bytes.seek(0)  # Reset the pointer to the beginning
        # pdf_reader = PdfReader(img_bytes)
        # for page in pdf_reader.pages:
        pdf_writer.add_page(page)
    
    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)
    
    return output_pdf

# def convert_to_pdf(image_files):
#     pdf_writer = PdfWriter()
    
#     for img_path in image_files:
#         img = Image.open(img_path)
#         pdf_writer.add_page(img)
    
#     output_pdf = "output.pdf"
#     with open(output_pdf, 'wb') as f:
#         pdf_writer.write(f)
    
#     return output_pdf
