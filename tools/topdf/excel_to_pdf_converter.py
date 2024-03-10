# tools/excel_to_pdf_converter.py
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import pandas as pd
from fpdf import FPDF
from pandas import ExcelWriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors



def convert_excel_to_pdf(file):
    file_path = os.path.join(settings.MEDIA_ROOT, file.name)
    fs = FileSystemStorage(location=settings.MEDIA_ROOT)
    filename = fs.save(file.name, file)
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    
    df = pd.read_excel(file_path)
    pdf_path = file_path.replace('.xlsx', '.pdf').replace('.xls', '.pdf').replace('.ods', '.pdf')
    
    # Determine page size based on the content
    page_orientation = 'portrait'
    if len(df.columns) > len(df.index):
        page_size = landscape(letter)
        page_orientation = 'landscape'
    else:
        page_size = letter
    
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Calculate column widths and row heights
    col_widths = [max(len(str(value)) for value in column) * 7 for column in zip(*data)]
    row_heights = [max(len(str(value)) for value in row) * 15 for row in data]
    
    doc = SimpleDocTemplate(pdf_path, pagesize=page_size, rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10)
    table = Table(data, colWidths=col_widths, rowHeights=row_heights)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    
    doc.build([table])
    
    # Remove the temporary Excel file
    os.remove(file_path)
    
    return pdf_path


# from spire.xls import Workbook, FileFormat

# def convert_excel_to_pdf(input_file, output_file):
#     workbook = Workbook()
#     workbook.LoadFromFile(input_file)

#     # Fit each worksheet to one page
#     workbook.ConverterSetting.SheetFitToPage = True

#     # Convert the Excel file to PDF format
#     workbook.SaveToFile(output_file, FileFormat.PDF)
#     workbook.Dispose()
