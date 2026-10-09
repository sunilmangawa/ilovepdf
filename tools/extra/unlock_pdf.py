"""
PDF Unlock Engine - Pure In-Memory Operations
Removes passwords and security restrictions from PDF documents.
Prioritizes pikepdf (handles 100% of modern AES-256 / Acrobat X encryptions),
with fallback to modern pypdf and legacy PyPDF2.
No files are saved to disk; all processing uses io.BytesIO.
"""
import io
import os
import re

# Tier 1: pikepdf (Best-in-class for removal of owner/user passwords and repairing encrypted xrefs)
try:
    import pikepdf
    HAS_PIKEPDF = True
except ImportError:
    pikepdf = None
    HAS_PIKEPDF = False

# Tier 2 & 3: pypdf / PyPDF2
try:
    from pypdf import PdfReader, PdfWriter
    try:
        from pypdf.errors import PasswordError, EmptyFileError
    except ImportError:
        PasswordError = Exception
        EmptyFileError = Exception
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
        PasswordError = Exception
        EmptyFileError = Exception
    except ImportError:
        PdfReader = None
        PdfWriter = None
        PasswordError = Exception
        EmptyFileError = Exception


def clean_base_filename(filename):
    """Sanitize and return base filename without extension."""
    if not filename:
        return "document"
    base = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base).strip('._')
    return cleaned or "document"


def unlock_pdf_in_memory(pdf_file, password=""):
    """
    Unlocks a password-protected PDF completely in-memory.
    
    Args:
        pdf_file: File-like object (e.g. InMemoryUploadedFile, BytesIO) or raw bytes.
        password: String password provided by the user (optional for restriction-only PDFs).
        
    Returns:
        dict: {
            'name': 'document_unlocked.pdf',
            'bytes': b'...',
            'size': int,
            'page_count': int,
            'was_encrypted': bool
        }
    """
    if hasattr(pdf_file, 'read'):
        raw_bytes = pdf_file.read()
    elif isinstance(pdf_file, (bytes, bytearray)):
        raw_bytes = bytes(pdf_file)
    else:
        raise ValueError("Invalid PDF input provided.")

    if not raw_bytes or len(raw_bytes) < 8:
        raise ValueError("The provided file is empty or corrupted.")

    original_name = getattr(pdf_file, 'name', 'document.pdf')
    base_name = clean_base_filename(original_name)
    output_filename = f"{base_name}_unlocked.pdf"

    user_password = (password or "").strip()

    # -------------------------------------------------------------------------
    # STRATEGY A: pikepdf (handles 128-bit/256-bit AES, standard owner/user security)
    # -------------------------------------------------------------------------
    if HAS_PIKEPDF:
        try:
            input_stream = io.BytesIO(raw_bytes)
            # Try with user-supplied password (or empty string for owner-restriction-only PDFs)
            try:
                pdf = pikepdf.open(input_stream, password=user_password)
            except pikepdf.PasswordError:
                # If no password was provided, try empty password explicitly
                if not user_password:
                    try:
                        pdf = pikepdf.open(input_stream, password="")
                    except pikepdf.PasswordError:
                        raise ValueError("This PDF is password-protected. Please enter the correct password to unlock it.")
                else:
                    raise ValueError("Incorrect password. Please verify the password and try again.")

            was_encrypted = pdf.is_encrypted

            # Save unencrypted to in-memory buffer
            output_stream = io.BytesIO()
            # Saving with no encryption parameters removes all security & passwords
            pdf.save(output_stream)
            page_count = len(pdf.pages)
            pdf.close()

            output_bytes = output_stream.getvalue()
            return {
                'name': output_filename,
                'bytes': output_bytes,
                'size': len(output_bytes),
                'page_count': page_count,
                'was_encrypted': was_encrypted
            }
        except (ValueError, Exception) as e:
            if "password" in str(e).lower():
                raise
            # If pikepdf encountered a non-password parsing anomaly, fall through to pypdf

    # -------------------------------------------------------------------------
    # STRATEGY B: pypdf / PyPDF2
    # -------------------------------------------------------------------------
    if PdfReader is None:
        raise RuntimeError("No PDF processing library available. Please install 'pypdf' or 'pikepdf'.")

    stream = io.BytesIO(raw_bytes)
    try:
        reader = PdfReader(stream)
    except Exception as e:
        raise ValueError(f"Could not parse PDF file: {str(e)}")

    was_encrypted = getattr(reader, 'is_encrypted', False)

    if was_encrypted:
        decrypt_success = False

        # Attempt 1: Try user-provided password
        if user_password:
            try:
                result = reader.decrypt(user_password)
                if result in (1, 2) or result is True:
                    decrypt_success = True
            except Exception:
                decrypt_success = False

        # Attempt 2: If no password or failed, try empty string (bypasses owner restrictions)
        if not decrypt_success:
            try:
                result = reader.decrypt("")
                if result in (1, 2) or result is True:
                    decrypt_success = True
            except Exception:
                pass

        if not decrypt_success:
            if not user_password:
                raise ValueError("This PDF file is password protected. Please enter the password to unlock it.")
            else:
                raise ValueError("Incorrect password. Please enter the valid password to unlock this file.")

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("The provided PDF has no pages.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # Preserve metadata if available
    try:
        if reader.metadata:
            writer.add_metadata(reader.metadata)
    except Exception:
        pass

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_bytes = output_stream.getvalue()

    return {
        'name': output_filename,
        'bytes': output_bytes,
        'size': len(output_bytes),
        'page_count': total_pages,
        'was_encrypted': was_encrypted
    }
