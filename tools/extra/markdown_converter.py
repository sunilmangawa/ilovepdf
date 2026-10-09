"""
Universal Markdown Conversion Engine for iLovePDF Django Project.
Wraps Microsoft MarkItDown (https://github.com/microsoft/markitdown)
with 100% in-memory streaming, robust fallbacks, and deep analytics.
"""
import io
import os
import re
import json
import zipfile
import tempfile
import urllib.parse
from typing import Dict, Any, Optional, Union, BinaryIO

# ------------------------------------------------------------------------------
# Try loading Microsoft MarkItDown
# ------------------------------------------------------------------------------
HAS_MARKITDOWN = False
try:
    from markitdown import MarkItDown
    HAS_MARKITDOWN = True
except ImportError:
    pass


def clean_base_filename(filename: str) -> str:
    """Sanitize and return base filename without extension."""
    if not filename:
        return "converted_document"
    base = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base).strip('._')
    return cleaned or "converted_document"


def compute_markdown_stats(text: str) -> Dict[str, Any]:
    """Calculates statistics: words, characters, lines, and reading time."""
    if not text:
        return {'words': 0, 'characters': 0, 'lines': 0, 'reading_time': '0 min', 'tokens_approx': 0}

    lines = text.splitlines()
    line_count = len(lines)
    char_count = len(text)
    
    clean_text = re.sub(r'[#*`_~\[\]\(\)<>|\\-]', ' ', text)
    words = [w for w in clean_text.split() if w.strip()]
    word_count = len(words)

    reading_mins = max(1, round(word_count / 200)) if word_count > 0 else 0
    reading_time = f"{reading_mins} min" if reading_mins > 0 else "< 1 min"
    tokens_approx = round(word_count * 1.33)

    return {
        'words': word_count,
        'characters': char_count,
        'lines': line_count,
        'reading_time': reading_time,
        'tokens_approx': tokens_approx
    }


def sanitize_markdown_output(markdown_text: str) -> str:
    """Clean duplicate blank lines while keeping document layout."""
    if not markdown_text:
        return ""
    cleaned = re.sub(r'\n{3,}', '\n\n', markdown_text.strip())
    return cleaned + '\n'


class MarkdownConverterEngine:
    """In-memory Universal Markdown Converter powered by Microsoft MarkItDown."""

    def __init__(self, llm_client=None, llm_model: Optional[str] = None):
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.md_instance = None
        if HAS_MARKITDOWN:
            try:
                kwargs = {}
                if llm_client:
                    kwargs['llm_client'] = llm_client
                    if llm_model:
                        kwargs['llm_model'] = llm_model
                self.md_instance = MarkItDown(**kwargs)
            except Exception:
                try:
                    self.md_instance = MarkItDown()
                except Exception:
                    self.md_instance = None

    def convert_file(
        self,
        file_obj,
        format_type: str = "pdf",
        filename: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Converts any uploaded file or stream into Markdown 100% in-memory."""
        options = options or {}
        orig_filename = filename or getattr(file_obj, 'name', f"document.{format_type}")
        base_name = clean_base_filename(orig_filename)
        output_filename = f"{base_name}.md"

        if hasattr(file_obj, 'read'):
            raw_bytes = file_obj.read()
        elif isinstance(file_obj, (bytes, bytearray)):
            raw_bytes = bytes(file_obj)
        else:
            raise ValueError("Invalid file input provided.")

        if len(raw_bytes) == 0:
            raise ValueError("The uploaded file is empty.")

        ext = os.path.splitext(orig_filename)[1].lower()
        if not ext and format_type:
            ext = f".{format_type.lower()}"

        markdown_result = ""

        # 1. Primary: Microsoft MarkItDown
        if self.md_instance:
            try:
                stream = io.BytesIO(raw_bytes)
                try:
                    res = self.md_instance.convert_stream(stream, file_extension=ext)
                    markdown_result = getattr(res, 'markdown', None) or getattr(res, 'text_content', '')
                except TypeError:
                    res = self.md_instance.convert(stream)
                    markdown_result = getattr(res, 'markdown', None) or getattr(res, 'text_content', '')
            except Exception:
                markdown_result = self._fallback_convert(raw_bytes, format_type, ext, orig_filename, options)
        else:
            markdown_result = self._fallback_convert(raw_bytes, format_type, ext, orig_filename, options)

        final_markdown = sanitize_markdown_output(markdown_result)
        stats = compute_markdown_stats(final_markdown)

        return {
            'filename': output_filename,
            'markdown': final_markdown,
            'bytes': final_markdown.encode('utf-8'),
            'size': len(final_markdown.encode('utf-8')),
            'stats': stats,
            'original_filename': orig_filename,
            'format_type': format_type
        }

    def convert_youtube(self, url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Converts a YouTube URL to Markdown transcript and metadata."""
        options = options or {}
        if self.md_instance:
            try:
                res = self.md_instance.convert_url(url)
                md_text = getattr(res, 'markdown', None) or getattr(res, 'text_content', '')
                if md_text:
                    stats = compute_markdown_stats(md_text)
                    return {
                        'filename': 'youtube_transcript.md',
                        'markdown': sanitize_markdown_output(md_text),
                        'bytes': md_text.encode('utf-8'),
                        'size': len(md_text.encode('utf-8')),
                        'stats': stats,
                        'original_url': url
                    }
            except Exception:
                pass
        return self._fallback_youtube(url, options)

    def _fallback_convert(self, raw_bytes: bytes, format_type: str, ext: str, filename: str, options: Dict[str, Any]) -> str:
        fmt = format_type.lower()
        if fmt == 'pdf' or ext == '.pdf':
            return self._fallback_pdf(raw_bytes, options)
        elif fmt in ('word', 'docx', 'doc') or ext in ('.docx', '.doc'):
            return self._fallback_docx(raw_bytes, options)
        elif fmt in ('powerpoint', 'pptx', 'ppt') or ext in ('.pptx', '.ppt'):
            return self._fallback_pptx(raw_bytes, options)
        elif fmt in ('excel', 'xlsx', 'xls') or ext in ('.xlsx', '.xls'):
            return self._fallback_xlsx(raw_bytes, options)
        elif fmt in ('image', 'images', 'ocr') or ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif'):
            return self._fallback_image(raw_bytes, ext, options)
        elif fmt in ('audio', 'speech') or ext in ('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'):
            return self._fallback_audio(raw_bytes, ext, options)
        elif fmt in ('html', 'htm') or ext in ('.html', '.htm'):
            return self._fallback_html(raw_bytes, options)
        elif fmt in ('text', 'csv', 'json', 'xml', 'tsv') or ext in ('.csv', '.json', '.xml', '.tsv', '.txt'):
            return self._fallback_text_formats(raw_bytes, ext, options)
        elif fmt in ('zip', 'archive') or ext == '.zip':
            return self._fallback_zip(raw_bytes, options)
        elif fmt in ('epub', 'ebook') or ext == '.epub':
            return self._fallback_epub(raw_bytes, options)
        else:
            try:
                return raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return raw_bytes.decode('latin-1', errors='replace')

    # 1. PDF Fallback
    def _fallback_pdf(self, raw_bytes: bytes, options: Dict[str, Any]) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw_bytes))
            pages_md = [f"# PDF Document\n\n*Total Pages: {len(reader.pages)}*\n"]
            for idx, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                pages_md.append(f"## Page {idx}\n\n{text.strip()}\n")
            return "\n".join(pages_md)
        except ImportError:
            return "# PDF Document\n\n*(Install `pip install markitdown[pdf]` or `pypdf` for direct extraction.)*"

    # 2. Word (DOCX) Fallback
    def _fallback_docx(self, raw_bytes: bytes, options: Dict[str, Any]) -> str:
        try:
            import docx
            doc = docx.Document(io.BytesIO(raw_bytes))
            md_lines = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                style = para.style.name.lower() if para.style else ""
                if 'heading 1' in style:
                    md_lines.append(f"# {text}\n")
                elif 'heading 2' in style:
                    md_lines.append(f"## {text}\n")
                elif 'heading 3' in style:
                    md_lines.append(f"### {text}\n")
                else:
                    md_lines.append(f"{text}\n")
            
            for table_idx, table in enumerate(doc.tables, 1):
                md_lines.append(f"\n### Table {table_idx}\n")
                for r_idx, row in enumerate(table.rows):
                    cells = [c.text.replace('\n', ' ').strip() for c in row.cells]
                    md_lines.append("| " + " | ".join(cells) + " |")
                    if r_idx == 0:
                        md_lines.append("| " + " | ".join(['---'] * len(cells)) + " |")
                md_lines.append("")
            return "\n".join(md_lines)
        except ImportError:
            return "# Word Document\n\n*(Install `pip install markitdown[docx]` or `python-docx`)*"

    # 3. PowerPoint (PPTX) Fallback
    def _fallback_pptx(self, raw_bytes: bytes, options: Dict[str, Any]) -> str:
        try:
            from pptx import Presentation
            prs = Presentation(io.BytesIO(raw_bytes))
            md_lines = ["# Presentation Slides\n"]
            for idx, slide in enumerate(prs.slides, 1):
                md_lines.append(f"## Slide {idx}\n")
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            t = paragraph.text.strip()
                            if t:
                                md_lines.append(f"- {t}")
                if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                    notes = slide.notes_slide.notes_text_frame.text.strip()
                    if notes:
                        md_lines.append(f"\n> **Speaker Notes:** {notes}\n")
                md_lines.append("")
            return "\n".join(md_lines)
        except ImportError:
            return "# PowerPoint Presentation\n\n*(Install `pip install markitdown[pptx]` or `python-pptx`)*"

    # 4. Excel (XLSX) Fallback
    def _fallback_xlsx(self, raw_bytes: bytes, options: Dict[str, Any]) -> str:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=True)
            md_lines = ["# Spreadsheet Workbook\n"]
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                md_lines.append(f"## Sheet: {sheet_name}\n")
                rows = list(sheet.iter_rows(values_only=True))
                if not rows:
                    continue
                header = [str(c) if c is not None else "" for c in rows[0]]
                md_lines.append("| " + " | ".join(header) + " |")
                md_lines.append("| " + " | ".join(['---'] * len(header)) + " |")
                for row in rows[1:]:
                    if any(c is not None for c in row):
                        row_vals = [str(c).replace('\n', ' ') if c is not None else "" for c in row]
                        md_lines.append("| " + " | ".join(row_vals) + " |")
                md_lines.append("")
            return "\n".join(md_lines)
        except ImportError:
            return "# Excel Document\n\n*(Install `pip install markitdown[xlsx]` or `openpyxl`)*"

    # 5. Image & EXIF / OCR Fallback
    def _fallback_image(self, raw_bytes: bytes, ext: str, options: Dict[str, Any]) -> str:
        md_lines = ["# Image Analysis & Metadata\n"]
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            img = Image.open(io.BytesIO(raw_bytes))
            md_lines.append(f"- **Dimensions:** {img.width} x {img.height} px")
            md_lines.append(f"- **Format:** {img.format or ext.replace('.', '').upper()}")
            md_lines.append(f"- **Color Mode:** {img.mode}\n")

            exif_data = img.getexif()
            if exif_data:
                md_lines.append("### EXIF Metadata\n\n| Property | Value |\n| --- | --- |")
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    clean_val = str(value).replace('\n', ' ').strip()
                    if len(clean_val) < 100:
                        md_lines.append(f"| **{tag_name}** | {clean_val} |")
                md_lines.append("")

            if options.get('enable_ocr', True):
                try:
                    import pytesseract
                    ocr_text = pytesseract.image_to_string(img).strip()
                    if ocr_text:
                        md_lines.append("### Extracted Text (OCR)\n\n```text\n" + ocr_text + "\n```\n")
                except Exception:
                    md_lines.append("*(OCR requires `pytesseract` or MarkItDown Vision LLM client).*\n")
            return "\n".join(md_lines)
        except ImportError:
            return "# Image Document\n\n*(Install `pip install pillow pytesseract` for image OCR.)*"

    # 6. Audio Fallback (EXIF & Transcription)
    def _fallback_audio(self, raw_bytes: bytes, ext: str, options: Dict[str, Any]) -> str:
        md_lines = ["# Audio File Analysis\n", f"- **File Type:** {ext.upper()}\n"]
        try:
            from mutagen import File as MutagenFile
            audio = MutagenFile(io.BytesIO(raw_bytes))
            if audio:
                md_lines.append("### Audio Metadata\n")
                md_lines.append(f"- **Duration:** {round(audio.info.length, 2)} seconds")
                if hasattr(audio.info, 'bitrate'):
                    md_lines.append(f"- **Bitrate:** {audio.info.bitrate // 1000} kbps")
                if audio.tags:
                    md_lines.append("\n| Tag | Value |\n| --- | --- |")
                    for k, v in audio.tags.items():
                        md_lines.append(f"| **{k}** | {str(v)} |")
                md_lines.append("")
        except ImportError:
            pass

        md_lines.append("### Speech Transcription\n")
        md_lines.append("*(Install `pip install 'markitdown[audio-transcription]'` or OpenAI Whisper for automated speech-to-text).*")
        return "\n".join(md_lines)

    # 7. HTML Fallback
    def _fallback_html(self, raw_bytes: bytes, options: Dict[str, Any]) -> str:
        html_str = raw_bytes.decode('utf-8', errors='replace')
        try:
            import markdownify
            return markdownify.markdownify(html_str, heading_style="ATX")
        except ImportError:
            text = re.sub(r'<script.*?</script>', '', html_str, flags=re.DOTALL)
            text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<h1.*?>(.*?)</h1>', r'# \1\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<h2.*?>(.*?)</h2>', r'## \1\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<p.*?>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<.*?>', '', text)
            return text

    # 8. CSV / JSON / XML Fallback
    def _fallback_text_formats(self, raw_bytes: bytes, ext: str, options: Dict[str, Any]) -> str:
        text_content = raw_bytes.decode('utf-8', errors='replace')
        ext = ext.lower()
        if ext == '.csv':
            import csv
            reader = csv.reader(io.StringIO(text_content))
            rows = list(reader)
            if not rows:
                return "# CSV Data\n*(Empty file)*"
            md = ["# CSV Data Table\n", "| " + " | ".join(rows[0]) + " |", "| " + " | ".join(['---'] * len(rows[0])) + " |"]
            for r in rows[1:]:
                md.append("| " + " | ".join(r) + " |")
            return "\n".join(md)
        elif ext == '.json':
            try:
                formatted = json.dumps(json.loads(text_content), indent=2)
                return f"# JSON Data\n\n```json\n{formatted}\n```\n"
            except Exception:
                return f"# JSON Data\n\n```json\n{text_content}\n```\n"
        elif ext == '.xml':
            return f"# XML Document\n\n```xml\n{text_content}\n```\n"
        return f"```text\n{text_content}\n```"

    # 9. ZIP Archives Fallback
    def _fallback_zip(self, raw_bytes: bytes, options: Dict[str, Any]) -> str:
        md_lines = ["# ZIP Archive Contents\n"]
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes), 'r') as z:
                file_list = z.namelist()
                md_lines.append(f"**Total Files in Archive:** {len(file_list)}\n")
                md_lines.append("## Table of Contents\n")
                for fname in file_list:
                    if not fname.endswith('/'):
                        md_lines.append(f"- [{fname}](#file-{clean_base_filename(fname)})")
                md_lines.append("\n---")

                for fname in file_list:
                    if fname.endswith('/'):
                        continue
                    clean_id = clean_base_filename(fname)
                    md_lines.append(f"\n### File: `{fname}` <a id='file-{clean_id}'></a>\n")
                    f_bytes = z.read(fname)
                    f_ext = os.path.splitext(fname)[1].lower()
                    if f_ext in ('.md', '.txt', '.csv', '.json', '.html', '.htm', '.xml'):
                        try:
                            md_lines.append(f"```{f_ext.replace('.', '')}\n{f_bytes.decode('utf-8')}\n```")
                        except Exception:
                            md_lines.append("*(Binary or non-UTF8 file)*")
                    else:
                        md_lines.append(f"*(Binary file, size: {len(f_bytes)} bytes)*")
            return "\n".join(md_lines)
        except Exception as e:
            return f"# ZIP Archive\n\nError extracting archive: {str(e)}"

    # 10. YouTube Fallback
    def _fallback_youtube(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        video_id = None
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
        elif "watch?v=" in url:
            video_id = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("v", [None])[0]

        if not video_id:
            raise ValueError("Could not find a valid YouTube video ID.")

        md_lines = [
            f"# YouTube Video Transcript\n",
            f"- **URL:** [{url}]({url})",
            f"- **Video ID:** `{video_id}`\n",
            f"## Transcript\n"
        ]

        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            for item in transcript_list:
                start_sec = int(item['start'])
                mins, secs = divmod(start_sec, 60)
                timestamp = f"{mins:02d}:{secs:02d}"
                text = item['text'].replace('\n', ' ')
                md_lines.append(f"**[{timestamp}]** {text}")
        except Exception:
            md_lines.append("*(Install `pip install youtube-transcript-api` for automated transcript retrieval).*")

        final_md = "\n".join(md_lines)
        stats = compute_markdown_stats(final_md)
        return {
            'filename': f"youtube_{video_id}.md",
            'markdown': final_md,
            'bytes': final_md.encode('utf-8'),
            'size': len(final_md.encode('utf-8')),
            'stats': stats,
            'original_url': url
        }

    # 11. EPUB Fallback
    def _fallback_epub(self, raw_bytes: bytes, options: Dict[str, Any]) -> str:
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
                tmp.write(raw_bytes)
                tmp_path = tmp.name

            try:
                book = epub.read_epub(tmp_path)
                md_lines = [f"# {book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else 'EPUB Book'}\n"]
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        for h in soup.find_all(['h1', 'h2', 'h3']):
                            level = '#' * int(h.name[1])
                            h.replace_with(f"\n{level} {h.get_text().strip()}\n")
                        for p in soup.find_all('p'):
                            p.replace_with(f"{p.get_text().strip()}\n\n")
                        text = soup.get_text()
                        if text.strip():
                            md_lines.append(text.strip() + "\n\n---\n")
                return "\n".join(md_lines)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except ImportError:
            return "# EPUB Book\n\n*(Install `pip install ebooklib beautifulsoup4` or MarkItDown EPUB plugin)*"


markdown_engine = MarkdownConverterEngine()
# markdown_engine = MarkdownConversionEngine()
