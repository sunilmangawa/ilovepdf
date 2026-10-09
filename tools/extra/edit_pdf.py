import io
import re
import os
import json
import base64
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError:
        raise ImportError("Please install either 'pypdf' (pip install pypdf) or 'PyPDF2'.")
# Check for ReportLab (preferred for vector PDF overlay generation)
try:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader as rl_ImageReader
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
# Check for Pillow (fallback for image handling)
try:
    from PIL import Image as PILImage
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
def clean_base_filename(filename):
    """Sanitize and return base filename without extension."""
    if not filename:
        return "document"
    base = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base).strip('._')
    return cleaned or "document"
def create_overlay_pdf_from_image(image_bytes, target_width_pt, target_height_pt):
    """
    Creates a single-page PDF in-memory containing the transparent overlay image,
    sized precisely to the target page dimensions (in points).
    """
    if HAS_REPORTLAB:
        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=(target_width_pt, target_height_pt))
        img = rl_ImageReader(io.BytesIO(image_bytes))
        c.drawImage(img, 0, 0, width=target_width_pt, height=target_height_pt, mask='auto')
        c.save()
        packet.seek(0)
        return packet
    if HAS_PILLOW:
        # Fallback: Convert image to PDF using Pillow in-memory
        img = PILImage.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            # Create white/transparent background RGB canvas for PDF compatibility
            bg = PILImage.new('RGBA', img.size, (255, 255, 255, 0))
            bg.paste(img, (0, 0), img if img.mode == 'RGBA' else None)
            img = bg.convert('RGB')
        packet = io.BytesIO()
        img.save(packet, format='PDF', resolution=72.0)
        packet.seek(0)
        return packet
    raise RuntimeError(
        "Neither ReportLab nor Pillow is installed. Please install reportlab (pip install reportlab) "
        "or pillow (pip install pillow) to merge overlays into PDFs on the server."
    )
def apply_edits_to_pdf_in_memory(pdf_file, overlays_data):
    """
    Applies annotations / overlays to the given PDF in-memory.
    Parameters:
    - pdf_file: UploadedFile, file-like object, or raw bytes.
    - overlays_data: List of dicts or JSON string containing:
        [
            {
                "page": 1,               # 1-based page number
                "dataUrl": "data:image/png;base64,...",  # Transparent PNG overlay
                "width": 595.28,         # Viewport width in points
                "height": 841.89         # Viewport height in points
            },
            ...
        ]
    Returns a dictionary:
    {
        'name': 'document_edited.pdf',
        'bytes': b'...',
        'page_count': 5,
        'size': 123456
    }
    """
    # 1. Read input PDF into memory stream
    if hasattr(pdf_file, 'read'):
        raw_bytes = pdf_file.read()
        stream = io.BytesIO(raw_bytes)
    elif isinstance(pdf_file, (bytes, bytearray)):
        stream = io.BytesIO(pdf_file)
    else:
        raise ValueError("Invalid PDF input provided.")
    reader = PdfReader(stream)
    if getattr(reader, 'is_encrypted', False):
        try:
            reader.decrypt('')
        except Exception:
            raise ValueError("The PDF file is password protected. Please unlock it before editing.")
    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("The provided PDF has no pages.")
    # 2. Parse overlays data
    if isinstance(overlays_data, str):
        try:
            overlays_data = json.loads(overlays_data)
        except Exception:
            overlays_data = []
    if not isinstance(overlays_data, list):
        overlays_data = []
    # Map overlays by page number (1-indexed)
    page_overlays = {}
    for item in overlays_data:
        try:
            p_num = int(item.get('page', 0))
            data_url = item.get('dataUrl') or item.get('image') or ''
            if p_num >= 1 and data_url and ',' in data_url:
                page_overlays[p_num] = {
                    'dataUrl': data_url,
                    'width': float(item.get('width', 0)),
                    'height': float(item.get('height', 0))
                }
        except (ValueError, TypeError):
            continue
    filename = getattr(pdf_file, 'name', 'document.pdf')
    base_name = clean_base_filename(filename)
    output_filename = f"{base_name}_edited.pdf"
    writer = PdfWriter()
    # 3. Process each page
    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        # Check if this page has an overlay
        if page_num in page_overlays:
            overlay_info = page_overlays[page_num]
            data_url = overlay_info['dataUrl']
            # Extract base64 image bytes
            header, encoded = data_url.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            # Determine page dimensions
            # mediabox usually returns (0, 0, width, height)
            media_box = page.mediabox
            page_w = float(media_box.width)
            page_h = float(media_box.height)
            # Generate overlay PDF page
            overlay_stream = create_overlay_pdf_from_image(
                image_bytes=image_bytes,
                target_width_pt=page_w,
                target_height_pt=page_h
            )
            overlay_reader = PdfReader(overlay_stream)
            overlay_page = overlay_reader.pages[0]
            # Merge overlay onto original page
            page.merge_page(overlay_page)
        writer.add_page(page)
    # 4. Write resulting PDF to in-memory buffer
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
