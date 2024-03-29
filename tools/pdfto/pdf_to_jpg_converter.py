import os
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import zipfile


def convert_pdf_to_jpg(pdf_content, output_folder):
    """
    Convert each page of a PDF file to a separate JPG image.

    :param pdf_content: Content of the input PDF file as a file-like object (e.g., BytesIO).
    :param output_folder: The folder where the JPG images will be saved.
    :return: List of paths to the generated JPG images.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf_document = fitz.open("pdf", pdf_content)

    jpg_paths = []

    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]

        # Use get_pixmap for older versions of PyMuPDF
        pixmap = page.get_pixmap()
        img_index_str = f"{page_number + 1:03d}"
        img_path = os.path.join(output_folder, f"{img_index_str}.jpg")

        # Convert pixmap to PIL Image
        img = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)

        # Save the image
        img.save(img_path)

        jpg_paths.append(img_path)

    pdf_document.close()
    return jpg_paths


def clean_up_jpg_files(jpg_paths):
    """
    Delete the temporary JPG files created during the conversion process.

    :param jpg_paths: List of paths to JPG files.
    """
    for jpg_path in jpg_paths:
        os.remove(jpg_path)


def create_zip_archive(file_paths, zip_file_path):
    """
    Create a zip archive containing files specified by their paths.

    :param file_paths: List of file paths to be included in the zip archive.
    :param zip_file_path: Path to the output zip file.
    """
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file_path in file_paths:
            zipf.write(file_path, os.path.basename(file_path))

            