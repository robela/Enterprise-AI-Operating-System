"""Document text extraction helpers for RAG ingestion and previews."""
from __future__ import annotations

from io import BytesIO

from PyPDF2 import PdfReader


def extract_text(content: bytes, filename: str, content_type: str = "") -> str:
    """Return readable text from a supported document, falling back to plain text."""
    is_pdf = filename.lower().endswith(".pdf") or content_type == "application/pdf"
    if is_pdf:
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
    return content.decode("utf-8", errors="ignore")


def extract_pdf_pages(content: bytes) -> list[str]:
    """Return extracted text per PDF page for the document preview."""
    return [page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages]


def get_pdf_page_count(content: bytes) -> int:
    """Return the number of pages in a PDF document."""
    return len(PdfReader(BytesIO(content)).pages)