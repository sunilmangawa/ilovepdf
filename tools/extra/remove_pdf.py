"""
PDF Remove Pages Engine - Pure In-Memory Operations
Supports both pypdf (modern) and PyPDF2 (legacy).
No files are saved to disk; all processing uses io.BytesIO.
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


def parse_pages_to_remove(selection, total_pages):
    """
    Parses pages to remove from various formats:
    - Comma-separated string with ranges: '1, 4-6, 8'
    - JSON array: '[1, 4, 5, 6, 8]' or '["1", "4-6", "8"]'
    - List of integers or strings: [1, 4, 5, 6, 8]

    Returns a sorted list of unique 1-indexed page integers to remove.
    """
    removed = set()
    if not selection:
        return []

    if isinstance(selection, (list, tuple, set)):
        items = selection
    else:
        sel_str = str(selection).strip()
        if sel_str.startswith('['):
            try:
                items = json.loads(sel_str)
            except Exception:
                items = [sel_str]
        else:
            items = sel_str.split(',')

    for item in items:
        part = str(item).strip()
        if not part:
            continue
        if '-' in part:
            sub = part.split('-')
            if len(sub) == 2 and sub[0].strip().isdigit() and sub[1].strip().isdigit():
                start = int(sub[0].strip())
                end = int(sub[1].strip())
                if start > end:
                    start, end = end, start
                start = max(1, min(start, total_pages))
                end = max(1, min(end, total_pages))
                for p in range(start, end + 1):
                    removed.add(p)
        elif part.isdigit():
            p = int(part)
            if 1 <= p <= total_pages:
                removed.add(p)

    return sorted(list(removed))


def format_pages_to_ranges(page_list):
    """
    Converts a sorted list of page numbers into compressed ranges string.
    Example: [1, 4, 5, 6, 8] -> "1, 4-6, 8"
    """
    if not page_list:
        return ""
    sorted_pages = sorted(list(set(page_list)))
    ranges = []
    start = sorted_pages[0]
    end = sorted_pages[0]

    for p in sorted_pages[1:]:
        if p == end + 1:
            end = p
        else:
            ranges.append(f"{start}" if start == end else f"{start}-{end}")
            start = end = p
    ranges.append(f"{start}" if start == end else f"{start}-{end}")
    return ", ".join(ranges)


def remove_pdf_in_memory(pdf_file, pages_to_remove_input):
    """
    Removes selected pages from the PDF file.
    Operates 100% in-memory via io.BytesIO.

    Parameters:
        pdf_file: UploadedFile, file-like object, or bytes of the PDF.
        pages_to_remove_input: string, list, or JSON specifying pages to delete.

    Returns:
        dict: {
            'name': 'document_removed.pdf',
            'bytes': b'...',
            'size': 12345,
            'original_pages': 10,
            'removed_pages_count': 3,
            'removed_pages_list': [1, 4, 5],
            'removed_pages_str': '1, 4-5',
            'final_page_count': 7
        }
    """
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
            raise ValueError("The PDF file is password protected. Please unlock it before removing pages.")

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("The provided PDF has no pages.")

    removed_pages = parse_pages_to_remove(pages_to_remove_input, total_pages)
    if not removed_pages:
        raise ValueError("Please select at least one page to remove.")

    removed_set = set(removed_pages)
    keep_pages = [p for p in range(1, total_pages + 1) if p not in removed_set]

    if not keep_pages:
        raise ValueError("You cannot remove all pages from the PDF. At least one page must remain.")

    writer = PdfWriter()
    for p in keep_pages:
        writer.add_page(reader.pages[p - 1])

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_bytes = output_stream.getvalue()
    output_stream.close()

    filename = getattr(pdf_file, 'name', 'document.pdf')
    base_name = clean_base_filename(filename)

    return {
        'name': f"{base_name}_removed.pdf",
        'bytes': output_bytes,
        'size': len(output_bytes),
        'original_pages': total_pages,
        'removed_pages_count': len(removed_pages),
        'removed_pages_list': removed_pages,
        'removed_pages_str': format_pages_to_ranges(removed_pages),
        'final_page_count': len(keep_pages),
    }
