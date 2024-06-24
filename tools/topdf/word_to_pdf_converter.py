# # tools/topdf/word_to_pdf_converter.py
import os
import subprocess
import re


def convert_to_pdf(docx_file_path):
    try:
        subprocess.run('doc2pdf', 'docx_file_path')
        # The output PDF file path will be the same as the input DOCX file path
        pdf_file_path = os.path.splitext(docx_file_path)[0] + '.pdf'
        return pdf_file_path
    except subprocess.CalledProcessError:
        return None



# def convert_to_pdf(docx_file_path, output_pdf_path):
#     try:
#         subprocess.run(['unoconv', '--output', output_pdf_path, '--format', 'pdf', docx_file_path], check=True)
#         return True
#     except subprocess.CalledProcessError:
#         return False

# def convert_to_pdf(folder, source, timeout=None):
#     """
#     Convert a DOCX file to PDF using LibreOffice.

#     Args:
#         folder (str): The output directory for the converted PDF file.
#         source (str): The path to the input DOCX file.
#         timeout (int, optional): Timeout for the conversion process (in seconds).

#     Returns:
#         str: The path to the converted PDF file.

#     Raises:
#         LibreOfficeError: If an error occurs during the conversion process.
#     """
#     # args = [libreoffice_exec(), '--headless', '--convert-to', 'pdf', '--outdir', folder, source]
#     # args = [libreoffice, '--convert-to', 'pdf', '--outdir', folder, source]
#     args = [doc2pdf, source, folder]

#     # process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
#     # filename = re.search('-> (.*?) using filter', process.stdout.decode())

#     if filename is None:
#         raise LibreOfficeError(process.stdout.decode())
#     else:
#         sanitized_filename = sanitize_filename(filename.group(1))
#         return filename.group(1)


# def libreoffice_exec():
#     """
#     Get the path to the LibreOffice executable based on the operating system.

#     Returns:
#         str: The path to the LibreOffice executable.
#     """
#     # Assuming LibreOffice is installed in the default location on Ubuntu
#     return '/usr/bin/libreoffice'  # Adjust if installed elsewhere

# class LibreOfficeError(Exception):
#     """
#     Custom exception class for errors during LibreOffice conversion.
#     """
#     def __init__(self, output):
#         self.output = output

# def sanitize_filename(filename):
#     """
#     Remove any null bytes ('\x00') from the filename.
#     """
#     return filename.replace('\x00', '')





# # import os
# from docxtopdf import convert

# # #write a function to convert word file to pdf for django project including views.py code
# def convert_word_to_pdf(input_file, output_file):
#     convert(input_file, output_file)


# import os
# import subprocess

# # def convert_to_pdf(input_file_path, output_file_path):
# #     try:
# #         Convert using LibreOffice
# #         subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', input_file_path, '--outdir', os.path.dirname(output_file_path)])
# #         return True
# #     except Exception as e:
# #         print(f"Conversion Error: {e}")
# #         return False

def clean_temp_files(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

# import sys
# import subprocess
# import re


# def convert_to_pdf(folder, source, timeout=None):
#     """
#     Convert a DOCX file to PDF using LibreOffice.
    
#     Args:
#         folder (str): The output directory for the converted PDF file.
#         source (str): The path to the input DOCX file.
#         timeout (int, optional): Timeout for the conversion process (in seconds).

#     Returns:
#         str: The path to the converted PDF file.
        
#     Raises:
#         LibreOfficeError: If an error occurs during the conversion process.
#     """
#     args = [libreoffice_exec(), '--headless', '--convert-to', 'pdf', '--outdir', folder, source]

#     process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
#     filename = re.search('-> (.*?) using filter', process.stdout.decode())

#     if filename is None:
#         raise LibreOfficeError(process.stdout.decode())
#     else:
#         return filename.group(1)


# def libreoffice_exec():
#     """
#     Get the path to the LibreOffice executable based on the operating system.
    
#     Returns:
#         str: The path to the LibreOffice executable.
#     """
#     # TODO: Provide support for more platforms
#     if sys.platform == 'darwin':
#         return '/Applications/LibreOffice.app/Contents/MacOS/soffice'
#     return 'libreoffice'


# class LibreOfficeError(Exception):
#     """
#     Custom exception class for errors during LibreOffice conversion.
#     """
#     def __init__(self, output):
#         self.output = output

# def sanitize_filename(filename):
#     """
#     Remove any null bytes ('\x00') from the filename.
#     """
#     return filename.replace('\x00', '')