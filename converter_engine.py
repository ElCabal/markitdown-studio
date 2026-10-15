import io
import re
from pathlib import Path
from typing import Optional, Tuple
import pymupdf
import pymupdf4llm
from markitdown import MarkItDown

# Singleton MarkItDown converter instance
_markitdown_instance: Optional[MarkItDown] = None

def get_markitdown() -> MarkItDown:
    global _markitdown_instance
    if _markitdown_instance is None:
        _markitdown_instance = MarkItDown()
    return _markitdown_instance

def clean_markdown(text: str) -> str:
    """
    Post-processes extracted Markdown:
    - Strips form-feed and binary artifacts
    - Corrects spaced-out tracking/kerning letters (e.g. "G U Í A" -> "GUÍA")
    - Removes isolated page numbers and running headers (e.g. "02 / 15")
    - Normalizes unicode bullet points to standard Markdown lists ("- ")
    - Cleans up excessive whitespace
    """
    if not text:
        return ""

    # 1. Clean form-feed characters
    text = text.replace('\x0c', '\n\n')

    # 2. Fix spaced-out letters / kerning (e.g. "G U Í A   N A T U R A L" -> "GUÍA NATURAL")
    def collapse_spaced_phrase(match):
        phrase = match.group(0)
        parts = re.split(r'\s{2,}', phrase)
        collapsed = [re.sub(r'\s+', '', p) for p in parts if p.strip()]
        return ' '.join(collapsed)

    text = re.sub(
        r'\b(?:[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]\s+){2,}[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]\b(?:\s{2,}\b(?:[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]\s+){2,}[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]\b)*',
        collapse_spaced_phrase,
        text
    )

    # 3. Strip page numbers and running footers like "02 / 15" or "Página 3 de 10"
    text = re.sub(r'(?m)^\s*(?:\d{1,3}\s*/\s*\d{1,3}|P[aá]g(?:ina)?\.?\s*\d+(?:\s*(?:de|of)\s*\d+)?)\s*$', '', text)

    # 4. Normalize raw unicode bullets into Markdown list dashes
    lines = []
    for line in text.split('\n'):
        line = re.sub(r'^[ \t]*[•●○■◆▪]\s*', '- ', line)
        lines.append(line)
    text = '\n'.join(lines)

    # 5. Clean up multiple empty lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def convert_document(content_bytes: bytes, filename: str, ext: Optional[str] = None) -> Tuple[str, dict]:
    """
    Converts document bytes into high-quality Markdown.
    Uses pymupdf4llm for PDFs (multi-column layout analysis + font-based headings),
    and MarkItDown for all other supported formats (Office, Excel, Word, HTML, etc.).
    """
    if not ext:
        ext = Path(filename).suffix.lower()
    else:
        ext = ext.lower()

    metadata = {"engine": "markitdown"}

    # Special handling for PDF: pymupdf4llm delivers superior layout analysis
    if ext == ".pdf":
        try:
            doc = pymupdf.open(stream=content_bytes, filetype="pdf")
            raw_md = pymupdf4llm.to_markdown(doc)
            cleaned_md = clean_markdown(raw_md)
            metadata["engine"] = "pymupdf4llm"
            metadata["page_count"] = len(doc)
            return cleaned_md, metadata
        except Exception as e:
            # Fallback to MarkItDown if pymupdf encounters an unexpected error
            metadata["pdf_fallback_error"] = str(e)

    # Universal engine (MarkItDown) for docx, xlsx, pptx, html, csv, audio, etc.
    md_converter = get_markitdown()
    stream = io.BytesIO(content_bytes)
    res = md_converter.convert_stream(stream, file_extension=ext)
    raw_md = res.text_content or getattr(res, "markdown", "") or ""
    cleaned_md = clean_markdown(raw_md)
    return cleaned_md, metadata

def convert_url(url: str) -> Tuple[str, str, dict]:
    """
    Converts a URL (web page or YouTube video) using MarkItDown.
    """
    md_converter = get_markitdown()
    res = md_converter.convert(url.strip())
    raw_md = res.text_content or getattr(res, "markdown", "") or ""
    title = getattr(res, "title", "transcripcion") or "transcripcion"
    cleaned_md = clean_markdown(raw_md)
    return cleaned_md, title, {"engine": "markitdown"}
