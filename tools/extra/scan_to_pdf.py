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
    Returns PIL.Image object in RGB mode with EXIF orientation auto-corrected.
    """
    if not HAS_PIL:
        raise RuntimeError("Pillow is required for image processing. Please run: pip install pillow")

    if hasattr(image_input, 'read'):
        raw = image_input.read()
        stream = io.BytesIO(raw)
        img = Image.open(stream)
    elif isinstance(image_input, (bytes, bytearray)):
        stream = io.BytesIO(image_input)
        img = Image.open(stream)
    elif isinstance(image_input, str):
        data_str = image_input.strip()
        if ',' in data_str and data_str.startswith('data:'):
            data_str = data_str.split(',', 1)[1]
        raw = base64.b64decode(data_str)
        stream = io.BytesIO(raw)
        img = Image.open(stream)
    else:
        raise ValueError("Unsupported image input type.")

    # Automatically correct image orientation based on EXIF tags (essential for mobile camera shots)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Normalize to RGB mode (safely handle RGBA transparency or CMYK)
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
    - 'original': Retains natural photo colors
    - 'grayscale': High fidelity 8-bit document monochrome
    - 'bw_document': CamScanner-style high-contrast document cleaner
                     (eliminates shadows, creases, yellow paper tints, and sharpens text)
    - 'magic_color': Boosts saturation and contrast for color stamps, IDs, and certificates
    """
    if filter_type == 'grayscale':
        gray = ImageOps.grayscale(image)
        return gray.convert('RGB')

    elif filter_type == 'bw_document':
        # 1. Convert to grayscale
        gray = ImageOps.grayscale(image)
        # 2. Sharpen letter edges
        sharpened = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        # 3. Enhance contrast
        contrasted = ImageEnhance.Contrast(sharpened).enhance(2.2)
        # 4. Adaptive thresholding curve: bright paper background -> pure 255 white; text -> deep black
        table = []
        for i in range(256):
            if i > 185:
                table.append(255)
            elif i < 60:
                table.append(0)
            else:
                val = int(((i - 60) / (185 - 60)) ** 1.3 * 255)
                table.append(max(0, min(255, val)))
        cleaned = contrasted.point(table, 'L')
        return cleaned.convert('RGB')

    elif filter_type == 'magic_color':
        # Boost contrast, saturation, and edge sharpness
        boosted = ImageEnhance.Contrast(image).enhance(1.35)
        vibrant = ImageEnhance.Color(boosted).enhance(1.4)
        bright = ImageEnhance.Brightness(vibrant).enhance(1.05)
        return bright.filter(ImageFilter.SHARPEN)

    return image


def layout_image_on_page(image, page_size='a4', orientation='portrait', margin='none', dpi=200):
    """
    Scales and positions an image onto a standard page canvas (A4, Letter, Legal, or Auto)
    with specified orientation and margins.
    Returns a PIL Image matching exact target canvas dimensions at given DPI.
    """
    PAGE_SIZES_PT = {
        'a4': (595.28, 841.89),       # 210 x 297 mm
        'letter': (612.0, 792.0),     # 8.5 x 11 in
        'legal': (612.0, 1008.0),     # 8.5 x 14 in
    }

    MARGINS_PT = {
        'none': 0.0,
        'small': 28.35,   # ~10 mm
        'normal': 56.7,   # ~20 mm
    }

    margin_pt = MARGINS_PT.get(margin, 0.0)

    # Auto sizing: Canvas matches image aspect ratio directly
    if page_size == 'auto':
        img_w, img_h = image.size
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
    else:
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

    available_w = max(10, canvas_w - (2 * margin_px))
    available_h = max(10, canvas_h - (2 * margin_px))

    # Calculate aspect-ratio preserved scaling
    img_ratio = img_w / float(img_h)
    target_ratio = available_w / float(available_h)

    if img_ratio > target_ratio:
        new_w = available_w
        new_h = int(available_w / img_ratio)
    else:
        new_h = available_h
        new_w = int(available_h * img_ratio)

    new_w = max(1, new_w)
    new_h = max(1, new_h)

    resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Center on white canvas
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
    crops=None,
    merge_pdf=True
):
    """
    Main Scan to PDF In-Memory Processor.
    Operates 100% in-memory via io.BytesIO.
    
    Supports:
    - Pre-cropped client-side base64 images OR server-side crop coordinates in `crops`
    - Per-page rotations and filters
    - Standard paper sizing and DPI control
    - 100% in-memory multi-page or single-page PDF generation
    """
    if not images:
        raise ValueError("No images provided for PDF generation.")

    DPI_MAP = {'high': 300, 'recommended': 200, 'compact': 150}
    JPEG_QUALITY_MAP = {'high': 95, 'recommended': 82, 'compact': 65}
    target_dpi = DPI_MAP.get(quality, 200)
    target_jpeg_quality = JPEG_QUALITY_MAP.get(quality, 82)

    rotations = rotations or []
    filters = filters or []
    crops = crops or []
    processed_pages = []

    for idx, img_input in enumerate(images):
        # 1. Decode & EXIF Transpose
        pil_img = decode_image_data(img_input)

        # 2. Server-side Crop (if explicit crop box is supplied and image not pre-cropped)
        if crops and idx < len(crops) and crops[idx]:
            c = crops[idx]
            try:
                x = max(0, int(c.get('x', 0)))
                y = max(0, int(c.get('y', 0)))
                w = int(c.get('w', c.get('width', 0)))
                h = int(c.get('h', c.get('height', 0)))
                if w > 0 and h > 0:
                    pil_img = pil_img.crop((x, y, min(pil_img.width, x + w), min(pil_img.height, y + h)))
            except Exception:
                pass

        # 3. Per-page Rotation (0, 90, 180, 270)
        rot_deg = 0
        if idx < len(rotations):
            try:
                rot_deg = int(rotations[idx]) % 360
            except (ValueError, TypeError):
                rot_deg = 0
        if rot_deg in (90, 180, 270):
            pil_img = pil_img.rotate(360 - rot_deg, expand=True)

        # 4. Document Filter
        page_filter = filter_type
        if idx < len(filters) and filters[idx]:
            page_filter = filters[idx]
        pil_img = apply_document_filter(pil_img, page_filter)

        # 5. Canvas Layout & DPI Normalization
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
        # Merge all into single cohesive multi-page PDF
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
        # Individual single-page PDFs
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
