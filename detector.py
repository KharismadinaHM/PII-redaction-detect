"""
detector.py
PII Detection Engine using Regular Expressions and spaCy Named Entity Recognition (NER).

Supported Entity Types:
- NIK: Indonesian National Identification Number (16 digits)
- NO_HP: Indonesian Mobile Phone Numbers (08xx / +62 / 62)
- EMAIL: Standard Internet Email Addresses
- NPWP: Indonesian Tax Identification Numbers
- NAMA: Person Names (via spaCy NER and column context heuristic)

Supports two input sources:
- Native text (from CSV or native-text PDF pages)
- OCR text (from image-based PDF pages, with bounding box position data)
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any

# ──────────────────────────────────────────────
# Regular Expression Patterns for Indonesian PII
# ──────────────────────────────────────────────

PATTERNS: Dict[str, re.Pattern] = {
    "NIK": re.compile(r"\b\d{16}\b"),
    "NO_HP": re.compile(r"\b(?:\+62|62|0)8[1-9]\d{6,10}\b"),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w.-]+\.\w{2,}\b", re.IGNORECASE),
    "NPWP": re.compile(r"\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b"),
    "NO_REKENING": re.compile(r"(?i)\b(?:(?:no\.?\s*)?rek(?:ening)?|bank\s*(?:bca|mandiri|bni|bri|cimb|btn|danamon|permata)?|acc(?:ount)?(?:\s*no)?)\s*[:.-]?\s*(\d{10,16})\b"),
}

# ──────────────────────────────────────────────
# spaCy NER loader (lazy initialization)
# ──────────────────────────────────────────────

_nlp = None


def _get_nlp():
    """Lazy-load spaCy model. Attempts en_core_web_sm, falls back to xx_ent_wiki_sm."""
    global _nlp
    if _nlp is not None:
        return _nlp

    import spacy

    models_to_try = ["en_core_web_sm", "xx_ent_wiki_sm"]
    for model_name in models_to_try:
        try:
            _nlp = spacy.load(model_name)
            return _nlp
        except OSError:
            continue

    return None


def detect_pii_regex(text: str) -> Dict[str, List[str]]:
    """
    Detects structured PII entities in a text string using regular expressions.

    Args:
        text: Input string to inspect.

    Returns:
        Dictionary mapping entity type to list of detected string matches.
    """
    results = {}
    for pii_type, pattern in PATTERNS.items():
        matches = pattern.findall(str(text))
        if matches:
            results[pii_type] = matches
    return results


def detect_name_ner(text: str) -> List[str]:
    """
    Detects person names in a text string using spaCy NER.

    Args:
        text: Input string to inspect.

    Returns:
        List of identified person names.
    """
    nlp = _get_nlp()
    if nlp is None:
        return []

    doc = nlp(str(text))
    names = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            names.append(ent.text)
    return names


# ──────────────────────────────────────────────
# Indonesian Name Gazetteer
# ──────────────────────────────────────────────

INDO_FIRST_NAMES = {
    # Male names
    "adi", "agus", "ahmad", "akhbar", "aldi", "amin", "andi", "andika",
    "andri", "angga", "anwar", "arief", "arif", "aris", "asep", "bagas",
    "bagus", "bambang", "bayu", "bima", "budi", "cahya", "candra", "danu",
    "dedi", "deni", "denny", "dian", "dimas", "doni", "dwi", "edi", "eko",
    "fajar", "faisal", "farid", "farhan", "fauzi", "galih", "galang",
    "gilang", "gunawan", "gustin", "habib", "hadi", "hafiz", "halim",
    "haris", "hasan", "hendri", "hendra", "hendy", "herman", "hero",
    "hidayat", "husein", "ibrahim", "ichsan", "ilham", "imam", "indra",
    "irfan", "irwan", "ivan", "joko", "jaya", "johan", "krisna", "kurnia",
    "lukman", "mahendra", "mulya", "nanda", "nova", "nugroho", "pandu",
    "prasetyo", "putra", "rachman", "rafi", "rahmat", "rama", "ramadan",
    "randi", "rangga", "rendy", "reza", "ridho", "ridwan", "rifki",
    "rizal", "rizki", "rudi", "ryan", "satria", "sigit", "soleh", "sugi",
    "sugeng", "sulastri", "supriyadi", "surya", "syahrul", "taufik",
    "teguh", "tri", "wahyu", "wahid", "wawan", "widodo", "wisnu", "yanto",
    "yoga", "yudi", "yusuf", "zaki", "zainal",
    # Female names
    "adinda", "aini", "aisyah", "ajeng", "amelia", "anisa", "anya",
    "arum", "ayu", "bella", "bunga", "citra", "cut", "dara", "devi",
    "dewi", "diana", "dina", "ella", "endang", "erna", "eva", "fitri",
    "fitriani", "gita", "hana", "ika", "indah", "intan", "ira", "irma",
    "isna", "kartika", "kirana", "laila", "lestari", "lilis", "linda",
    "mawar", "mega", "mira", "mutia", "nadia", "nana", "ningsih", "nina",
    "nisa", "nita", "novianti", "nurul", "paramita", "puspita", "putri",
    "rahma", "rahmawati", "rani", "ratna", "rini", "rina", "rita", "rosa",
    "sari", "septiani", "setiawati", "sinta", "siska", "siti", "sri",
    "suci", "tari", "tika", "tri", "umi", "utami", "vina", "wati",
    "widya", "wulan", "yanti", "yeni", "yuli", "yuliana", "zahra",
}

INDO_LAST_NAMES = {
    "abdullah", "adiputra", "agustina", "aisyah", "amalia", "anggraeni",
    "anwar", "ardiansyah", "arianto", "budianto", "budiman", "cahyani",
    "darmawan", "darma", "dewantara", "firmansyah", "gunawan", "halim",
    "handoko", "harahap", "hardian", "hartono", "hasibuan", "hermawan",
    "hidayat", "hutapea", "hutasoit", "iskandar", "juwita", "kartono",
    "kurniawan", "laksono", "lestari", "mahardika", "mahendra", "manurung",
    "maulana", "megawati", "mulyadi", "nainggolan", "nasution", "nugraha",
    "nugroho", "panjaitan", "permadi", "permana", "prakoso", "prasetyo",
    "pratama", "purnama", "purnomo", "putra", "putri", "rachman",
    "rahayu", "rahmawati", "ramadhan", "riyadi", "santoso", "saputra", "saputri",
    "sari", "setiawan", "simanjuntak", "sinaga", "siregar", "situmorang",
    "subagyo", "subekti", "sudirman", "sugiarto", "sukma", "sulistyo",
    "sumadi", "supriyadi", "surya", "susanto", "sutanto", "syahputra",
    "tampubolon", "tanjung", "utama", "utami", "wardana", "wardani",
    "wibowo", "wibisono", "widodo", "wijaya", "wulandari", "yulianto",
    "yusuf",
}


def detect_name_gazetteer(text: str) -> List[str]:
    """
    Detects Indonesian person names using a gazetteer (dictionary) approach.

    Logic: scans tokens for known Indonesian first names, then checks if
    the adjacent token is a known surname to form a full name match.

    Args:
        text: Input string to inspect.

    Returns:
        List of detected name strings.
    """
    words = str(text).split()
    names = []
    i = 0
    while i < len(words):
        word_clean = re.sub(r"[^a-zA-Z]", "", words[i]).lower()
        if word_clean in INDO_FIRST_NAMES:
            # Try to capture a multi-word name (first + last)
            candidate = [words[i]]
            j = i + 1
            while j < len(words) and j < i + 3:  # max 3 tokens for a name
                next_clean = re.sub(r"[^a-zA-Z]", "", words[j]).lower()
                if next_clean in INDO_LAST_NAMES or next_clean in INDO_FIRST_NAMES:
                    candidate.append(words[j])
                    j += 1
                else:
                    break
            if len(candidate) >= 2:
                names.append(" ".join(candidate))
                i = j
                continue
        i += 1
    return names


def detect_name_hybrid(text: str, use_ner: bool = True) -> List[str]:
    """
    Hybrid name detection combining spaCy NER with Indonesian name gazetteer.

    Merges results from both approaches and deduplicates.

    Args:
        text: Input string to inspect.
        use_ner: Whether to also run spaCy NER.

    Returns:
        Deduplicated list of detected person names.
    """
    names_set = set()

    # Gazetteer-based detection (always active)
    for name in detect_name_gazetteer(text):
        names_set.add(name)

    # spaCy NER detection
    if use_ner:
        for name in detect_name_ner(text):
            names_set.add(name)

    return list(names_set)


def detect_all_pii(text: str, use_ner: bool = True) -> Dict[str, List[str]]:
    """
    Detects all configured PII categories (Regex + NER).

    Args:
        text: Input string to inspect.
        use_ner: Whether to apply NER for person name recognition.

    Returns:
        Dictionary mapping entity type to detected matches.
    """
    results = detect_pii_regex(text)

    names = detect_name_hybrid(text, use_ner=use_ner)
    if names:
        results["NAMA"] = names

    return results


def detect_pii_in_value(value: str, column_name: str = "",
                        use_ner: bool = True) -> Dict[str, List[str]]:
    """
    Detects PII in a specific cell value taking column context into account.

    Columns representing names are automatically categorized as NAMA.
    Columns representing financial compensation (e.g. salary/gaji) are skipped.

    Args:
        value: Cell value string.
        column_name: Header name of the column for contextual disambiguation.
        use_ner: Whether to apply NER.

    Returns:
        Dictionary of detected PII entities.
    """
    text = str(value).strip()
    if not text:
        return {}

    col_lower = column_name.lower().strip()

    # Skip compensation / salary columns (outside PII redaction scope)
    if col_lower in ("gaji", "salary", "compensation", "wage"):
        return {}

    results = detect_pii_regex(text)

    # Name column heuristic: automatically tag as NAMA
    if col_lower in ("nama", "name", "nama_lengkap", "full_name", "employee_name"):
        if text and len(text) > 1:
            results["NAMA"] = [text]
    elif col_lower in ("no_rekening", "nomor_rekening", "rekening", "no_rek", "bank_account", "account_number"):
        # Match digits (10-16 digits) directly in bank column
        digits_match = re.findall(r"\b\d{10,16}\b", text)
        if digits_match:
            results["NO_REKENING"] = digits_match
        elif text:
            results["NO_REKENING"] = [text]
    else:
        names = detect_name_hybrid(text, use_ner=use_ner)
        if names:
            results["NAMA"] = names

    return results


def analyze_dataframe(df, use_ner: bool = True) -> Tuple[dict, dict]:
    """
    Scans an entire pandas DataFrame for PII across all rows and columns.

    Args:
        df: pandas DataFrame to analyze.
        use_ner: Whether to apply spaCy NER.

    Returns:
        Tuple of:
        - detail_per_cell: Dict[row_idx][col_name] = Dict PII findings
        - summary: Dict[pii_type] = aggregate count
    """
    detail_per_cell = {}
    summary = {}

    for idx, row in df.iterrows():
        detail_per_cell[idx] = {}
        for col in df.columns:
            value = str(row[col])
            pii_found = detect_pii_in_value(value, column_name=col, use_ner=use_ner)
            if pii_found:
                detail_per_cell[idx][col] = pii_found
                for pii_type, matches in pii_found.items():
                    summary[pii_type] = summary.get(pii_type, 0) + len(matches)

    return detail_per_cell, summary


# ──────────────────────────────────────────────
# OCR-Aware Detection (PDF Image-Based Pages)
# ──────────────────────────────────────────────

@dataclass
class PIIMatch:
    """A detected PII entity with optional bounding box position (from OCR)."""
    pii_type: str               # e.g. "NIK", "NO_HP", "EMAIL"
    matched_text: str           # The raw matched string
    # Pixel bounding box (set only for OCR-sourced pages)
    box_left: Optional[int] = None
    box_top: Optional[int] = None
    box_width: Optional[int] = None
    box_height: Optional[int] = None
    confidence: float = 100.0   # OCR confidence (100 for native text)


def detect_pii_in_ocr_result(ocr_result: Any, use_ner: bool = True) -> List[PIIMatch]:
    """
    Runs PII detection on an OCRResult object and maps each detected entity
    back to the word bounding boxes returned by Tesseract.

    Args:
        ocr_result: OCRResult dataclass from ocr_engine.py.
        use_ner: Whether to apply spaCy NER for person names.

    Returns:
        List of PIIMatch objects with text and pixel coordinates.
    """
    from ocr_engine import find_word_boxes_for_match

    full_text = ocr_result.full_text
    pii_results: List[PIIMatch] = []

    # Regex detection on full text
    regex_hits = detect_pii_regex(full_text)
    for pii_type, matches in regex_hits.items():
        for match in matches:
            words = find_word_boxes_for_match(match, ocr_result)
            if words:
                # Compute merged bounding box spanning all matched words
                left = min(w.left for w in words)
                top = min(w.top for w in words)
                right = max(w.left + w.width for w in words)
                bottom = max(w.top + w.height for w in words)
                conf = sum(w.confidence for w in words) / len(words)
                pii_results.append(PIIMatch(
                    pii_type=pii_type,
                    matched_text=match,
                    box_left=left,
                    box_top=top,
                    box_width=right - left,
                    box_height=bottom - top,
                    confidence=conf,
                ))
            else:
                # Match found in text but word not located (token boundary issues)
                pii_results.append(PIIMatch(pii_type=pii_type, matched_text=match))

    # NER for person names
    if use_ner:
        names = detect_name_ner(full_text)
        for name in names:
            words = find_word_boxes_for_match(name, ocr_result)
            if words:
                left = min(w.left for w in words)
                top = min(w.top for w in words)
                right = max(w.left + w.width for w in words)
                bottom = max(w.top + w.height for w in words)
                conf = sum(w.confidence for w in words) / len(words)
                pii_results.append(PIIMatch(
                    pii_type="NAMA",
                    matched_text=name,
                    box_left=left,
                    box_top=top,
                    box_width=right - left,
                    box_height=bottom - top,
                    confidence=conf,
                ))
            else:
                pii_results.append(PIIMatch(pii_type="NAMA", matched_text=name))

    return pii_results


def detect_pii_in_native_pdf_page(page_text: str, use_ner: bool = True) -> List[PIIMatch]:
    """
    Runs PII detection on a native-text PDF page. Returns PIIMatch list
    without pixel coordinates (text replacement handles redaction).

    Args:
        page_text: Extracted text string from a native PDF page.
        use_ner: Whether to apply spaCy NER.

    Returns:
        List of PIIMatch objects (box coordinates will be None).
    """
    results: List[PIIMatch] = []
    regex_hits = detect_pii_regex(page_text)
    for pii_type, matches in regex_hits.items():
        for match in matches:
            results.append(PIIMatch(pii_type=pii_type, matched_text=match))

    if use_ner:
        names = detect_name_ner(page_text)
        for name in names:
            results.append(PIIMatch(pii_type="NAMA", matched_text=name))

    return results
