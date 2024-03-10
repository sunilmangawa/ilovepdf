# tools/topdf/word_to_pdf_converter.py
import os
from docxtopdf import convert

def convert_word_to_pdf(input_file, output_file):
    convert(input_file, output_file)

def clean_temp_files(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
