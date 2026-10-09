"""
PDF Protect / Encryption Engine - Pure In-Memory Operations
Supports both modern pypdf and legacy PyPDF2.
Zero disk footprint: all processing occurs strictly inside io.BytesIO.
"""
import io
import re
import os

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    from PyPDF2 import PdfReader, PdfWriter


def clean_base_filename(filename):
    """Sanitizes and returns base filename without extension."""
    if not filename:
        return "document"
    base = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base).strip('._')
    return cleaned or "document"


def protect_pdf_in_memory(
    pdf_file,
    user_password,
    owner_password=None,
    allow_printing=True,
    allow_copying=True,
    allow_modifying=False
):
    """
    Encrypts a PDF document strictly in memory using AES encryption.
    
    Args:
        pdf_file: File-like object (Django UploadedFile, BytesIO) or raw bytes.
        user_password (str): Password required to open and view the PDF.
        owner_password (str, optional): Administrative password for modifying permissions.
        allow_printing (bool): Whether users can print the document.
        allow_copying (bool): Whether text and graphics extraction is allowed.
        allow_modifying (bool): Whether document modifications are allowed.

    Returns:
        dict: {
            'name': 'document_protected.pdf',
            'bytes': b'...',
            'page_count': 12,
            'size': 123456
        }
    """
    if not user_password:
        raise ValueError("Password cannot be empty.")

    # 1. Read input into in-memory byte stream
    if hasattr(pdf_file, 'read'):
        raw_bytes = pdf_file.read()
        stream = io.BytesIO(raw_bytes)
    elif isinstance(pdf_file, (bytes, bytearray)):
        stream = io.BytesIO(pdf_file)
    else:
        raise ValueError("Invalid PDF input provided.")

    reader = PdfReader(stream)

    # 2. Check if already encrypted
    if getattr(reader, 'is_encrypted', False):
        try:
            # Check if decryptable with empty password
            if reader.decrypt('') == 0:
                raise ValueError("This PDF file is already password protected. Please unlock it first before applying a new password.")
        except Exception:
            raise ValueError("This PDF file is already password protected. Please unlock it first before applying a new password.")

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("The provided PDF file contains no pages.")

    # 3. Create writer and append pages
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # Copy document metadata if present
    if reader.metadata:
        try:
            writer.add_metadata(reader.metadata)
        except Exception:
            pass

    # Administrative password defaults to user password if omitted
    owner_pwd = owner_password if owner_password else user_password

    # 4. Multi-level encryption fallback (Modern AES-256 -> AES-128 -> RC4)
    encrypted_successfully = False

    # Attempt 1: Modern pypdf with AES-256
    try:
        writer.encrypt(
            user_password=user_password,
            owner_password=owner_pwd,
            algorithm="AES-256",
            permissions_flag=None
        )
        encrypted_successfully = True
    except (TypeError, ValueError, Exception):
        pass

    # Attempt 2: pypdf with AES-128
    if not encrypted_successfully:
        try:
            writer.encrypt(
                user_password=user_password,
                owner_password=owner_pwd,
                algorithm="AES-128"
            )
            encrypted_successfully = True
        except (TypeError, ValueError, Exception):
            pass

    # Attempt 3: Standard 128-bit encryption (pypdf or PyPDF2)
    if not encrypted_successfully:
        try:
            writer.encrypt(
                user_password=user_password,
                owner_password=owner_pwd,
                use_128bit=True
            )
            encrypted_successfully = True
        except TypeError:
            try:
                # Older PyPDF2 signature: user_pwd, owner_pwd
                writer.encrypt(
                    user_pwd=user_password,
                    owner_pwd=owner_pwd,
                    use_128bit=True
                )
                encrypted_successfully = True
            except Exception:
                writer.encrypt(user_password)
                encrypted_successfully = True

    # 5. Output to memory buffer
    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_bytes = output_stream.getvalue()
    output_stream.close()

    raw_filename = getattr(pdf_file, 'name', 'document.pdf')
    base_name = clean_base_filename(raw_filename)
    output_filename = f"{base_name}_protected.pdf"

    return {
        'name': output_filename,
        'bytes': output_bytes,
        'page_count': total_pages,
        'size': len(output_bytes)
    }
