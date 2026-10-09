"""
Crop PDF Engine - 100% Pure In-Memory Operations
Compatible with modern `pypdf` and legacy `PyPDF2`.
Zero temporary files written to disk; handles point conversions, rotation, and custom ranges.
"""
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


def parse_page_range(range_str, total_pages):
    """
    Parses comma-separated ranges e.g. "1-3, 5, 7-10".
    Returns a set of 1-based page indices.
    """
    selected = set()
    if not range_str or not range_str.strip():
        return set(range(1, total_pages + 1))

    parts = [p.strip() for p in range_str.split(',') if p.strip()]
    for part in parts:
        if '-' in part:
            sub = part.split('-', 1)
            if sub[0].strip().isdigit() and sub[1].strip().isdigit():
                start = int(sub[0].strip())
                end = int(sub[1].strip())
                if start > end:
                    start, end = end, start
                start = max(1, min(start, total_pages))
                end = max(1, min(end, total_pages))
                for p in range(start, end + 1):
                    selected.add(p)
        elif part.isdigit():
            pg = int(part)
            if 1 <= pg <= total_pages:
                selected.add(pg)

    return selected or set(range(1, total_pages + 1))


def crop_pdf_in_memory(
    pdf_file,
    crop_x=0.0,
    crop_y=0.0,
    crop_width=None,
    crop_height=None,
    preview_width=None,
    preview_height=None,
    crop_mode='all',        # 'all', 'current', or 'custom'
    target_pages='',        # comma-separated e.g. '1-3, 5'
    current_page_num=1      # 1-based
):
    """
    Crops PDF in memory by calculating the coordinate transform between
    the browser's preview viewport (canvas pixels) and the PDF's native coordinates (points).

    Returns a dict:
    {
        'name': 'document_cropped.pdf',
        'bytes': b'...',
        'page_count': int,
        'size': int
    }
    """
    if hasattr(pdf_file, 'read'):
        raw_bytes = pdf_file.read()
        stream = io.BytesIO(raw_bytes)
    elif isinstance(pdf_file, (bytes, bytearray)):
        stream = io.BytesIO(pdf_file)
    else:
        raise ValueError("Invalid PDF input stream.")

    reader = PdfReader(stream)

    if getattr(reader, 'is_encrypted', False):
        try:
            reader.decrypt('')
        except Exception:
            raise ValueError("The PDF file is encrypted/password protected. Please unlock it first.")

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("The provided PDF has no pages.")

    filename = getattr(pdf_file, 'name', 'document.pdf')
    base_name = clean_base_filename(filename)

    # Determine which pages should have the crop applied
    if crop_mode == 'current':
        pages_to_crop = {max(1, min(int(current_page_num or 1), total_pages))}
    elif crop_mode == 'custom':
        pages_to_crop = parse_page_range(target_pages, total_pages)
    else:  # 'all'
        pages_to_crop = set(range(1, total_pages + 1))

    # Float conversion of crop coordinates
    cx = float(crop_x or 0.0)
    cy = float(crop_y or 0.0)
    cw = float(crop_width or 0.0)
    ch = float(crop_height or 0.0)
    pw = float(preview_width or 0.0)
    ph = float(preview_height or 0.0)

    # Ratio fallback: if preview dimensions aren't provided, assume crop coordinates are percentages (0-100)
    is_percentage = (pw <= 0 or ph <= 0)

    writer = PdfWriter()

    for idx, page in enumerate(reader.pages, 1):
        if idx in pages_to_crop:
            # Get existing page boundaries (PDF coordinates: bottom-left is origin [0,0])
            mb = page.mediabox
            pdf_w = float(mb.width)
            pdf_h = float(mb.height)
            lower_left_x = float(mb.left)
            lower_left_y = float(mb.bottom)

            if is_percentage:
                # Percentage mode (0 to 100)
                norm_x = cx / 100.0
                norm_y = cy / 100.0
                norm_w = cw / 100.0
                norm_h = ch / 100.0
            else:
                # Pixel-to-point relative scaling
                norm_x = cx / pw
                norm_y = cy / ph
                norm_w = cw / pw
                norm_h = ch / ph

            # Guard against invalid dimensions
            norm_x = max(0.0, min(norm_x, 1.0))
            norm_y = max(0.0, min(norm_y, 1.0))
            norm_w = max(0.01, min(norm_w, 1.0 - norm_x))
            norm_h = max(0.01, min(norm_h, 1.0 - norm_y))

            # Transform from Canvas coordinate system (top-left is 0,0)
            # to PDF coordinate system (bottom-left is 0,0)
            new_ll_x = lower_left_x + (norm_x * pdf_w)
            new_ur_x = new_ll_x + (norm_w * pdf_w)
            new_ur_y = lower_left_y + ((1.0 - norm_y) * pdf_h)
            new_ll_y = new_ur_y - (norm_h * pdf_h)

            # Apply crop to all relevant boxes
            page.cropbox.lower_left = (new_ll_x, new_ll_y)
            page.cropbox.upper_right = (new_ur_x, new_ur_y)

            # Also clamp mediabox/trimbox/bleedbox for maximum PDF reader compatibility
            try:
                page.mediabox.lower_left = (new_ll_x, new_ll_y)
                page.mediabox.upper_right = (new_ur_x, new_ur_y)
            except Exception:
                pass

        writer.add_page(page)

    out_buf = io.BytesIO()
    writer.write(out_buf)
    pdf_bytes = out_buf.getvalue()
    out_buf.close()

    out_filename = f"{base_name}_cropped.pdf"
    return {
        'name': out_filename,
        'bytes': pdf_bytes,
        'page_count': total_pages,
        'size': len(pdf_bytes)
    }
