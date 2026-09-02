"""
detector.py
PII Detection Engine using Regular Expressions and spaCy Named Entity Recognition (NER).

Supported Entity Types:
- NIK: Indonesian National Identification Number (16 digits)
- NO_HP: Indonesian Mobile Phone Numbers (08xx / +62 / 62)
- EMAIL: Standard Internet Email Addresses
- NPWP: Indonesian Tax Identification Numbers
- NAMA: Person Names (via spaCy NER and column context heuristic)
"""

import re
from typing import Dict, List, Tuple, Optional

# ──────────────────────────────────────────────
# Regular Expression Patterns for Indonesian PII
# ──────────────────────────────────────────────

PATTERNS: Dict[str, re.Pattern] = {
    "NIK": re.compile(r"\b\d{16}\b"),
    "NO_HP": re.compile(r"\b(?:\+62|62|0)8[1-9]\d{6,10}\b"),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w.-]+\.\w{2,}\b", re.IGNORECASE),
    "NPWP": re.compile(r"\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b"),
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

    if use_ner:
        names = detect_name_ner(text)
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
    elif use_ner:
        names = detect_name_ner(text)
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
