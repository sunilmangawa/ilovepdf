"""
In-Memory Scan to PDF Engine
Supports Pillow (PIL) for image processing, EXIF transposition,
document filters, paper formatting, and multi-page PDF generation.
100% In-Memory via io.BytesIO (Zero disk storage usage).
"""
import io
import re
import os
import json
import base64
from datetime import datetime
try:
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
def clean_base_filename(filename, default="Scan"):
    """Sanitize and return base filename without extension."""
    if not filename:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        return f"{default}_{timestamp}"
    base = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base).strip('._')
    if not cleaned:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        return f"{default}_{timestamp}"
    return cleaned
def decode_image_data(image_input):
    """
    Accepts:
    - Django UploadedFile / InMemoryUploadedFile
    - Raw bytes or bytearray
    - Base64 Data URL string (e.g. 'data:image/jpeg;base64,...') or raw base64 string
    Returns PIL.Image object in RGB mode.
    """
    if not HAS_PIL:
        raise RuntimeError("Pillow is required for image processing. Please install pillow.")
    if hasattr(image_input, 'read'):
        raw = image_input.read()
        stream = io.BytesIO(raw)
        img = Image.open(stream)
    elif isinstance(image_input, (bytes, bytearray)):
        stream = io.BytesIO(image_input)
        img = Image.open(stream)
    elif isinstance(image_input, str):
        # Base64 string
        data_str = image_input.strip()
        if ',' in data_str and data_str.startswith('data:'):
            data_str = data_str.split(',', 1)[1]
        raw = base64.b64decode(data_str)
        stream = io.BytesIO(raw)
        img = Image.open(stream)
    else:
        raise ValueError("Unsupported image input type.")
    # Automatically correct image orientation based on EXIF tags (crucial for mobile camera photos)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    # Ensure RGB format (convert RGBA, palette, or CMYK safely)
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    return img
def apply_document_filter(image, filter_type='original'):
    """
    Applies image enhancement filter:
    - 'original': Keeps natural colors with mild contrast balance
    - 'grayscale': High fidelity monochrome
    - 'bw_document': High-contrast document cleaner (wipes shadows, sharpens text)
    - 'magic_color': Boosts contrast and color saturation for stamps, certificates, badges
    """
    if filter_type == 'grayscale':
        gray = ImageOps.grayscale(image)
        return gray.convert('RGB')
    elif filter_type == 'bw_document':
        # Step 1: Convert to grayscale
        gray = ImageOps.grayscale(image)
        # Step 2: Unsharp mask to enhance letter edges
        sharpened = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        # Step 3: Contrast stretch
        contrasted = ImageEnhance.Contrast(sharpened).enhance(2.2)
        # Step 4: High-contrast thresholding with smooth tone preservation
        # Pixels > 185 become pure white (eliminates shadow/creases), darker pixels boosted
        table = []
        for i in range(256):
            if i > 185:
                table.append(255)
            elif i < 60:
                table.append(0)
            else:
                # Dynamic curve
                val = int(((i - 60) / (185 - 60)) ** 1.3 * 255)
                table.append(max(0, min(255, val)))
        cleaned = contrasted.point(table, 'L')
        return cleaned.convert('RGB')
    elif filter_type == 'magic_color':
        # Boost contrast
        enhancer = ImageEnhance.Contrast(image)
        boosted = enhancer.enhance(1.35)
        # Boost color saturation
        color_enhancer = ImageEnhance.Color(boosted)
        vibrant = color_enhancer.enhance(1.4)
        # Slight brightness balance
        bright = ImageEnhance.Brightness(vibrant).enhance(1.05)
        # Mild sharpening for text legibility
        sharp = bright.filter(ImageFilter.SHARPEN)
        return sharp
    # Default 'original'
    return image
def layout_image_on_page(image, page_size='a4', orientation='portrait', margin='none', dpi=200):
    """
    Positions and scales an image onto a standard page canvas (A4, Letter, Legal, or Auto)
    with specified orientation and margins.
    Returns PIL Image matching exact target canvas dimensions at given DPI.
    """
    # Standard dimensions in points (1 pt = 1/72 inch)
    PAGE_SIZES_PT = {
        'a4': (595.28, 841.89),       # 210 x 297 mm
        'letter': (612.0, 792.0),     # 8.5 x 11 in
        'legal': (612.0, 1008.0),     # 8.5 x 14 in
    }
    # Margin values in points
    MARGINS_PT = {
        'none': 0.0,
        'small': 28.35,   # ~10 mm
        'normal': 56.7,   # ~20 mm
    }
    margin_pt = MARGINS_PT.get(margin, 0.0)
    # Determine canvas dimensions
    if page_size == 'auto':
        # Fit page directly to image aspect ratio
        img_w, img_h = image.size
        # Margin in pixels directly proportional to image dimensions
        margin_px = int((margin_pt / 72.0) * dpi) if margin_pt > 0 else 0
        canvas_w = img_w + 2 * margin_px
        canvas_h = img_h + 2 * margin_px
        canvas = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
        canvas.paste(image, (margin_px, margin_px))
        return canvas
    pt_w, pt_h = PAGE_SIZES_PT.get(page_size, PAGE_SIZES_PT['a4'])
    # Determine orientation
    img_w, img_h = image.size
    if orientation == 'auto':
        is_landscape = img_w > img_h
    elif orientation == 'landscape':
        is_landscape = True
    else: # portrait
        is_landscape = False
    if is_landscape:
        page_w_pt = max(pt_w, pt_h)
        page_h_pt = min(pt_w, pt_h)
    else:
        page_w_pt = min(pt_w, pt_h)
        page_h_pt = max(pt_w, pt_h)
    # Convert points to pixels at specified DPI
    scale_factor = dpi / 72.0
    canvas_w = int(page_w_pt * scale_factor)
    canvas_h = int(page_h_pt * scale_factor)
    margin_px = int(margin_pt * scale_factor)
    # Available printable area
    available_w = max(10, canvas_w - (2 * margin_px))
    available_h = max(10, canvas_h - (2 * margin_px))
    # Calculate aspect-ratio preserved scaling
    img_ratio = img_w / float(img_h)
    target_ratio = available_w / float(available_h)
    if img_ratio > target_ratio:
        # Width constrained
        new_w = available_w
        new_h = int(available_w / img_ratio)
    else:
        # Height constrained
        new_h = available_h
        new_w = int(available_h * img_ratio)
    new_w = max(1, new_w)
    new_h = max(1, new_h)
    # Resize image with high-quality resampling
    resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    # Create white canvas and center resized image
    canvas = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
    paste_x = margin_px + (available_w - new_w) // 2
    paste_y = margin_px + (available_h - new_h) // 2
    canvas.paste(resized_img, (paste_x, paste_y))
    return canvas
def scan_to_pdf_in_memory(
    images,
    output_filename="Scan.pdf",
    page_size="a4",
    orientation="portrait",
    margin="none",
    filter_type="original",
    quality="recommended",
    rotations=None,
    filters=None,
    merge_pdf=True
):
    """
    Main Scan to PDF Processing Engine.
    Operates 100% in-memory via io.BytesIO.
    
    Parameters:
    - images: list of image inputs (UploadedFiles, base64 strings, or raw bytes)
    - output_filename: base output filename
    - page_size: 'a4', 'letter', 'legal', 'auto'
    - orientation: 'auto', 'portrait', 'landscape'
    - margin: 'none', 'small', 'normal'
    - filter_type: global filter ('original', 'grayscale', 'bw_document', 'magic_color')
    - quality: 'high' (300 DPI, q=95), 'recommended' (200 DPI, q=82), 'compact' (150 DPI, q=65)
    - rotations: list of rotation degrees per page [0, 90, 180, 270, ...]
    - filters: optional list of per-page filter names
    - merge_pdf: if True, merges all into 1 PDF; if False, generates individual PDFs per page.
    
    Returns:
    List of file dicts:
    [
        {
            'name': 'Scan_Document.pdf',
            'bytes': b'...',
            'page_count': 5,
            'size': 456789
        },
        ...
    ]
    """
    if not images:
        raise ValueError("No images provided for PDF generation.")
    # Quality settings
    DPI_MAP = {'high': 300, 'recommended': 200, 'compact': 150}
    JPEG_QUALITY_MAP = {'high': 95, 'recommended': 82, 'compact': 65}
    target_dpi = DPI_MAP.get(quality, 200)
    target_jpeg_quality = JPEG_QUALITY_MAP.get(quality, 82)
    rotations = rotations or []
    filters = filters or []
    processed_pages = []
    for idx, img_input in enumerate(images):
        # 1. Decode & Transpose
        pil_img = decode_image_data(img_input)
        # 2. Page Rotation (if specified)
        rot_deg = 0
        if idx < len(rotations):
            try:
                rot_deg = int(rotations[idx]) % 360
            except (ValueError, TypeError):
                rot_deg = 0
        if rot_deg in (90, 180, 270):
            # PIL rotate counter-clockwise by default, so use -rot_deg or expand=True
            pil_img = pil_img.rotate(360 - rot_deg, expand=True)
        # 3. Document Filter
        page_filter = filter_type
        if idx < len(filters) and filters[idx]:
            page_filter = filters[idx]
        pil_img = apply_document_filter(pil_img, page_filter)
        # 4. Canvas & Layout
        page_canvas = layout_image_on_page(
            pil_img,
            page_size=page_size,
            orientation=orientation,
            margin=margin,
            dpi=target_dpi
        )
        processed_pages.append(page_canvas)
    if not processed_pages:
        raise ValueError("Failed to process scanned images.")
    base_name = clean_base_filename(output_filename, default="Scan")
    output_files = []
    if merge_pdf:
        # Merge all pages into a single PDF
        pdf_stream = io.BytesIO()
        first_page = processed_pages[0]
        other_pages = processed_pages[1:] if len(processed_pages) > 1 else []
        first_page.save(
            pdf_stream,
            format='PDF',
            save_all=True,
            append_images=other_pages,
            resolution=float(target_dpi),
            quality=target_jpeg_quality
        )
        pdf_bytes = pdf_stream.getvalue()
        output_files.append({
            'name': f"{base_name}.pdf",
            'bytes': pdf_bytes,
            'page_count': len(processed_pages),
            'size': len(pdf_bytes)
        })
    else:
        # Separate single-page PDF for each page
        for i, page in enumerate(processed_pages, start=1):
            pdf_stream = io.BytesIO()
            page.save(
                pdf_stream,
                format='PDF',
                resolution=float(target_dpi),
                quality=target_jpeg_quality
            )
            pdf_bytes = pdf_stream.getvalue()
            output_files.append({
                'name': f"{base_name}_page_{i}.pdf",
                'bytes': pdf_bytes,
                'page_count': 1,
                'size': len(pdf_bytes)
            })
    return output_files
