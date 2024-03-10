import os
from PyPDF2 import PdfReader, PdfWriter

from django.utils.encoding import smart_str

def split_pdf_by_page(pdf_file, page_numbers=''):
    output_files = []
    pdf_reader = PdfReader(pdf_file)
    if page_numbers:
        page_numbers_list = page_numbers.split(',')
        for page_range in page_numbers_list:
            if '-' in page_range:
                start, end = map(int, page_range.split('-'))
                for page_num in range(start-1, end):
                    output_pdf_writer = PdfWriter()
                    output_pdf_writer.add_page(pdf_reader.pages[page_num])
                    output_pdf_path = f'{os.path.splitext(pdf_file.name)[0]}_page_{page_num+1}.pdf'
                    with open(output_pdf_path, 'wb') as output_pdf_file:
                        output_pdf_writer.write(output_pdf_file)
                    output_files.append(output_pdf_path)
            else:
                page_num = int(page_range)
                output_pdf_writer = PdfWriter()
                output_pdf_writer.add_page(pdf_reader.pages[page_num-1])
                output_pdf_path = f'{os.path.splitext(pdf_file.name)[0]}_page_{page_num}.pdf'
                with open(output_pdf_path, 'wb') as output_pdf_file:
                    output_pdf_writer.write(output_pdf_file)
                output_files.append(output_pdf_path)
    else:
        for page_num in range(len(pdf_reader.pages)):
            output_pdf_writer = PdfWriter()
            output_pdf_writer.add_page(pdf_reader.pages[page_num])
            output_pdf_path = f'{os.path.splitext(pdf_file.name)[0]}_page_{page_num+1}.pdf'
            with open(output_pdf_path, 'wb') as output_pdf_file:
                output_pdf_writer.write(output_pdf_file)
            output_files.append(output_pdf_path)
    return output_files

