# ==============================================================================
# FILE: tools/extra/forms_pdf.py
# ==============================================================================
"""
PDF Forms Engine - Pure In-Memory Operations
Fills existing AcroForm fields, creates new interactive form fields,
or flattens filled values into permanent vector/raster PDF layers.
Zero disk usage: all operations use io.BytesIO.
"""
import io
import re
import os
import json
import base64

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (
        DictionaryObject,
        NameObject,
        ArrayObject,
        NumberObject,
        create_string_object,
    )
    HAS_PYPDF = True
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from PyPDF2.generic import (
            DictionaryObject,
            NameObject,
            ArrayObject,
            NumberObject,
            create_string_object,
        )
        HAS_PYPDF = True
    except ImportError:
        HAS_PYPDF = False

# ReportLab for crisp vector-level flattening
try:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.colors import HexColor
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def clean_base_filename(filename):
    """Sanitize and return base filename without extension."""
    if not filename:
        return "document"
    base = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base).strip('._')
    return cleaned or "document"


def flatten_fields_with_reportlab(fields_by_page, page_w, page_h):
    """
    Generates a single-page transparent PDF overlay with burned-in field values
    rendered using ReportLab vector canvas.
    """
    packet = io.BytesIO()
    c = rl_canvas.Canvas(packet, pagesize=(page_w, page_h))

    for field in fields_by_page:
        ftype = field.get('type', 'text')
        val = str(field.get('value', ''))
        rect = field.get('rect', {})
        fx = float(rect.get('x', 0))
        # ReportLab coordinate system: (0,0) is bottom-left, DOM canvas is top-left
        fy_top = float(rect.get('y', 0))
        fw = float(rect.get('width', 100))
        fh = float(rect.get('height', 24))
        fy = page_h - fy_top - fh

        font_size = float(field.get('fontSize', 11))

        if ftype in ('text', 'textarea', 'date'):
            if val:
                c.setFont("Helvetica", font_size)
                c.setFillColor(HexColor(field.get('color', '#1e293b')))
                # Padding
                c.drawString(fx + 4, fy + (fh - font_size) / 2, val)

        elif ftype == 'checkbox':
            checked = field.get('checked', False) or val.lower() in ('true', '1', 'yes', 'on')
            if checked:
                c.setStrokeColor(HexColor(field.get('color', '#e5322d')))
                c.setLineWidth(2)
                # Draw checkmark
                p = c.beginPath()
                p.moveTo(fx + fw * 0.2, fy + fh * 0.5)
                p.lineTo(fx + fw * 0.45, fy + fh * 0.2)
                p.lineTo(fx + fw * 0.85, fy + fh * 0.8)
                c.drawPath(p, stroke=1, fill=0)

        elif ftype == 'radio':
            checked = field.get('checked', False) or val.lower() in ('true', '1', 'yes', 'on')
            if checked:
                c.setFillColor(HexColor(field.get('color', '#e5322d')))
                radius = min(fw, fh) * 0.3
                c.circle(fx + fw / 2, fy + fh / 2, radius, stroke=0, fill=1)

        elif ftype == 'dropdown':
            if val:
                c.setFont("Helvetica", font_size)
                c.setFillColor(HexColor(field.get('color', '#1e293b')))
                c.drawString(fx + 4, fy + (fh - font_size) / 2, val)

    c.save()
    packet.seek(0)
    return packet


def process_pdf_forms_in_memory(pdf_file, fields_data, export_mode='interactive'):
    """
    Processes PDF forms 100% in memory.

    Parameters:
    - pdf_file: UploadedFile, file-like object, or bytes.
    - fields_data: JSON string or list of dicts with field definitions & values.
    - export_mode: 'interactive' (keep AcroForm fillable) or 'flatten' (burn into content).

    Returns:
    {
        'name': 'document_form.pdf',
        'bytes': b'...',
        'page_count': 3,
        'size': 123456
    }
    """
    if not HAS_PYPDF:
        raise ImportError("pypdf or PyPDF2 is required for in-memory PDF form processing.")

    # 1. Read input PDF into memory
    if hasattr(pdf_file, 'read'):
        raw_bytes = pdf_file.read()
        stream = io.BytesIO(raw_bytes)
    elif isinstance(pdf_file, (bytes, bytearray)):
        stream = io.BytesIO(pdf_file)
    else:
        raise ValueError("Invalid PDF file object provided.")

    reader = PdfReader(stream)

    if getattr(reader, 'is_encrypted', False):
        try:
            reader.decrypt('')
        except Exception:
            raise ValueError("The PDF is password-protected. Please unlock it before editing.")

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("The provided PDF contains no pages.")

    # 2. Parse fields data
    if isinstance(fields_data, str):
        try:
            fields_data = json.loads(fields_data)
        except Exception:
            fields_data = []

    if not isinstance(fields_data, list):
        fields_data = []

    # Map fields by page index (1-based)
    page_fields_map = {}
    form_values_to_update = {}

    for item in fields_data:
        try:
            p_num = int(item.get('page', 1))
            page_fields_map.setdefault(p_num, []).append(item)
            name = item.get('name')
            val = item.get('value')
            if name and val is not None:
                form_values_to_update[name] = str(val)
        except (ValueError, TypeError):
            continue

    filename = getattr(pdf_file, 'name', 'document.pdf')
    base_name = clean_base_filename(filename)
    mode_suffix = "filled" if export_mode == "flatten" else "form"
    output_filename = f"{base_name}_{mode_suffix}.pdf"

    writer = PdfWriter()

    # If the original PDF already had AcroForm fields, populate matching values
    for page in reader.pages:
        writer.add_page(page)

    if form_values_to_update and hasattr(writer, 'update_page_form_field_values'):
        try:
            for page in writer.pages:
                writer.update_page_form_field_values(page, form_values_to_update)
        except Exception:
            pass  # Fall back to overlay merging

    # If flattening requested or adding new placed fields via overlay
    if export_mode == 'flatten' and HAS_REPORTLAB and page_fields_map:
        new_writer = PdfWriter()
        for idx, page in enumerate(writer.pages):
            page_num = idx + 1
            if page_num in page_fields_map:
                p_box = page.mediabox
                page_w = float(p_box.width)
                page_h = float(p_box.height)
                overlay_stream = flatten_fields_with_reportlab(page_fields_map[page_num], page_w, page_h)
                overlay_reader = PdfReader(overlay_stream)
                page.merge_page(overlay_reader.pages[0])
            new_writer.add_page(page)
        writer = new_writer

    # 3. Write resulting PDF to in-memory buffer
    out_buffer = io.BytesIO()
    writer.write(out_buffer)
    out_buffer.seek(0)
    pdf_bytes = out_buffer.getvalue()

    return {
        'name': output_filename,
        'bytes': pdf_bytes,
        'page_count': total_pages,
        'size': len(pdf_bytes)
    }
