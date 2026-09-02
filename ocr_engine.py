"""
ocr_engine.py
OCR Processing Engine using Tesseract via pytesseract.

Renders PDF image-based pages to high-DPI images and extracts:
- Full page text
- Per-word bounding box coordinates and confidence scores
"""

import fitz  # PyMuPDF
import pytesseract
from pytesseract import Output
from PIL import Image
import io
import os
import shutil
from dataclasses import dataclass, field
from typing import List, Optional

# ── Tesseract binary path auto-detection ──
# Checks common Homebrew paths on macOS before falling back to system PATH.
def _find_tesseract() -> str:
    candidates = [
        "/opt/homebrew/bin/tesseract",   # Apple Silicon Homebrew
        "/usr/local/bin/tesseract",       # Intel Homebrew
        shutil.which("tesseract") or "",  # System PATH
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return "tesseract"  # last-resort fallback

pytesseract.pytesseract.tesseract_cmd = _find_tesseract()



@dataclass
class OCRWord:
    """A single word extracted by OCR with its position and confidence."""
    text: str
    left: int           # x-coordinate of left edge (pixels)
    top: int            # y-coordinate of top edge (pixels)
    width: int          # bounding box width (pixels)
    height: int         # bounding box height (pixels)
    confidence: float   # Tesseract confidence 0–100


@dataclass
class OCRResult:
    """Full OCR result for one PDF page."""
    page_number: int
    full_text: str
    words: List[OCRWord] = field(default_factory=list)
    dpi: int = 300


def render_page_to_image(page: fitz.Page, dpi: int = 300) -> Image.Image:
    """
    Renders a PDF page to a high-resolution PIL Image.

    Args:
        page: PyMuPDF Page object.
        dpi: Resolution for rendering (300 recommended for OCR quality).

    Returns:
        PIL Image in RGB mode.
    """
    mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 = PDF point resolution
    pixmap = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img_bytes = pixmap.tobytes("png")
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")


def ocr_image(image: Image.Image, page_number: int = 0, dpi: int = 300) -> OCRResult:
    """
    Runs Tesseract OCR on a PIL Image and extracts text with bounding boxes.

    Args:
        image: PIL Image (should be high-resolution RGB).
        page_number: 0-based page index for metadata.
        dpi: DPI used when rendering (for scale reference).

    Returns:
        OCRResult with full text and per-word word list.
    """
    # Run Tesseract with structured data output (includes bounding boxes)
    data = pytesseract.image_to_data(
        image,
        lang="eng",
        output_type=Output.DICT,
        config="--psm 3",  # Fully automatic page segmentation
    )

    words: List[OCRWord] = []
    n_boxes = len(data["text"])

    for i in range(n_boxes):
        word_text = data["text"][i].strip()
        # Skip empty or low-confidence tokens
        conf = float(data["conf"][i])
        if not word_text or conf < 0:
            continue

        words.append(OCRWord(
            text=word_text,
            left=int(data["left"][i]),
            top=int(data["top"][i]),
            width=int(data["width"][i]),
            height=int(data["height"][i]),
            confidence=conf,
        ))

    full_text = " ".join(w.text for w in words)

    return OCRResult(
        page_number=page_number,
        full_text=full_text,
        words=words,
        dpi=dpi,
    )


def ocr_pdf_page(page: fitz.Page, page_number: int = 0, dpi: int = 300) -> OCRResult:
    """
    End-to-end: renders a PDF page to image, then runs OCR.

    Args:
        page: PyMuPDF Page object.
        page_number: 0-based page index.
        dpi: Rendering resolution.

    Returns:
        OCRResult with text and word bounding boxes.
    """
    image = render_page_to_image(page, dpi=dpi)
    return ocr_image(image, page_number=page_number, dpi=dpi)


def ocr_pdf_page_regions(page: fitz.Page, rects: List[tuple], page_number: int = 0, dpi: int = 300) -> List[OCRResult]:
    """
    Renders the page, but crops to specific rectangles and runs OCR on those crops.
    The resulting bounding boxes in OCRResult are offset back to full-page pixel coordinates.

    Args:
        page: PyMuPDF Page object.
        rects: List of (x0, y0, x1, y1) tuples in PDF points.
        page_number: 0-based page index.
        dpi: Rendering resolution.

    Returns:
        List of OCRResult objects (one per region).
    """
    full_image = render_page_to_image(page, dpi=dpi)
    scale = dpi / 72.0
    
    results = []
    for rect in rects:
        # Convert PDF points to pixels for cropping
        left = int(rect[0] * scale)
        top = int(rect[1] * scale)
        right = int(rect[2] * scale)
        bottom = int(rect[3] * scale)
        
        # Ensure within bounds
        left = max(0, left)
        top = max(0, top)
        right = min(full_image.width, right)
        bottom = min(full_image.height, bottom)
        
        if right <= left or bottom <= top:
            continue
            
        crop_img = full_image.crop((left, top, right, bottom))
        crop_ocr = ocr_image(crop_img, page_number=page_number, dpi=dpi)
        
        # Offset the words back to full-page pixel coordinates
        for word in crop_ocr.words:
            word.left += left
            word.top += top
            
        results.append(crop_ocr)
        
    return results


def find_word_boxes_for_match(match_text: str, ocr_result: OCRResult) -> List[OCRWord]:
    """
    Finds OCR word bounding boxes that correspond to a detected PII match.

    Matches words by comparing OCR word tokens against the detected string.
    Handles multi-word matches (e.g. full names spanning two words).

    Args:
        match_text: The PII string that was detected (e.g. "081234567890").
        ocr_result: The OCRResult from the same page.

    Returns:
        List of OCRWord objects whose text is part of the match.
    """
    match_lower = match_text.lower().strip()
    matched_words = []

    # Single-token match (e.g. NIK, phone, email, NPWP)
    for word in ocr_result.words:
        if match_lower in word.text.lower():
            matched_words.append(word)
            break

    # Multi-token match: try sliding window (e.g. "Budi Santoso")
    if not matched_words:
        tokens = match_lower.split()
        ocr_texts = [w.text.lower() for w in ocr_result.words]
        for start in range(len(ocr_texts) - len(tokens) + 1):
            window = ocr_texts[start: start + len(tokens)]
            if window == tokens:
                matched_words = ocr_result.words[start: start + len(tokens)]
                break

    return matched_words
