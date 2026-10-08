# tools/Topdf/excel_to_pdf_converter.py
import io
import os
import csv
import shutil
import logging
import tempfile
import subprocess
from datetime import date, datetime
from typing import Tuple, Dict, Any, Generator, List, Optional

from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import xlrd
except ImportError:
    xlrd = None

logger = logging.getLogger(__name__)


class FastNumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas for exact 'Page X of Y' on standard documents (< 250 pages),
    and streaming single-pass numbering on massive multi-thousand-page documents
    to guarantee high speed and low memory usage without process freezing.
    """
    def __init__(self, *args, max_two_pass_pages: int = 250, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.max_two_pass_pages = max_two_pass_pages
        self.is_huge_document = False

    def showPage(self):
        if not self.is_huge_document and len(self._saved_page_states) < self.max_two_pass_pages:
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()
        else:
            if not self.is_huge_document:
                self.is_huge_document = True
                # Flush previously saved pages with streaming single-pass footer
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self._draw_page_footer(page_num=self._pageNumber, total_pages=None)
                    super().showPage()
                self._saved_page_states.clear()
            self._draw_page_footer(page_num=self._pageNumber, total_pages=None)
            super().showPage()

    def save(self):
        if not self.is_huge_document:
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self._draw_page_footer(page_num=self._pageNumber, total_pages=num_pages)
                super().showPage()
            self._saved_page_states.clear()
        super().save()

    def _draw_page_footer(self, page_num: int, total_pages: Optional[int] = None):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)

        pw, _ = self._pagesize
        self.line(30, 24, pw - 30, 24)
        self.drawString(30, 13, "iLovePDF Converter • Excel to PDF")

        page_str = f"Page {page_num} of {total_pages}" if total_pages else f"Page {page_num}"
        self.drawRightString(pw - 30, 13, page_str)
        self.restoreState()


def format_cell_value(val: Any) -> str:
    """Formats cell values cleanly (handles None, dates, floats, booleans, formulas)."""
    if val is None:
        return ""
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return f"{val:.4f}".rstrip("0").rstrip(".")
    return str(val).strip()


def fit_text(text: str, max_w: float, font_name: str, font_size: float) -> str:
    """Fast text truncation with ellipsis if content exceeds available cell width."""
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if not text:
        return ""
    w = stringWidth(text, font_name, font_size)
    if w <= max_w:
        return text

    ellipsis = "..."
    ew = stringWidth(ellipsis, font_name, font_size)
    if ew >= max_w:
        return ""

    avail = max_w - ew
    ratio = avail / max(w, 1.0)
    target = max(1, int(len(text) * ratio))
    sub = text[:target]
    while target > 0 and stringWidth(sub, font_name, font_size) > avail:
        target -= 1
        sub = text[:target]
    return sub + ellipsis


def calculate_column_widths(headers: List[str], sample_rows: List[List[Any]], usable_w: float) -> List[float]:
    """Calculates proportional column widths based on header and data content length."""
    col_count = len(headers)
    if col_count == 0:
        return []

    col_scores = []
    for c_idx in range(col_count):
        h_len = len(str(headers[c_idx])) if c_idx < len(headers) else 0
        r_lens = []
        for r in sample_rows:
            if c_idx < len(r) and r[c_idx] is not None:
                r_lens.append(len(str(r[c_idx])))
        avg_len = sum(r_lens) / len(r_lens) if r_lens else 0
        max_len = max(r_lens) if r_lens else 0
        # Balance header length, average content length, and capped max length
        score = max(6, int(0.35 * h_len + 0.35 * avg_len + 0.30 * min(max_len, 35)))
        col_scores.append(score)

    tot_score = sum(col_scores)
    min_col_w = max(28.0, usable_w / (col_count * 2.5))
    raw_widths = [(s / tot_score) * usable_w for s in col_scores]
    widths = [max(min_col_w, w) for w in raw_widths]
    tot = sum(widths)
    if tot > 0:
        widths = [w * (usable_w / tot) for w in widths]
    return widths


def render_sheet_to_canvas(
    c: canvas.Canvas,
    sheet_name: str,
    headers: List[str],
    rows_generator: Generator[List[Any], None, None],
    page_size: Tuple[float, float],
    show_grid: bool = True
):
    """
    Renders an individual spreadsheet sheet into the PDF canvas using high-speed
    vectorized batch drawing for minimal PDF size and maximum performance.
    """
    page_w, page_h = page_size
    margin_x = 30
    margin_top = 35
    margin_bottom = 35
    usable_w = page_w - 2 * margin_x

    clean_headers = [
        str(h if h is not None and str(h).strip() != "" else f"Column {i+1}").strip()
        for i, h in enumerate(headers)
    ]
    col_count = len(clean_headers)
    if col_count == 0:
        return

    # Dynamic typography sizing based on column density
    if col_count <= 6:
        font_size = 8.5
        header_font_size = 9.0
        row_h = 16
        header_h = 20
    elif col_count <= 10:
        font_size = 7.5
        header_font_size = 8.0
        row_h = 14
        header_h = 18
    elif col_count <= 16:
        font_size = 6.5
        header_font_size = 7.0
        row_h = 12
        header_h = 16
    else:
        font_size = 5.5
        header_font_size = 6.0
        row_h = 11
        header_h = 14

    # Sample initial rows for optimal column width calculation
    sample_rows = []
    buffered_rows = []
    for r in rows_generator:
        row_list = [format_cell_value(val) for val in r]
        if len(row_list) < col_count:
            row_list.extend([""] * (col_count - len(row_list)))
        elif len(row_list) > col_count:
            row_list = row_list[:col_count]
        buffered_rows.append(row_list)
        if len(sample_rows) < 100:
            sample_rows.append(row_list)
        if len(buffered_rows) >= 500:
            break

    col_widths = calculate_column_widths(clean_headers, sample_rows, usable_w)
    x_positions = []
    curr_x = margin_x
    for w in col_widths:
        x_positions.append(curr_x)
        curr_x += w
    x_positions.append(curr_x)

    usable_page_h = page_h - margin_top - margin_bottom - header_h
    rows_per_page = max(1, int(usable_page_h / row_h))

    def render_page(rows_batch: List[List[str]], is_first_page_of_sheet: bool):
        # Sheet Banner on first page of this worksheet
        if is_first_page_of_sheet:
            c.saveState()
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(colors.HexColor("#0F172A"))
            c.drawString(margin_x, page_h - 22, f"Worksheet: {sheet_name}")
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.HexColor("#64748B"))
            c.drawRightString(page_w - margin_x, page_h - 22, f"{col_count} columns")
            c.restoreState()

        header_y = page_h - margin_top - header_h

        # Header background & border (Slate-900)
        c.setFillColor(colors.HexColor("#1E293B"))
        c.rect(margin_x, header_y, usable_w, header_h, fill=1, stroke=0)

        # Header text
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", header_font_size)
        for i, h in enumerate(clean_headers):
            col_w = col_widths[i]
            txt = fit_text(h, col_w - 6, "Helvetica-Bold", header_font_size)
            c.drawString(x_positions[i] + 4, header_y + (header_h - header_font_size) / 2 + 1, txt)

        num_rows = len(rows_batch)
        table_top_y = header_y
        table_bottom_y = table_top_y - num_rows * row_h

        # Bulk Zebra striping
        c.setFillColor(colors.HexColor("#F8FAFC"))
        for r_idx in range(1, num_rows, 2):
            ry = table_top_y - (r_idx + 1) * row_h
            c.rect(margin_x, ry, usable_w, row_h, fill=1, stroke=0)

        # Draw cell contents
        c.setFillColor(colors.HexColor("#1E293B"))
        c.setFont("Helvetica", font_size)
        for r_idx, row in enumerate(rows_batch):
            ry = table_top_y - (r_idx + 1) * row_h + (row_h - font_size) / 2 + 1
            for c_idx in range(col_count):
                val_str = row[c_idx] if c_idx < len(row) else ""
                if not val_str or val_str == "None":
                    continue
                col_w = col_widths[c_idx]
                txt = fit_text(val_str, col_w - 6, "Helvetica", font_size)

                # Right align numbers and currencies
                clean_num = val_str.replace(",", "").replace("$", "").replace("%", "").strip()
                is_num = bool(clean_num and clean_num.replace(".", "", 1).replace("-", "", 1).isdigit())

                if is_num and col_w > 45:
                    tw = stringWidth(txt, "Helvetica", font_size)
                    c.drawString(x_positions[c_idx] + col_w - tw - 4, ry, txt)
                else:
                    c.drawString(x_positions[c_idx] + 4, ry, txt)

        # Bulk Grid lines
        if show_grid:
            c.setStrokeColor(colors.HexColor("#E2E8F0"))
            c.setLineWidth(0.5)
            # Horizontal lines
            for r_idx in range(num_rows + 1):
                ly = table_top_y - r_idx * row_h
                c.line(margin_x, ly, margin_x + usable_w, ly)
            # Vertical lines
            for lx in x_positions:
                c.line(lx, table_top_y, lx, table_bottom_y)

        c.showPage()

    # Stream rendering in chunks of rows_per_page
    is_first = True
    page_batch = []

    for r in buffered_rows:
        page_batch.append(r)
        if len(page_batch) >= rows_per_page:
            render_page(page_batch, is_first)
            is_first = False
            page_batch = []

    for r in rows_generator:
        row_list = [format_cell_value(val) for val in r]
        if len(row_list) < col_count:
            row_list.extend([""] * (col_count - len(row_list)))
        elif len(row_list) > col_count:
            row_list = row_list[:col_count]
        page_batch.append(row_list)
        if len(page_batch) >= rows_per_page:
            render_page(page_batch, is_first)
            is_first = False
            page_batch = []

    if page_batch:
        render_page(page_batch, is_first)


def parse_csv_stream(file_bytes: bytes) -> List[Tuple[str, List[str], Generator[List[str], None, None]]]:
    """
    Decodes CSV/TSV bytes with automatic character encoding detection and delimiter sniffing.
    """
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    text = None
    for enc in encodings:
        try:
            text = file_bytes.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if text is None:
        text = file_bytes.decode("utf-8", errors="replace")

    sample = text[:4096]
    delimiter = ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        delimiter = dialect.delimiter
    except Exception:
        if "\t" in sample and sample.count("\t") > sample.count(","):
            delimiter = "\t"
        elif ";" in sample and sample.count(";") > sample.count(","):
            delimiter = ";"

    lines = io.StringIO(text)
    reader = csv.reader(lines, delimiter=delimiter)

    try:
        first_row = next(reader)
        while not any(str(c).strip() for c in first_row):
            first_row = next(reader)
    except StopIteration:
        first_row = ["(Empty File)"]

    headers = [str(h).strip() for h in first_row]
    return [("Data", headers, reader)]


def parse_xlsx_stream(file_bytes: bytes, sheet_mode: str = "all") -> List[Tuple[str, List[str], Generator[List[Any], None, None]]]:
    """
    Parses OpenXML (.xlsx, .xlsm, .xltx, .xltm) files using openpyxl in read_only
    and data_only mode to retrieve calculated formula results and conserve RAM.
    """
    if openpyxl is None:
        raise ImportError("openpyxl library is required for .xlsx files. Run: pip install openpyxl")

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    sheets_to_process = wb.sheetnames if sheet_mode == "all" else [wb.active.title]

    results = []
    for s_name in sheets_to_process:
        ws = wb[s_name]
        row_iter = ws.iter_rows(values_only=True)
        try:
            first_row = next(row_iter)
            while first_row is not None and not any(c is not None and str(c).strip() != "" for c in first_row):
                first_row = next(row_iter)
        except StopIteration:
            first_row = ["(Empty Sheet)"]

        if first_row is None:
            first_row = ["(Empty Sheet)"]

        headers = [format_cell_value(c) if c is not None else f"Column {i+1}" for i, c in enumerate(first_row)]
        results.append((s_name, headers, row_iter))

    return results


def parse_xls_stream(file_bytes: bytes, sheet_mode: str = "all") -> List[Tuple[str, List[str], Generator[List[Any], None, None]]]:
    """
    Parses legacy Excel (.xls) files using xlrd directly in-memory.
    """
    if xlrd is None:
        raise ImportError("xlrd library is required for legacy .xls files. Run: pip install xlrd")

    workbook = xlrd.open_workbook(file_contents=file_bytes)
    sheet_indices = range(workbook.nsheets) if sheet_mode == "all" else [0]

    results = []
    for idx in sheet_indices:
        sheet = workbook.sheet_by_index(idx)
        if sheet.nrows == 0:
            results.append((sheet.name, ["(Empty Sheet)"], (r for r in [])))
            continue

        first_row_vals = sheet.row_values(0)
        headers = [
            str(v).strip() if v is not None and str(v).strip() != "" else f"Column {i+1}"
            for i, v in enumerate(first_row_vals)
        ]

        def row_generator(s=sheet):
            for r in range(1, s.nrows):
                yield s.row_values(r)

        results.append((sheet.name, headers, row_generator()))

    return results


def try_libreoffice_convert(file_bytes: bytes, file_extension: str) -> Optional[bytes]:
    """
    Optional conversion using system headless LibreOffice if installed.
    Scoped strictly within a temp directory context manager to ensure 100% cleanup.
    """
    soffice = shutil.which("libreoffice") or shutil.which("soffice")
    if not soffice:
        return None

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, f"document{file_extension}")
            with open(input_path, "wb") as f:
                f.write(file_bytes)

            cmd = [
                soffice,
                "--headless",
                "--invisible",
                "--nodefault",
                "--nofirststartwizard",
                "--nolockcheck",
                "--nologo",
                "--convert-to", "pdf:calc_pdf_Export",
                "--outdir", temp_dir,
                input_path,
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
            if res.returncode == 0:
                output_pdf = os.path.join(temp_dir, "document.pdf")
                if os.path.exists(output_pdf):
                    with open(output_pdf, "rb") as out:
                        return out.read()
    except Exception as e:
        logger.warning("LibreOffice conversion failed, falling back to native engine: %s", e)

    return None


def convert_excel_to_pdf(
    file_input: Any,
    filename: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> Tuple[bytes, str]:
    """
    Main entrypoint: Converts Excel (.xlsx, .xls, .xlsm, .xltx, .xltm) or CSV/TSV into PDF.
    Guarantees zero temporary files left on disk.

    Args:
        file_input: UploadedFile (Django), file-like object, bytes, or file path.
        filename: Original file name (e.g. 'sales_report.xlsx').
        options: Dict containing:
            - orientation: 'auto' (default), 'landscape', 'portrait'
            - page_size: 'letter' (default), 'a4'
            - gridlines: True (default), False
            - sheet_mode: 'all' (default), 'first'
            - engine: 'auto' (default), 'native', 'libreoffice'

    Returns:
        Tuple[bytes, str]: (pdf_bytes, output_pdf_filename)
    """
    if options is None:
        options = {}

    orientation = str(options.get("orientation", "auto")).lower()
    page_size_pref = str(options.get("page_size", "letter")).lower()
    show_grid = bool(options.get("gridlines", True))
    sheet_mode = str(options.get("sheet_mode", "all")).lower()
    engine = str(options.get("engine", "auto")).lower()

    # Extract bytes and filename
    if hasattr(file_input, "read"):
        if hasattr(file_input, "name") and not filename:
            filename = file_input.name
        file_bytes = file_input.read()
    elif isinstance(file_input, bytes):
        file_bytes = file_input
    elif isinstance(file_input, str):
        if not filename:
            filename = os.path.basename(file_input)
        with open(file_input, "rb") as f:
            file_bytes = f.read()
    else:
        raise ValueError("Invalid file_input: expected file-like object, bytes, or path string.")

    if not filename:
        filename = "document.xlsx"

    base_name, ext = os.path.splitext(filename)
    ext = ext.lower()
    safe_output_name = f"{base_name}.pdf"

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    # Try headless LibreOffice if requested or in auto mode when available
    if engine in ["auto", "libreoffice"] and ext in [".xlsx", ".xls", ".xlsm", ".xltx", ".xltm"]:
        lo_pdf = try_libreoffice_convert(file_bytes, ext)
        if lo_pdf:
            return lo_pdf, safe_output_name
        if engine == "libreoffice":
            raise RuntimeError("LibreOffice conversion failed or LibreOffice is not installed.")

    # Native ReportLab Pure-Python Engine
    if ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
        sheets = parse_xlsx_stream(file_bytes, sheet_mode=sheet_mode)
    elif ext == ".xls":
        sheets = parse_xls_stream(file_bytes, sheet_mode=sheet_mode)
    elif ext in [".csv", ".tsv", ".txt"]:
        sheets = parse_csv_stream(file_bytes)
    else:
        # Fallback probe
        try:
            sheets = parse_xlsx_stream(file_bytes, sheet_mode=sheet_mode)
        except Exception:
            sheets = parse_csv_stream(file_bytes)

    if not sheets:
        raise ValueError("No readable worksheets found in the uploaded file.")

    # Determine Page Orientation
    max_cols = max(len(h) for _, h, _ in sheets)
    if orientation == "landscape":
        is_landscape = True
    elif orientation == "portrait":
        is_landscape = False
    else:  # auto
        is_landscape = (max_cols > 6)

    base_size = A4 if page_size_pref == "a4" else letter
    page_size = landscape(base_size) if is_landscape else base_size

    # Render PDF completely in memory (io.BytesIO)
    pdf_buffer = io.BytesIO()
    c = FastNumberedCanvas(pdf_buffer, pagesize=page_size)

    for sheet_name, headers, row_iter in sheets:
        render_sheet_to_canvas(
            c=c,
            sheet_name=sheet_name,
            headers=headers,
            rows_generator=row_iter,
            page_size=page_size,
            show_grid=show_grid,
        )

    c.save()
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    return pdf_bytes, safe_output_name













# import os
# from django.conf import settings
# from django.core.files.storage import FileSystemStorage
# import pandas as pd
# from fpdf import FPDF
# from pandas import ExcelWriter
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
# from reportlab.lib import colors



# def convert_excel_to_pdf(file):
#     file_path = os.path.join(settings.MEDIA_ROOT, file.name)
#     fs = FileSystemStorage(location=settings.MEDIA_ROOT)
#     filename = fs.save(file.name, file)
#     file_path = os.path.join(settings.MEDIA_ROOT, filename)
    
#     df = pd.read_excel(file_path)
#     pdf_path = file_path.replace('.xlsx', '.pdf').replace('.xls', '.pdf').replace('.ods', '.pdf')
    
#     # Determine page size based on the content
#     page_orientation = 'portrait'
#     if len(df.columns) > len(df.index):
#         page_size = landscape(letter)
#         page_orientation = 'landscape'
#     else:
#         page_size = letter
    
#     data = [df.columns.tolist()] + df.values.tolist()
    
#     # Calculate column widths and row heights
#     col_widths = [max(len(str(value)) for value in column) * 7 for column in zip(*data)]
#     row_heights = [max(len(str(value)) for value in row) * 15 for row in data]
    
#     doc = SimpleDocTemplate(pdf_path, pagesize=page_size, rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10)
#     table = Table(data, colWidths=col_widths, rowHeights=row_heights)
#     table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                                ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    
#     doc.build([table])
    
#     # Remove the temporary Excel file
#     os.remove(file_path)
    
#     return pdf_path


# # from spire.xls import Workbook, FileFormat

# # def convert_excel_to_pdf(input_file, output_file):
# #     workbook = Workbook()
# #     workbook.LoadFromFile(input_file)

# #     # Fit each worksheet to one page
# #     workbook.ConverterSetting.SheetFitToPage = True

# #     # Convert the Excel file to PDF format
# #     workbook.SaveToFile(output_file, FileFormat.PDF)
# #     workbook.Dispose()
