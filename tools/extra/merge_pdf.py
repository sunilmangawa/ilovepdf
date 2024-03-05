# tools/merger_pdf.py
# import PyPDF2  # Or import fitz from pymupdf

# def merge_pdfs(pdf_files, output_file):
#     """Merges multiple PDF files into a single output file."""
#     pdf_merger = PyPDF2.PdfMerger()  # Or fitz.open() for pymupdf
#     for pdf_file in pdf_files:
#         with open(pdf_file, 'rb') as f:
#             pdf_merger.append(f)

#     with open(output_file, 'wb') as f:
#         pdf_merger.write(f)


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

# from PyPDF2 import PdfFileMerger

# def merge_pdfs(files, output_path):
#     merger = PdfFileMerger()
#     for pdf_file in files:
#         merger.append(pdf_file)
#     merger.write(output_path)
#     merger.close()





# from PyPDF2 import PdfMerger

# def merge_pdfs(pdf_files):
#     merger = PdfMerger()
#     merged_pdf_path = 'merged_pdf.pdf'
#     for pdf_file in pdf_files:
#         merger.append(pdf_file)
#     with open(merged_pdf_path, 'wb') as output:
#         merger.write(output)
#     return merged_pdf_path
