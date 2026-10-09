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
    # Keep alphanumeric, underscores, hyphens
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base).strip('._')
    return cleaned or "document"


def parse_extract_selection(selection_str, total_pages):
    """
    Parses page selection strings like '1-3, 5, 7-10'.
    Returns list of group dicts:
    [
        {'type': 'range', 'start': 1, 'end': 3, 'pages': [1, 2, 3]},
        {'type': 'single', 'start': 5, 'end': 5, 'pages': [5]},
        {'type': 'range', 'start': 7, 'end': 10, 'pages': [7, 8, 9, 10]}
    ]
    """
    groups = []
    if not selection_str:
        return groups

    parts = [p.strip() for p in selection_str.split(',') if p.strip()]
    for part in parts:
        if '-' in part:
            sub = part.split('-')
            if len(sub) == 2 and sub[0].strip().isdigit() and sub[1].strip().isdigit():
                start = int(sub[0].strip())
                end = int(sub[1].strip())
                if start > end:
                    start, end = end, start
                start = max(1, min(start, total_pages))
                end = max(1, min(end, total_pages))
                if start <= end:
                    groups.append({
                        'type': 'range',
                        'start': start,
                        'end': end,
                        'pages': list(range(start, end + 1))
                    })
        elif part.isdigit():
            pg = int(part)
            if 1 <= pg <= total_pages:
                groups.append({
                    'type': 'single',
                    'start': pg,
                    'end': pg,
                    'pages': [pg]
                })
    return groups


def parse_custom_ranges(ranges_data, total_pages):
    """
    Parses ranges data supplied as:
    - JSON string or list of dicts: [{'start': 1, 'end': 3}, {'start': 5, 'end': 8}]
    - Or comma-separated string: '1-3, 5-8'
    """
    parsed = []
    if not ranges_data:
        return [{'start': 1, 'end': total_pages}]

    if isinstance(ranges_data, str):
        ranges_data = ranges_data.strip()
        # Try JSON first
        if ranges_data.startswith('['):
            try:
                ranges_data = json.loads(ranges_data)
            except Exception:
                ranges_data = []

    if isinstance(ranges_data, list):
        for item in ranges_data:
            try:
                start = int(item.get('start', 1))
                end = int(item.get('end', total_pages))
                if start > end:
                    start, end = end, start
                start = max(1, min(start, total_pages))
                end = max(1, min(end, total_pages))
                if start <= end:
                    parsed.append({'start': start, 'end': end})
            except (ValueError, TypeError, AttributeError):
                continue
    elif isinstance(ranges_data, str):
        # Fallback to string parsing '1-3, 5-8'
        for part in ranges_data.split(','):
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                sub = part.split('-', 1)
                if sub[0].strip().isdigit() and sub[1].strip().isdigit():
                    s = int(sub[0].strip())
                    e = int(sub[1].strip())
                    if s > e:
                        s, e = e, s
                    s = max(1, min(s, total_pages))
                    e = max(1, min(e, total_pages))
                    if s <= e:
                        parsed.append({'start': s, 'end': e})
            elif part.isdigit():
                pg = int(part)
                if 1 <= pg <= total_pages:
                    parsed.append({'start': pg, 'end': pg})

    if not parsed:
        parsed = [{'start': 1, 'end': total_pages}]
    return parsed


def split_pdf_in_memory(
    pdf_file,
    split_mode='range',
    range_type='custom',
    ranges=None,
    fixed_range_size=1,
    merge_ranges=False,
    extract_type='select',
    extract_pages_str='',
    merge_extract=False
):
    """
    Main PDF splitting processor. Operates 100% in-memory via io.BytesIO.
    Returns a list of dictionaries:
    [
        {
            'name': 'document_range_1-3.pdf',
            'bytes': b'...',
            'page_count': 3,
            'size': 123456
        },
        ...
    ]
    """
    # 1. Read input file into memory stream
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
            # Try decrypting with empty password
            reader.decrypt('')
        except Exception:
            raise ValueError("The PDF file is password protected. Please unlock it before splitting.")

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("The provided PDF has no pages.")

    filename = getattr(pdf_file, 'name', 'document.pdf')
    base_name = clean_base_filename(filename)
    output_files = []

    # -------------------------------------------------------------------------
    # MODE 1: SPLIT BY RANGE
    # -------------------------------------------------------------------------
    if split_mode == 'range':
        # Sub-mode A: Custom ranges
        if range_type == 'custom':
            custom_ranges = parse_custom_ranges(ranges, total_pages)

            if merge_ranges:
                # Merge all ranges into a single output PDF
                writer = PdfWriter()
                page_count = 0
                for r in custom_ranges:
                    for p in range(r['start'] - 1, r['end']):
                        writer.add_page(reader.pages[p])
                        page_count += 1
                if page_count > 0:
                    buf = io.BytesIO()
                    writer.write(buf)
                    val = buf.getvalue()
                    buf.close()
                    output_files.append({
                        'name': f"{base_name}_merged_ranges.pdf",
                        'bytes': val,
                        'page_count': page_count,
                        'size': len(val)
                    })
            else:
                # Output ONE PDF per range (no zipping!)
                for r in custom_ranges:
                    writer = PdfWriter()
                    for p in range(r['start'] - 1, r['end']):
                        writer.add_page(reader.pages[p])
                    count = r['end'] - r['start'] + 1
                    buf = io.BytesIO()
                    writer.write(buf)
                    val = buf.getvalue()
                    buf.close()

                    if r['start'] == r['end']:
                        out_name = f"{base_name}_range_page_{r['start']}.pdf"
                    else:
                        out_name = f"{base_name}_range_{r['start']}-{r['end']}.pdf"

                    output_files.append({
                        'name': out_name,
                        'bytes': val,
                        'page_count': count,
                        'size': len(val)
                    })

        # Sub-mode B: Fixed ranges (e.g. split every N pages)
        elif range_type == 'fixed':
            try:
                fixed_size = max(1, int(fixed_range_size))
            except (ValueError, TypeError):
                fixed_size = 1

            chunk_idx = 1
            for start_idx in range(0, total_pages, fixed_size):
                end_idx = min(start_idx + fixed_size, total_pages)
                writer = PdfWriter()
                for p in range(start_idx, end_idx):
                    writer.add_page(reader.pages[p])
                count = end_idx - start_idx
                buf = io.BytesIO()
                writer.write(buf)
                val = buf.getvalue()
                buf.close()

                s_num = start_idx + 1
                e_num = end_idx
                if s_num == e_num:
                    out_name = f"{base_name}_part_{chunk_idx}_page_{s_num}.pdf"
                else:
                    out_name = f"{base_name}_part_{chunk_idx}_pages_{s_num}-{e_num}.pdf"

                output_files.append({
                    'name': out_name,
                    'bytes': val,
                    'page_count': count,
                    'size': len(val)
                })
                chunk_idx += 1

    # -------------------------------------------------------------------------
    # MODE 2: EXTRACT PAGES
    # -------------------------------------------------------------------------
    elif split_mode == 'extract':
        # Sub-mode A: Extract all pages into individual PDFs
        if extract_type == 'all':
            if merge_extract:
                # Merge all pages (reconstructed single PDF)
                writer = PdfWriter()
                for p in reader.pages:
                    writer.add_page(p)
                buf = io.BytesIO()
                writer.write(buf)
                val = buf.getvalue()
                buf.close()
                output_files.append({
                    'name': f"{base_name}_all_pages.pdf",
                    'bytes': val,
                    'page_count': total_pages,
                    'size': len(val)
                })
            else:
                for idx, page in enumerate(reader.pages, 1):
                    writer = PdfWriter()
                    writer.add_page(page)
                    buf = io.BytesIO()
                    writer.write(buf)
                    val = buf.getvalue()
                    buf.close()
                    output_files.append({
                        'name': f"{base_name}_page_{idx}.pdf",
                        'bytes': val,
                        'page_count': 1,
                        'size': len(val)
                    })

        # Sub-mode B: Select pages (e.g. '1-3, 5, 7-10' -> 3 separate PDFs)
        else:
            groups = parse_extract_selection(extract_pages_str, total_pages)
            if not groups:
                raise ValueError("Please provide valid pages or page ranges to extract.")

            if merge_extract:
                # Merge selected into 1 PDF
                writer = PdfWriter()
                page_count = 0
                for g in groups:
                    for pg in g['pages']:
                        writer.add_page(reader.pages[pg - 1])
                        page_count += 1
                buf = io.BytesIO()
                writer.write(buf)
                val = buf.getvalue()
                buf.close()
                output_files.append({
                    'name': f"{base_name}_extracted_pages.pdf",
                    'bytes': val,
                    'page_count': page_count,
                    'size': len(val)
                })
            else:
                # Each range or single page gets its own separate PDF without zipping
                for g in groups:
                    writer = PdfWriter()
                    for pg in g['pages']:
                        writer.add_page(reader.pages[pg - 1])
                    buf = io.BytesIO()
                    writer.write(buf)
                    val = buf.getvalue()
                    buf.close()

                    if g['type'] == 'single':
                        out_name = f"{base_name}_page_{g['start']}.pdf"
                    else:
                        out_name = f"{base_name}_pages_{g['start']}-{g['end']}.pdf"

                    output_files.append({
                        'name': out_name,
                        'bytes': val,
                        'page_count': len(g['pages']),
                        'size': len(val)
                    })

    if not output_files:
        raise ValueError("No pages could be extracted with the given parameters.")

    return output_files


def split_pdf_by_page(pdf_file, page_numbers=''):
    """
    Backwards compatibility helper:
    Preserved for any external references, now executed 100% in-memory.
    """
    return split_pdf_in_memory(
        pdf_file=pdf_file,
        split_mode='extract' if page_numbers else 'range',
        extract_pages_str=page_numbers,
        merge_extract=False
    )
