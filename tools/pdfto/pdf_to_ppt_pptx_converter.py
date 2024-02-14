from reportlab.lib.units import inch as Inches

import os
from io import BytesIO
from reportlab.pdfgen import canvas
from pptx import Presentation
import PyPDF2
from PIL import Image
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
import zipfile


# def convert_pdf_to_ppt_pptx(pdf_content, output_folder):
#     pdf_reader = PdfReader(pdf_content)

#     ppt_paths = []

#     for page_number in range(len(pdf_reader.pages)):
#         # Extract text from the PDF page
#         text = pdf_reader.pages[page_number].extract_text()

#         # Create a PowerPoint slide for each page
#         ppt_path = create_ppt_slide(text, output_folder, page_number + 1)
#         ppt_paths.append(ppt_path)

#     return ppt_paths

def create_ppt_slide(text, output_folder, slide_number):
    # Create a PowerPoint slide using reportlab
    output_path = os.path.join(output_folder, f"slide_{slide_number}.pptx")

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    flowables = [Paragraph(text, styles["Normal"])]

    doc.build(flowables)

    return output_path

def clean_up_temp_files(file_paths):
    for file_path in file_paths:
        os.remove(file_path)

def create_zip_archives(file_paths, zip_file_path):
    """
    Create a zip archive containing files specified by their paths.

    :param file_paths: List of file paths to be included in the zip archive.
    :param zip_file_path: Path to the output zip file.
    """
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file_path in file_paths:
            zipf.write(file_path, os.path.basename(file_path))


# def convert_pdf_to_ppt_pptx(pdf_content, output_folder):
#     """
#     Convert each page of a PDF file to a separate slide in PowerPoint (PPT and PPTX).

#     :param pdf_content: Content of the input PDF file as a file-like object (e.g., BytesIO).
#     :param output_folder: The folder where the PowerPoint files will be saved.
#     :return: List of paths to the generated PowerPoint files.
#     """
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)

#     pdf_canvas = canvas.Canvas(BytesIO(pdf_content))
#     pdf_pages = pdf_canvas.pages

#     ppt_paths = []

#     for page_number, pdf_page in enumerate(pdf_pages, start=1):
#         ppt_path = os.path.join(output_folder, f"slide_{page_number}.pptx")

#         prs = Presentation()

#         # Create a slide for each page
#         slide_layout = prs.slide_layouts[5]  # Choose a suitable layout (Title and Content)
#         slide = prs.slides.add_slide(slide_layout)

#         # Add a title to the slide
#         title = slide.shapes.title
#         title.text = f"Page {page_number}"

#         # Add content (image) to the slide
#         img = slide.shapes.add_picture(BytesIO(pdf_page.get_pdf_data()), 0, 0)

#         # Save the PowerPoint file
#         prs.save(ppt_path)
#         ppt_paths.append(ppt_path)

#     return ppt_paths


# def convert_pdf_to_ppt_pptx(pdf_content, output_folder):
#     """
#     Convert each page of a PDF file to a separate slide in PowerPoint (PPT and PPTX).

#     :param pdf_content: Content of the input PDF file as a file-like object (e.g., BytesIO).
#     :param output_folder: The folder where the PowerPoint files will be saved.
#     :return: List of paths to the generated PowerPoint files.
#     """
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)

#     # pdf_canvas = canvas.Canvas(BytesIO(pdf_content))
#     pdf_canvas = canvas.Canvas(BytesIO(pdf_content.getvalue()))

#     pdf_pages = pdf_canvas.pages

#     ppt_paths = []

#     for page_number, pdf_page in enumerate(pdf_pages, start=1):
#         ppt_path = os.path.join(output_folder, f"slide_{page_number}.pptx")

#         prs = Presentation()

#         # Create a slide for each page
#         slide_layout = prs.slide_layouts[5]  # Choose a suitable layout (Title and Content)
#         slide = prs.slides.add_slide(slide_layout)

#         # Add a title to the slide
#         title = slide.shapes.title
#         title.text = f"Page {page_number}"

#         # Add content (image) to the slide
#         img = slide.shapes.add_picture(BytesIO(pdf_page.get_pdf_data()), 0, 0)

#         # Save the PowerPoint file
#         prs.save(ppt_path)
#         ppt_paths.append(ppt_path)

#     return ppt_paths

# def convert_pdf_to_ppt_pptx(pdf_content, output_folder):
#     """
#     Convert each page of a PDF file to a separate slide in PowerPoint (PPT and PPTX).

#     :param pdf_content: Content of the input PDF file as a file-like object (e.g., BytesIO).
#     :param output_folder: The folder where the PowerPoint files will be saved.
#     :return: List of paths to the generated PowerPoint files.
#     """
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)

#     pdf_reader = PyPDF2.PdfReader(pdf_content)
#     total_pages = len(pdf_reader.pages)#pdf_reader.numPages

#     ppt_paths = []

#     for page_number in range(total_pages):
#         ppt_path = os.path.join(output_folder, f"slide_{page_number + 1}.pptx")

#         prs = Presentation()

#         # Create a slide for each page
#         slide_layout = prs.slide_layouts[5]  # Choose a suitable layout (Title and Content)
#         slide = prs.slides.add_slide(slide_layout)

#         # Add a title to the slide
#         title = slide.shapes.title
#         title.text = f"Page {page_number + 1}"

#         # Extract page image from PDF
#         pdf_page = pdf_reader.pages[page_number] #pdf_reader.getPage(page_number)
#         pdf_bytes = pdf_page.extract_text()
#         img = Image.open(BytesIO(pdf_bytes))

#         # Add content (image) to the slide
#         left = top = Inches(1)
#         img_width, img_height = img.size
#         slide.shapes.add_picture(BytesIO(pdf_page.get_pdf_data()), left, top, width=img_width, height=img_height)

#         # Save the PowerPoint file
#         prs.save(ppt_path)
#         ppt_paths.append(ppt_path)

#     return ppt_paths

def convert_pdf_to_ppt_pptx(pdf_content, output_folder):
    pdf_reader = PdfReader(pdf_content)

    ppt_paths = []

    for page_number, pdf_page in enumerate(pdf_reader.pages):
        # Extract content from the PDF page
        pdf_bytes = pdf_page.extract_text().encode('utf-8')
        # Create a PowerPoint slide for each page
        ppt_path = create_ppt_slide(pdf_bytes, output_folder, page_number + 1)
        ppt_paths.append(ppt_path)

    return ppt_paths


#Bard
# def convert_pdf_to_ppt_pptx(pdf_content, output_folder):
#     pdf_reader = PdfReader(pdf_content)

#     ppt_paths = []

#     for page_number in range(len(pdf_reader.pages)):
#         # Extract text from the PDF page
#         text = pdf_reader.pages[page_number].extract_text()

#         # Create a PowerPoint slide for each page
#         ppt_path = create_ppt_slide(text, output_folder, page_number + 1)
#         ppt_paths.append(ppt_path)

#     return ppt_paths

# def create_ppt_slide(text, output_folder, slide_number):
#     # Create a PowerPoint slide using reportlab
#     output_path = os.path.join(output_folder, f"slide_{slide_number}.pptx")

#     # ... (reportlab code to create the PPTX slide)

#     return output_path