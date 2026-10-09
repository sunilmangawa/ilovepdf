import io
import re
import os
import json
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    from PyPDF2 import PdfReader, PdfWriter
def clean_base_filename(filename):
    """Sanitize and return base filename without extension."""
    if not filename:
        return "document"
    base = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base).strip('._')
    return cleaned or "document"
def parse_pages_order(pages_order_input, total_pages):
    """
    Parses pages order specification from various formats:
    - JSON string or list of dicts:
      [{"page": 3, "rotation": 90}, {"page": 1, "rotation": 0}, {"page": "blank", "rotation": 0}]
    - JSON string or list of ints: [3, 1, 2]
    - Comma-separated string: "3:90, 1:0, 2:180" or "3, 1, 2"
    Returns a list of dicts:
    [
        {'page': 3, 'rotation': 90, 'is_blank': False},
        {'page': 1, 'rotation': 0, 'is_blank': False},
        ...
    ]
    """
    if not pages_order_input:
        return [{'page': p, 'rotation': 0, 'is_blank': False} for p in range(1, total_pages + 1)]
    raw_items = []
    if isinstance(pages_order_input, (list, tuple)):
        raw_items = pages_order_input
    elif isinstance(pages_order_input, str):
        val = pages_order_input.strip()
        if val.startswith('[') or val.startswith('{'):
            try:
                data = json.loads(val)
                if isinstance(data, list):
                    raw_items = data
                else:
                    raw_items = [data]
            except Exception:
                raw_items = val.split(',')
        else:
            raw_items = val.split(',')
    parsed = []
    for item in raw_items:
        if isinstance(item, dict):
            page_val = item.get('page')
            rot = item.get('rotation', 0)
            try:
                rot = int(rot) % 360
            except (ValueError, TypeError):
                rot = 0
            if str(page_val).lower() == 'blank':
                parsed.append({'page': 'blank', 'rotation': rot, 'is_blank': True})
            else:
                try:
                    p = int(page_val)
                    if 1 <= p <= total_pages:
                        parsed.append({'page': p, 'rotation': rot, 'is_blank': False})
                except (ValueError, TypeError):
                    continue
        else:
            item_str = str(item).strip()
            if not item_str:
                continue
            if item_str.lower() == 'blank':
                parsed.append({'page': 'blank', 'rotation': 0, 'is_blank': True})
                continue
            if ':' in item_str:
                parts = item_str.split(':')
                try:
                    p = int(parts[0].strip())
                    rot = int(parts[1].strip()) % 360
                    if 1 <= p <= total_pages:
                        parsed.append({'page': p, 'rotation': rot, 'is_blank': False})
                except (ValueError, TypeError):
                    continue
            elif item_str.isdigit():
                p = int(item_str)
                if 1 <= p <= total_pages:
                    parsed.append({'page': p, 'rotation': 0, 'is_blank': False})
    if not parsed:
        parsed = [{'page': p, 'rotation': 0, 'is_blank': False} for p in range(1, total_pages + 1)]
    return parsed
def apply_page_rotation(page, deg):
    """Safely apply rotation degrees (0, 90, 180, 270) across pypdf and PyPDF2 versions."""
    deg = int(deg) % 360
    if deg == 0:
        return
    if hasattr(page, 'rotate'):
        try:
            page.rotate(deg)
            return
        except Exception:
            pass
    if hasattr(page, 'rotate_clockwise'):
        try:
            page.rotate_clockwise(deg)
            return
        except Exception:
            pass
    if hasattr(page, 'rotateClockwise'):
        try:
            page.rotateClockwise(deg)
            return
        except Exception:
            pass
def organize_pdf_in_memory(pdf_file, pages_order_input):
    """
    Reorders, rotates, and organizes pages of a PDF file.
    Operates 100% in-memory via io.BytesIO.
    Parameters:
        pdf_file: UploadedFile, file-like object, or bytes of the PDF.
        pages_order_input: list, JSON string, or comma string of page dicts/numbers.
    Returns:
        dict: {
            'name': 'document_organized.pdf',
            'bytes': b'...',
            'size': 12345,
            'original_pages': 10,
            'organized_pages_count': 8,
            'order_summary': [3, 1, 2, ...],
            'rotated_count': 2
        }
    """
    # 1. Read input into memory stream
    if hasattr(pdf_file, 'read'):
        raw_bytes = pdf_file.read()
        stream = io.BytesIO(raw_bytes)
    elif isinstance(pdf_file, (bytes, bytearray)):
        stream = io.BytesIO(pdf_file)
    else:
        raise ValueError("Invalid PDF input provided.")
    reader = PdfReader(stream)
    # Decrypt if empty password protected
    if getattr(reader, 'is_encrypted', False):
        try:
            reader.decrypt('')
        except Exception:
            raise ValueError("The PDF file is password protected. Please unlock it before organizing pages.")
    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("The provided PDF has no pages.")
    # 2. Parse ordered sequence and rotations
    ordered_items = parse_pages_order(pages_order_input, total_pages)
    if not ordered_items:
        raise ValueError("Please include at least one page in the organized PDF.")
    # Reference dimensions for blank pages
    first_page = reader.pages[0]
    blank_width = getattr(getattr(first_page, 'mediabox', None), 'width', 595.28)
    blank_height = getattr(getattr(first_page, 'mediabox', None), 'height', 841.89)
    # 3. Assemble organized PDF in memory
    writer = PdfWriter()
    rotated_count = 0
    order_summary = []
    for item in ordered_items:
        rot = item.get('rotation', 0)
        if rot != 0:
            rotated_count += 1
        if item.get('is_blank'):
            try:
                writer.add_blank_page(width=blank_width, height=blank_height)
                order_summary.append('blank')
            except Exception:
                pass
        else:
            p_idx = item['page'] - 1
            if 0 <= p_idx < total_pages:
                # Add page clone
                page = reader.pages[p_idx]
                if rot != 0:
                    apply_page_rotation(page, rot)
                writer.add_page(page)
                order_summary.append(item['page'])
    if len(writer.pages) == 0:
        raise ValueError("The resulting PDF cannot be empty. At least one page must remain.")
    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_bytes = output_stream.getvalue()
    output_stream.close()
    filename = getattr(pdf_file, 'name', 'document.pdf')
    base_name = clean_base_filename(filename)
    return {
        'name': f"{base_name}_organized.pdf",
        'bytes': output_bytes,
        'size': len(output_bytes),
        'original_pages': total_pages,
        'organized_pages_count': len(writer.pages),
        'order_summary': order_summary,
        'rotated_count': rotated_count,
    }
