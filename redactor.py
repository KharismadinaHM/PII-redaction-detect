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


def mask_bank_account(account: str) -> str:
    """Mask bank account number: displays first 4 and last 2 digits → 1234****90."""
    account = str(account).strip()
    if len(account) >= 6:
        return account[:4] + "*" * (len(account) - 6) + account[-2:]
    return "*" * len(account)


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
    "NO_REKENING": mask_bank_account,
}


def redact_value(value: str, pii_detected: Dict, mode: str = "mask",
                 policy: Dict = None, tokenizer=None) -> str:
    """
    Redacts a single cell value based on detected PII entities.

    Args:
        value: Original cell value.
        pii_detected: Dictionary of detected PII {pii_type: [matches]}.
        mode: "mask" for partial masking, "full" for complete token replacement,
              "tokenize" for consistent pseudo-anonymization.
        policy: Optional per-field mode overrides {pii_type: mode_str}.
        tokenizer: Optional PIITokenizer instance (required for tokenize mode).

    Returns:
        Redacted cell string.
    """
    if not pii_detected:
        return value

    result = str(value)

    for pii_type, matches in pii_detected.items():
        # Determine effective mode: policy override > global mode
        effective_mode = mode
        if policy and pii_type in policy:
            effective_mode = policy[pii_type]

        # Skip if policy says visible
        if effective_mode == "visible":
            continue

        if effective_mode == "full":
            return redact_full(result, pii_type)
        elif effective_mode == "tokenize" and tokenizer is not None:
            for match in matches:
                token = tokenizer.tokenize(match, pii_type)
                result = result.replace(match, token)
            # For NAMA that covers the whole cell
            if pii_type == "NAMA" and result == str(value):
                result = tokenizer.tokenize(result, pii_type)
        else:
            # Default: mask
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
    policy: Dict = None,
    tokenizer=None,
) -> tuple:
    """
    Redacts an entire pandas DataFrame.

    Args:
        df: Original pandas DataFrame.
        mode: "mask" (partial), "full" (complete replacement), or "tokenize".
        use_ner: Whether to apply spaCy NER for person name recognition.
        policy: Optional per-field mode overrides {pii_type: mode_str}.
        tokenizer: Optional PIITokenizer instance for tokenize mode.

    Returns:
        Tuple containing:
        - df_redacted: Redacted pandas DataFrame.
        - detail: Per-cell PII detection details.
        - summary: Aggregate PII counts per type.
    """
    detail, summary = analyze_dataframe(df, use_ner=use_ner)

    # Auto-create tokenizer if tokenize mode but none provided
    if mode == "tokenize" and tokenizer is None:
        from tokenizer import PIITokenizer
        tokenizer = PIITokenizer()

    df_redacted = df.copy()

    for idx in df_redacted.index:
        if idx in detail:
            for col in df_redacted.columns:
                if col in detail[idx]:
                    original_value = str(df_redacted.at[idx, col])
                    pii_found = detail[idx][col]
                    df_redacted.at[idx, col] = redact_value(
                        original_value, pii_found, mode=mode,
                        policy=policy, tokenizer=tokenizer,
                    )

    return df_redacted, detail, summary


# ──────────────────────────────────────────────
# Human-in-the-Loop (HITL) Review Functions
# ──────────────────────────────────────────────

def scan_dataframe_for_review(df: pd.DataFrame, use_ner: bool = True) -> tuple:
    """
    Scans a DataFrame and returns a list of candidate PII items suitable
    for interactive review in an editable data grid.

    Args:
        df: pandas DataFrame to inspect.
        use_ner: Whether to apply NER / gazetteer.

    Returns:
        Tuple of:
        - review_records: List of dicts with keys [approved, row, column, pii_type, matched_text, cell_preview, _row_idx]
        - detail: Full detail dict from analyze_dataframe
        - summary: Summary count dict
    """
    detail, summary = analyze_dataframe(df, use_ner=use_ner)
    review_records = []

    for idx in df.index:
        if idx in detail:
            for col, pii_dict in detail[idx].items():
                orig_val = str(df.at[idx, col])
                for ptype, matches in pii_dict.items():
                    for match in matches:
                        review_records.append({
                            "approved": True,
                            "row": int(idx) + 1,
                            "column": str(col),
                            "pii_type": str(ptype),
                            "matched_text": str(match),
                            "cell_preview": orig_val[:40] + ("..." if len(orig_val) > 40 else ""),
                            "_row_idx": int(idx),
                        })

    return review_records, detail, summary


def redact_dataframe_with_review(
    df: pd.DataFrame,
    review_records: list,
    mode: str = "mask",
    policy: Dict = None,
    tokenizer=None,
) -> tuple:
    """
    Redacts a DataFrame applying only user-approved PII records.

    Args:
        df: Original pandas DataFrame.
        review_records: List of dicts from review table (with 'approved' boolean).
        mode: Redaction mode ("mask", "full", "tokenize").
        policy: Optional role-based policy overrides.
        tokenizer: Optional PIITokenizer instance.

    Returns:
        Tuple of (df_redacted, filtered_detail, summary).
    """
    filtered_detail: Dict = {}
    summary: Dict[str, int] = {}

    for item in review_records:
        if not item.get("approved", True):
            continue

        idx = item.get("_row_idx", item.get("row", 1) - 1)
        col = item["column"]
        ptype = item["pii_type"]
        match = item["matched_text"]

        if idx not in filtered_detail:
            filtered_detail[idx] = {}
        if col not in filtered_detail[idx]:
            filtered_detail[idx][col] = {}
        if ptype not in filtered_detail[idx][col]:
            filtered_detail[idx][col][ptype] = []

        filtered_detail[idx][col][ptype].append(match)
        summary[ptype] = summary.get(ptype, 0) + 1

    if mode == "tokenize" and tokenizer is None:
        from tokenizer import PIITokenizer
        tokenizer = PIITokenizer()

    df_redacted = df.copy()
    for idx in df_redacted.index:
        if idx in filtered_detail:
            for col in df_redacted.columns:
                if col in filtered_detail[idx]:
                    original_value = str(df_redacted.at[idx, col])
                    pii_found = filtered_detail[idx][col]
                    df_redacted.at[idx, col] = redact_value(
                        original_value, pii_found, mode=mode,
                        policy=policy, tokenizer=tokenizer,
                    )

    return df_redacted, filtered_detail, summary


def scan_pdf_for_review(
    pdf_bytes: bytes,
    use_ner: bool = True,
    ocr_dpi: int = 300,
) -> tuple:
    """
    Scans a PDF document and extracts all candidate PII matches across all pages
    without modifying the document, preparing candidates for manual review.

    Returns:
        Tuple of:
        - review_records: List of candidate match dicts for the UI.
        - page_classifications: List of PageInfo objects.
    """
    import fitz
    from page_classifier import classify_pdf_bytes
    from ocr_engine import ocr_pdf_page, ocr_pdf_page_regions
    from detector import (
        detect_pii_in_native_pdf_page,
        detect_pii_in_ocr_result,
    )

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_classifications = classify_pdf_bytes(pdf_bytes)
    review_records = []

    for page_info in page_classifications:
        page = doc[page_info.page_number]
        pg_num = page_info.page_number + 1

        if page_info.classification == "native-text":
            matches = detect_pii_in_native_pdf_page(page_info.native_text, use_ner=use_ner)
            for m in matches:
                review_records.append({
                    "approved": True,
                    "page": pg_num,
                    "source": "Native Text",
                    "pii_type": m.pii_type,
                    "matched_text": m.matched_text,
                    "_page_idx": page_info.page_number,
                    "_is_ocr": False,
                    "_box": None,
                })

            if page_info.has_images and page_info.image_rects:
                ocr_results = ocr_pdf_page_regions(
                    page, page_info.image_rects, page_info.page_number, dpi=ocr_dpi
                )
                for ocr_res in ocr_results:
                    img_matches = detect_pii_in_ocr_result(ocr_res, use_ner=use_ner)
                    for m in img_matches:
                        review_records.append({
                            "approved": True,
                            "page": pg_num,
                            "source": "Embedded Image (OCR)",
                            "pii_type": m.pii_type,
                            "matched_text": m.matched_text,
                            "_page_idx": page_info.page_number,
                            "_is_ocr": True,
                            "_box": (m.box_left, m.box_top, m.box_width, m.box_height) if m.box_left is not None else None,
                        })
        else:
            ocr_result = ocr_pdf_page(page, page_info.page_number, dpi=ocr_dpi)
            ocr_matches = detect_pii_in_ocr_result(ocr_result, use_ner=use_ner)
            for m in ocr_matches:
                review_records.append({
                    "approved": True,
                    "page": pg_num,
                    "source": "Scanned Page (OCR)",
                    "pii_type": m.pii_type,
                    "matched_text": m.matched_text,
                    "_page_idx": page_info.page_number,
                    "_is_ocr": True,
                    "_box": (m.box_left, m.box_top, m.box_width, m.box_height) if m.box_left is not None else None,
                })

    doc.close()
    return review_records, page_classifications


def redact_pdf_with_review(
    pdf_bytes: bytes,
    review_records: list,
    mode: str = "mask",
    ocr_dpi: int = 300,
) -> tuple:
    """
    Applies redaction to a PDF using only approved items from the review table.

    Returns:
        Tuple of (output_pdf_bytes, page_metadata, summary).
    """
    import fitz
    from detector import PIIMatch

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = len(doc)

    # Group approved records per page index
    per_page_native = {i: [] for i in range(num_pages)}
    per_page_ocr = {i: [] for i in range(num_pages)}
    summary: Dict[str, int] = {}
    page_metadata = []

    for item in review_records:
        if not item.get("approved", True):
            continue

        pg_idx = item.get("_page_idx", item.get("page", 1) - 1)
        if pg_idx >= num_pages:
            continue

        ptype = item["pii_type"]
        text = item["matched_text"]
        summary[ptype] = summary.get(ptype, 0) + 1

        if item.get("_is_ocr", False):
            box = item.get("_box")
            if box:
                bl, bt, bw, bh = box
                per_page_ocr[pg_idx].append(PIIMatch(
                    pii_type=ptype,
                    matched_text=text,
                    box_left=bl,
                    box_top=bt,
                    box_width=bw,
                    box_height=bh,
                ))
            else:
                per_page_native[pg_idx].append(PIIMatch(pii_type=ptype, matched_text=text))
        else:
            per_page_native[pg_idx].append(PIIMatch(pii_type=ptype, matched_text=text))

    for pg_idx in range(num_pages):
        page = doc[pg_idx]
        native_matches = per_page_native[pg_idx]
        ocr_matches = per_page_ocr[pg_idx]

        if native_matches:
            redact_pdf_native_page(page, native_matches, mode=mode)
        if ocr_matches:
            redact_pdf_image_page(page, ocr_matches, image_dpi=ocr_dpi)

        all_matches = native_matches + ocr_matches
        page_metadata.append({
            "page_number": pg_idx + 1,
            "classification": "reviewed",
            "pii_found": [
                {"type": m.pii_type, "text": m.matched_text, "has_position": m.box_left is not None}
                for m in all_matches
            ],
        })

    output_buf = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return output_buf, page_metadata, summary


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
        "NO_REKENING": "Bank Account Number",
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


def generate_pdf_report(
    summary: Dict[str, int],
    total_records_or_pages: int,
    document_name: str = "Document",
    document_type: str = "CSV",
    mode: str = "mask",
) -> bytes:
    """
    Generates a formal 1-page PDF Data Redaction & Compliance Audit Certificate.

    Args:
        summary: Dictionary of {pii_type: count}.
        total_records_or_pages: Number of rows or pages processed.
        document_name: Original file name.
        document_type: "CSV" or "PDF".
        mode: Redaction mode ("mask" or "full").

    Returns:
        Bytes of the generated compliance PDF document.
    """
    import fitz
    from datetime import datetime, timezone

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Header background
    page.draw_rect(fitz.Rect(0, 0, 595, 110), fill=(0.06, 0.09, 0.16))  # #0f172a
    page.draw_rect(fitz.Rect(0, 107, 595, 110), fill=(0.11, 0.31, 0.85)) # blue accent

    # Title
    page.insert_text(
        fitz.Point(50, 50),
        "DATA PRIVACY COMPLIANCE AUDIT CERTIFICATE",
        fontsize=15,
        fontname="helv",
        color=(1, 1, 1),
    )
    page.insert_text(
        fitz.Point(50, 72),
        "Official Personal Data Redaction & Audit Verification Record",
        fontsize=10,
        fontname="helv",
        color=(0.7, 0.75, 0.82),
    )
    page.insert_text(
        fitz.Point(50, 92),
        "Legal Framework: Indonesian Personal Data Protection Act (UU PDP No. 27/2022)",
        fontsize=8,
        fontname="helv",
        color=(0.58, 0.64, 0.72),
    )

    # Document & Audit Metadata
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    mode_label = "Partial Masking (Operational)" if mode == "mask" else "Full Redaction (External Distribution)"

    metadata_items = [
        ("Target Document", document_name),
        ("Document Format", f"{document_type.upper()} ({total_records_or_pages} {'rows' if document_type.upper() == 'CSV' else 'pages'})"),
        ("Redaction Method", mode_label),
        ("Execution Timestamp", now_str),
        ("Audit Log Identifier", f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
    ]

    y = 150
    page.draw_rect(fitz.Rect(50, 130, 545, 235), fill=(0.97, 0.98, 0.99), color=(0.8, 0.84, 0.88))
    for label, val in metadata_items:
        page.insert_text(fitz.Point(65, y), f"{label}:", fontsize=9, fontname="helv", color=(0.3, 0.35, 0.42))
        page.insert_text(fitz.Point(210, y), str(val), fontsize=9, fontname="helv", color=(0.06, 0.09, 0.16))
        y += 18

    # Table Header
    y_table = 265
    page.insert_text(fitz.Point(50, y_table - 8), "SUMMARY OF REDACTED PERSONAL DATA ENTITIES", fontsize=11, fontname="helv", color=(0.06, 0.09, 0.16))
    page.draw_rect(fitz.Rect(50, y_table, 545, y_table + 24), fill=(0.06, 0.09, 0.16))

    page.insert_text(fitz.Point(65, y_table + 16), "PII Classification Category", fontsize=9, fontname="helv", color=(1, 1, 1))
    page.insert_text(fitz.Point(340, y_table + 16), "Detected Count", fontsize=9, fontname="helv", color=(1, 1, 1))
    page.insert_text(fitz.Point(440, y_table + 16), "Status", fontsize=9, fontname="helv", color=(1, 1, 1))

    pii_labels = {
        "NIK": "National ID (NIK - 16 Digits)",
        "NO_HP": "Mobile Phone Number (08xx / +62)",
        "EMAIL": "Email Address",
        "NPWP": "Taxpayer Identification (NPWP)",
        "NAMA": "Full Name (Person Entity)",
        "NO_REKENING": "Bank Account Number",
    }

    y_row = y_table + 24
    total_pii = sum(summary.values()) if summary else 0

    all_types = ["NAMA", "NIK", "NO_HP", "EMAIL", "NPWP", "NO_REKENING"]
    for i, ptype in enumerate(all_types):
        count = summary.get(ptype, 0)
        bg = (0.97, 0.98, 0.99) if i % 2 == 0 else (1, 1, 1)
        page.draw_rect(fitz.Rect(50, y_row, 545, y_row + 22), fill=bg, color=(0.88, 0.91, 0.94))

        label = pii_labels.get(ptype, ptype)
        page.insert_text(fitz.Point(65, y_row + 15), label, fontsize=9, fontname="helv", color=(0.12, 0.16, 0.22))
        page.insert_text(fitz.Point(350, y_row + 15), str(count), fontsize=9, fontname="helv", color=(0.12, 0.16, 0.22))
        page.insert_text(fitz.Point(440, y_row + 15), "REDACTED" if count > 0 else "None Found", fontsize=8, fontname="helv", color=(0.08, 0.48, 0.25) if count > 0 else (0.5, 0.55, 0.6))
        y_row += 22

    # Total Row
    page.draw_rect(fitz.Rect(50, y_row, 545, y_row + 24), fill=(0.94, 0.96, 0.98), color=(0.75, 0.8, 0.85))
    page.insert_text(fitz.Point(65, y_row + 16), "TOTAL PROTECTED ENTITIES", fontsize=9, fontname="helv", color=(0.06, 0.09, 0.16))
    page.insert_text(fitz.Point(350, y_row + 16), str(total_pii), fontsize=10, fontname="helv", color=(0.11, 0.31, 0.85))
    page.insert_text(fitz.Point(440, y_row + 16), "VERIFIED", fontsize=9, fontname="helv", color=(0.08, 0.48, 0.25))

    # Attestation Section
    y_attest = y_row + 55
    page.draw_rect(fitz.Rect(50, y_attest, 545, y_attest + 100), fill=(0.98, 0.99, 1.0), color=(0.8, 0.86, 0.95))
    page.insert_text(fitz.Point(65, y_attest + 22), "COMPLIANCE ATTESTATION STATEMENT", fontsize=10, fontname="helv", color=(0.11, 0.31, 0.85))
    attest_text = (
        "This certifies that all identified personal identifiable information (PII) within the subject document\n"
        "has undergone automated cryptographic masking and/or physical pixel redaction in compliance with\n"
        "applicable data protection statutes. Non-PII fields remain structurally unaltered."
    )
    y_line = y_attest + 42
    for line in attest_text.split("\n"):
        page.insert_text(fitz.Point(65, y_line), line, fontsize=8, fontname="helv", color=(0.25, 0.3, 0.38))
        y_line += 14

    # Footer
    page.draw_line(fitz.Point(50, 790), fitz.Point(545, 790), color=(0.8, 0.84, 0.88), width=1)
    page.insert_text(
        fitz.Point(50, 805),
        "Generated automatically by PII Redaction System v1.2 — Confidential & Privileged Record",
        fontsize=8,
        fontname="helv",
        color=(0.58, 0.64, 0.72),
    )

    pdf_report_bytes = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return pdf_report_bytes


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
            # 1. Process Native Text
            pii_matches = detect_pii_in_native_pdf_page(
                page_info.native_text, use_ner=use_ner
            )
            redact_pdf_native_page(page, pii_matches, mode=mode)

            # 2. Process Embedded Images (Hybrid Case)
            if page_info.has_images and page_info.image_rects:
                from ocr_engine import ocr_pdf_page_regions
                ocr_results = ocr_pdf_page_regions(
                    page, page_info.image_rects, page_info.page_number, dpi=ocr_dpi
                )
                for ocr_res in ocr_results:
                    img_pii_matches = detect_pii_in_ocr_result(ocr_res, use_ner=use_ner)
                    redact_pdf_image_page(page, img_pii_matches, image_dpi=ocr_dpi)
                    pii_matches.extend(img_pii_matches)
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
