"""
redactor.py
PII Redaction and Masking Module.

Redaction Modes:
- MASK_PARTIAL: Partially masks sensitive values (e.g., 0812****5678, B*** A***)
- REDACT_FULL:  Completely replaces sensitive values with typed tokens (e.g., [REDACTED-NIK])
"""

import re
import pandas as pd
from typing import Dict, Optional
from detector import analyze_dataframe, PATTERNS


# ──────────────────────────────────────────────
# Masking Functions per PII Type
# ──────────────────────────────────────────────

def mask_nik(nik: str) -> str:
    """Mask NIK: displays first 4 and last 4 digits → 3201********0001."""
    nik = str(nik).strip()
    if len(nik) >= 8:
        return nik[:4] + "*" * (len(nik) - 8) + nik[-4:]
    return "*" * len(nik)


def mask_phone(phone: str) -> str:
    """Mask phone number: displays first 4 and last 4 digits → 0812****5678."""
    phone = str(phone).strip()
    if len(phone) >= 8:
        return phone[:4] + "*" * (len(phone) - 8) + phone[-4:]
    return "*" * len(phone)


def mask_email(email: str) -> str:
    """Mask email: displays first 2 characters + domain → bu**@gmail.com."""
    email = str(email).strip()
    if "@" in email:
        local, domain = email.rsplit("@", 1)
        if len(local) > 2:
            masked_local = local[:2] + "*" * (len(local) - 2)
        else:
            masked_local = local[0] + "*" * (len(local) - 1) if local else "*"
        return f"{masked_local}@{domain}"
    return "*" * len(email)


def mask_npwp(npwp: str) -> str:
    """Mask NPWP (Tax ID): displays first 2 digits, masks subsequent digits → 12.***.***.* -***. ***."""
    npwp = str(npwp).strip()
    if len(npwp) >= 5:
        return npwp[:3] + re.sub(r"\d", "*", npwp[3:])
    return "*" * len(npwp)


def mask_name(name: str) -> str:
    """Mask person name: displays first character of each word + asterisks → B*** A***."""
    name = str(name).strip()
    words = name.split()
    masked = []
    for word in words:
        if len(word) > 1:
            masked.append(word[0] + "*" * (len(word) - 1))
        elif word:
            masked.append(word[0] + "***")
    return " ".join(masked)


# ──────────────────────────────────────────────
# Full Redaction Placeholder
# ──────────────────────────────────────────────

def redact_full(value: str, pii_type: str) -> str:
    """Full redaction: replaces entire value with typed token."""
    return f"[REDACTED-{pii_type}]"


# ──────────────────────────────────────────────
# Masking Dispatcher
# ──────────────────────────────────────────────

MASK_FUNCTIONS = {
    "NIK": mask_nik,
    "NO_HP": mask_phone,
    "EMAIL": mask_email,
    "NPWP": mask_npwp,
    "NAMA": mask_name,
}


def redact_value(value: str, pii_detected: Dict, mode: str = "mask") -> str:
    """
    Redacts a single cell value based on detected PII entities.

    Args:
        value: Original cell value.
        pii_detected: Dictionary of detected PII {pii_type: [matches]}.
        mode: "mask" for partial masking, "full" for complete token replacement.

    Returns:
        Redacted cell string.
    """
    if not pii_detected:
        return value

    result = str(value)

    for pii_type, matches in pii_detected.items():
        if mode == "full":
            return redact_full(result, pii_type)
        else:
            if pii_type == "NAMA":
                mask_fn = MASK_FUNCTIONS.get(pii_type, lambda x: "****")
                result = mask_fn(result)
            else:
                mask_fn = MASK_FUNCTIONS.get(pii_type, lambda x: "****")
                for match in matches:
                    masked = mask_fn(match)
                    result = result.replace(match, masked)

    return result


def redact_dataframe(
    df: pd.DataFrame,
    mode: str = "mask",
    use_ner: bool = True,
) -> tuple:
    """
    Redacts an entire pandas DataFrame.

    Args:
        df: Original pandas DataFrame.
        mode: "mask" (partial) or "full" (complete replacement).
        use_ner: Whether to apply spaCy NER for person name recognition.

    Returns:
        Tuple containing:
        - df_redacted: Redacted pandas DataFrame.
        - detail: Per-cell PII detection details.
        - summary: Aggregate PII counts per type.
    """
    detail, summary = analyze_dataframe(df, use_ner=use_ner)

    df_redacted = df.copy()

    for idx in df_redacted.index:
        if idx in detail:
            for col in df_redacted.columns:
                if col in detail[idx]:
                    original_value = str(df_redacted.at[idx, col])
                    pii_found = detail[idx][col]
                    df_redacted.at[idx, col] = redact_value(
                        original_value, pii_found, mode=mode
                    )

    return df_redacted, detail, summary


def generate_report(summary: Dict, total_rows: int) -> str:
    """
    Generates a concise compliance and audit text report.

    Args:
        summary: Dictionary of {pii_type: count}.
        total_rows: Total rows processed.

    Returns:
        Formatted summary report string.
    """
    lines = [
        "=" * 55,
        "PERSONAL IDENTIFIABLE INFORMATION (PII) AUDIT REPORT",
        "=" * 55,
        f"Total Records Processed   : {total_rows}",
        "",
        "Detected PII Distribution:",
        "-" * 35,
    ]

    total_pii = 0
    pii_labels = {
        "NIK": "National ID (NIK)",
        "NO_HP": "Mobile Phone Number",
        "EMAIL": "Email Address",
        "NPWP": "Tax ID (NPWP)",
        "NAMA": "Full Name",
    }

    for pii_type, count in sorted(summary.items()):
        label = pii_labels.get(pii_type, pii_type)
        lines.append(f"  {label:<26}: {count}")
        total_pii += count

    lines.extend([
        "-" * 35,
        f"  TOTAL PII ENTITIES        : {total_pii}",
        "=" * 55,
    ])

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# PDF Redaction Pipeline (Native Text + Image-Based Pages)
# ══════════════════════════════════════════════════════════

def redact_pdf_native_page(
    page,  # fitz.Page
    pii_matches: list,
    mode: str = "mask",
) -> None:
    """
    Redacts PII from a native-text PDF page using PyMuPDF redaction annotations.

    For partial masking: replaces text in-place with masked equivalent.
    For full redaction: applies solid black boxes over PII text regions.

    Args:
        page: PyMuPDF Page object (modified in place).
        pii_matches: List of PIIMatch from detect_pii_in_native_pdf_page().
        mode: "mask" or "full".
    """
    import fitz

    for match in pii_matches:
        # Find all text instances of this match on the page
        text_instances = page.search_for(match.matched_text)
        for rect in text_instances:
            if mode == "full":
                # Black redaction box
                page.add_redact_annot(rect, fill=(0, 0, 0))
            else:
                # Mask: show masked text in redaction box
                fn = MASK_FUNCTIONS.get(match.pii_type, lambda x: "****")
                masked = fn(match.matched_text)
                page.add_redact_annot(
                    rect,
                    text=masked,
                    fontsize=8,
                    fill=(1, 1, 1),  # white background
                    text_color=(0.1, 0.1, 0.1),
                )

    page.apply_redactions()


def redact_pdf_image_page(
    page,          # fitz.Page
    pii_matches: list,
    image_dpi: int = 300,
) -> None:
    """
    Redacts PII from an image-based PDF page by drawing solid black rectangles
    over the pixel coordinates of each detected PII entity.

    Coordinate conversion: OCR returns pixel coords at image_dpi; these must be
    scaled to PDF point coordinates (72 pt/inch).

    Args:
        page: PyMuPDF Page object (modified in place).
        pii_matches: List of PIIMatch with box_left/top/width/height.
        image_dpi: The DPI used when rendering the page for OCR.
    """
    import fitz

    scale = 72.0 / image_dpi  # convert pixels → PDF points

    for match in pii_matches:
        if match.box_left is None:
            continue  # no position data available — skip

        x0 = match.box_left * scale
        y0 = match.box_top * scale
        x1 = (match.box_left + match.box_width) * scale
        y1 = (match.box_top + match.box_height) * scale

        # Add a small padding around the box for robustness
        padding = 2
        rect = fitz.Rect(x0 - padding, y0 - padding, x1 + padding, y1 + padding)
        page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0))


def redact_pdf(
    pdf_bytes: bytes,
    mode: str = "mask",
    use_ner: bool = True,
    ocr_dpi: int = 300,
) -> tuple:
    """
    Full end-to-end PDF redaction pipeline.

    Processes each page:
    1. Classifies as native-text or image-based (via page_classifier)
    2. Extracts text (native) or runs OCR (image-based, via ocr_engine)
    3. Detects PII on extracted/OCR text (via detector)
    4. Applies appropriate redaction per page type
    5. Returns redacted PDF bytes + per-page metadata + summary

    Args:
        pdf_bytes: Raw bytes of the input PDF.
        mode: "mask" for partial masking, "full" for complete redaction.
        use_ner: Whether to apply spaCy NER for person names.
        ocr_dpi: DPI used for rendering image-based pages before OCR.

    Returns:
        Tuple of:
        - redacted_pdf_bytes: Bytes of the output PDF.
        - page_metadata: List of dicts with per-page results.
        - summary: Dict[pii_type -> count].
    """
    import fitz
    from page_classifier import classify_pdf_bytes
    from ocr_engine import ocr_pdf_page
    from detector import (
        detect_pii_in_native_pdf_page,
        detect_pii_in_ocr_result,
    )

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_classifications = classify_pdf_bytes(pdf_bytes)

    page_metadata = []
    summary: dict = {}

    for page_info in page_classifications:
        page = doc[page_info.page_number]
        page_meta = {
            "page_number": page_info.page_number + 1,  # 1-indexed for display
            "classification": page_info.classification,
            "pii_found": [],
        }

        if page_info.classification == "native-text":
            pii_matches = detect_pii_in_native_pdf_page(
                page_info.native_text, use_ner=use_ner
            )
            redact_pdf_native_page(page, pii_matches, mode=mode)
        else:
            # Image-based: run OCR then pixel-level redaction
            ocr_result = ocr_pdf_page(page, page_info.page_number, dpi=ocr_dpi)
            pii_matches = detect_pii_in_ocr_result(ocr_result, use_ner=use_ner)
            redact_pdf_image_page(page, pii_matches, image_dpi=ocr_dpi)

        # Collect metadata and summary counts
        for match in pii_matches:
            page_meta["pii_found"].append({
                "type": match.pii_type,
                "text": match.matched_text,
                "has_position": match.box_left is not None,
            })
            summary[match.pii_type] = summary.get(match.pii_type, 0) + 1

        page_metadata.append(page_meta)

    # Save to bytes
    output_buf = doc.tobytes(garbage=3, deflate=True)
    doc.close()

    return output_buf, page_metadata, summary
