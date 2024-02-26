# tools/word_to_pdf_converter.py
import os
from docxtopdf import convert

def convert_word_to_pdf(input_file, output_file):
    convert(input_file, output_file)

def clean_temp_files(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


# def convert_word_to_pdf(word_file_path, pdf_output_path):
#     # Convert Word file to PDF
#     convert(word_file_path, pdf_output_path)
#     return pdf_output_path


# def convert_word_to_pdf(word_file_path, pdf_output_path):
#     # Convert Word file to PDF
#     convert(word_file_path, pdf_output_path)

# def convert_word_to_pdf(word_file):
#     # Convert Word file to PDF
#     pdf_bytes = convert(word_file)

#     return pdf_bytes


