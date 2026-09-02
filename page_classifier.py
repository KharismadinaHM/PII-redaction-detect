"""
page_classifier.py
PDF Page Classification Module — determines whether each page contains
extractable native text or is image-based (requiring OCR).

Uses PyMuPDF (fitz) for PDF parsing and text extraction.
"""

import fitz  # PyMuPDF
from dataclasses import dataclass, field
from typing import List

# Minimum character count threshold to consider a page as having meaningful
# native text. Pages below this threshold are classified as image-based.
MIN_TEXT_CHARS = 30


@dataclass
class PageInfo:
    """Classification result for a single PDF page."""
    page_number: int            # 0-indexed page number
    classification: str         # "native-text" or "image-based"
    native_text: str            # Extracted text (empty for image-based pages)
    char_count: int             # Number of extracted text characters
    has_images: bool            # Whether the page contains embedded images
    width: float = 0.0          # Page width in points
    height: float = 0.0         # Page height in points


def classify_page(page: fitz.Page, page_index: int) -> PageInfo:
    """
    Classifies a single PDF page as native-text or image-based.

    Heuristic: if the page yields fewer than MIN_TEXT_CHARS characters
    of extractable text, it is considered image-based and will need OCR.

    Args:
        page: A PyMuPDF Page object.
        page_index: 0-based page index.

    Returns:
        PageInfo dataclass with classification result.
    """
    text = page.get_text("text").strip()
    char_count = len(text)
    images = page.get_images(full=True)
    has_images = len(images) > 0
    rect = page.rect

    if char_count >= MIN_TEXT_CHARS:
        classification = "native-text"
    else:
        classification = "image-based"

    return PageInfo(
        page_number=page_index,
        classification=classification,
        native_text=text if classification == "native-text" else "",
        char_count=char_count,
        has_images=has_images,
        width=rect.width,
        height=rect.height,
    )


def classify_pdf(pdf_path: str) -> List[PageInfo]:
    """
    Opens a PDF file and classifies every page.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        Ordered list of PageInfo objects, one per page.
    """
    doc = fitz.open(pdf_path)
    results = []
    for i, page in enumerate(doc):
        info = classify_page(page, i)
        results.append(info)
    doc.close()
    return results


def classify_pdf_bytes(pdf_bytes: bytes) -> List[PageInfo]:
    """
    Classifies pages of a PDF provided as raw bytes (e.g. from Streamlit upload).

    Args:
        pdf_bytes: Raw PDF file content.

    Returns:
        Ordered list of PageInfo objects.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    results = []
    for i, page in enumerate(doc):
        info = classify_page(page, i)
        results.append(info)
    doc.close()
    return results
