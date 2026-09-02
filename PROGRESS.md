# PROGRESS.md — PII Detection & Redaction Prototype

> **This document tracks development progress and roadmap items for the PII Detection & Redaction Prototype.**
> Future sessions and contributors can seamlessly resume development from this checkpoint.

---

## Current Status: Phase 3 — Hybrid PDF Pipeline (Completed & Verified)

Referencing design specifications from:
- [`docs/Prototype_Build_Guide_Antigravity.md`](docs/Prototype_Build_Guide_Antigravity.md)
- [`docs/Solution_Brief_PII_Redaction_System.md`](docs/Solution_Brief_PII_Redaction_System.md)
- [`docs/OCR_Hybrid_Document_Build_Guide.md`](docs/OCR_Hybrid_Document_Build_Guide.md)

---

## Completed Milestones

### 1. Project Architecture & Setup
- [x] `app.py` — Streamlit UI entry point (enterprise high-contrast theme)
- [x] `detector.py` — Multi-pattern PII detection module (Regex + spaCy NER)
- [x] `redactor.py` — Masking & redaction transformation engine
- [x] `generate_dummy_data.py` — Synthetic employee record generator (Faker `id_ID`)
- [x] `requirements.txt` — Project dependencies
- [x] `.streamlit/config.toml` — High-contrast enterprise theme configuration
- [x] `tests/test_detector.py` — Detector unit test suite
- [x] `tests/test_redactor.py` — Redactor unit test suite
- [x] `data/` — Storage directory for input and output CSV datasets
- [x] `docs/` — Technical specifications and solution briefs
- [x] `PROGRESS.md` — Active development tracker

### 2. PII Detection Engine (`detector.py`)
- [x] National ID (NIK - 16 digits) Regex: `\b\d{16}\b`
- [x] Mobile Phone (08xx, +62, 62) Regex: `\b(?:\+62|62|0)8[1-9]\d{6,10}\b`
- [x] Email Address Regex: `\b[\w.+-]+@[\w.-]+\.\w{2,}\b`
- [x] Tax ID (NPWP) Regex: `\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b`
- [x] spaCy NER (Named Entity Recognition) for person names (`PERSON` entities)
- [x] Column context awareness (automatic name column identification; financial compensation/salary column preserved)
- [x] Lazy-loading for language models (`en_core_web_sm` with fallback to `xx_ent_wiki_sm`)

### 3. Redaction Engine (`redactor.py`)
- [x] Partial Masking Mode: NIK -> `3201********0001`, Phone -> `0812****7890`, Email -> `bu**@gmail.com`, Name -> `B*** S***`, NPWP -> `12.***.***.* -***. ***`
- [x] Full Redaction Mode: Replaces entities with typed placeholders (`[REDACTED-NIK]`, `[REDACTED-NAMA]`, etc.)
- [x] Formatted compliance audit text report generator
- [x] Preservation of non-PII columns (salary values remain intact)

### 4. Synthetic Data Generator (`generate_dummy_data.py`)
- [x] Generates 100 realistic fictitious employee records (customizable 10–500 rows)
- [x] Supported schema: `nama` (name), `nik`, `no_hp` (phone), `email`, `alamat` (address), `gaji` (salary), `npwp`
- [x] Indonesian locale formatting via Faker (`id_ID`)
- [x] Outputs to `data/dummy_input.csv`

### 5. Streamlit User Interface (`app.py`)
- [x] CSV file upload with drag-and-drop support
- [x] "Execute Redaction Process" trigger action
- [x] Side-by-side and toggle table comparisons (Original vs Redacted)
- [x] Aggregate detection statistics via high-contrast metric boxes + Plotly bar chart
- [x] Redacted CSV download capability
- [x] Sidebar configuration: toggle partial masking vs full redaction
- [x] Sidebar configuration: toggle spaCy NER
- [x] In-app synthetic dataset generator
- [x] High-volume record advisory banner
- [x] Expandable per-row PII detection breakdown
- [x] Enterprise-grade styling: dark slate typography on crisp white cards, WCAG-compliant contrast, no emojis/emoticons

### 6. Automated Unit Testing (32 tests in test_detector.py + test_redactor.py)
- [x] Valid 16-digit NIK pattern validation & boundary rejection (15/17 digits)
- [x] Mobile phone format validation (08xx, +62, 62) and landline exclusion
- [x] Email format matching with subaddressing support (`+` tags)
- [x] Tax ID (NPWP) structure validation
- [x] Non-PII column integrity checks (salary preservation)
- [x] Verification of individual masking functions across all entity types

### 7. Targeted Validation Test Suite (37 tests in test_validation.py)
- [x] **NIK Regex — Exact 16-Digit Capture** (11 tests): standalone, embedded in text, all-zeros edge case, all-nines edge case, multiple NIKs in one string, rejection of 12/15/17 digits, alphabetic strings, mixed alphanumeric, empty strings
- [x] **Phone Regex — 08xx and +62 Format Recognition** (16 tests): 0812/0852/0877/0895 prefixes, short 11-digit numbers, text-embedded detection, +62 with multiple operators, 62 (no plus), rejection of Jakarta/Bandung landlines, too-short numbers, plain text, non-Indonesian international numbers
- [x] **Non-PII Column Preservation** (10 tests): salary intact in partial mask mode, salary intact in full redaction mode, salary-only DataFrame pass-through (zero PII detected), NIK/email/phone confirmed changed (proves PII columns are redacted), fully redacted tokens in full mode, row count preserved, column count preserved, non-PII address column unchanged

### 8. Hybrid PDF Processing & OCR Pipeline (`page_classifier.py`, `ocr_engine.py`)
- [x] **Page Classifier (`page_classifier.py`)**: Automatic distinction between native-text and image-based/scanned pages via PyMuPDF.
- [x] **OCR Engine (`ocr_engine.py`)**: Tesseract OCR wrapper extracting text and per-word bounding box coordinates.
- [x] **OCR-Aware Detection (`detector.py`)**: Bounding box coordinate mapping for detected PII entities.
- [x] **Hybrid PDF Redactor (`redactor.py`)**: Native redaction annotations for text pages + solid black bounding box overlay for scanned pages.
- [x] **Streamlit Multi-Format UI (`app.py`)**: Parallel CSV and PDF workflows, per-page classification badges, visual before/after page rendering, and redacted PDF export.
- [x] **Hybrid Test PDF Generator (`generate_dummy_pdf.py`)**: Generates 3-page mixed PDF (2 native text pages + 1 rasterized scan image).

### 9. Bank Account Detection & Compliance Audit Suite (`audit_logger.py`, `redactor.py`)
- [x] **Bank Account Number Detection (`detector.py`)**: Regex with context prefixes (`rekening`, `no. rek`, `bank bca/mandiri/bni/bri`, `account no`) + column-aware rules.
- [x] **Bank Account Masking (`redactor.py`)**: Dedicated masking function (`1234****90`) and full token replacement (`[REDACTED-NO_REKENING]`).
- [x] **Structured Audit Logging (`audit_logger.py`)**: Automatic event logging in JSON Lines (`data/audit_trail.log`) with SHA-256 document hashing, timestamping, and entity metrics conforming to UU PDP.
- [x] **PDF Compliance Audit Certificate (`redactor.py`)**: One-click downloadable official PDF compliance certificate with attestation statement and category breakdown.
- [x] **Live Audit Log Viewer in UI (`app.py`)**: Interactive real-time audit ledger panel displayed on the Streamlit interface.

---

## Product Roadmap & Backlog

### Phase 2 Next Steps
- [ ] Fine-tune custom NER models for Indonesian person names
- [x] Add Bank Account Number pattern detection (with contextual disambiguation against NIK)
- [x] PDF export for compliance audit reports
- [x] Structured file logging with audit trail metadata

### Phase 3 — Human-in-the-Loop MVP
- [ ] Interactive manual review & spot-check dashboard
- [x] Optical Character Recognition (OCR) for scanned ID cards and physical employment contracts
- [ ] Consistent pseudo-anonymization / Tokenization (`[EMP_001]` consistent mapping across documents)
- [ ] Role-based redaction policies (granular field visibility based on role)
- [x] Extended document parser support (CSV + Hybrid PDF)

### Phase 4 — Enterprise Production
- [ ] Single Sign-On (SSO) & Role-Based Access Control (RBAC)
- [x] Permanent database/file audit logging & compliance tracking
- [ ] Automated HRIS system API integrations (Workday / SAP SuccessFactors)
- [ ] Containerized deployment with Docker and Kubernetes

---

## Quickstart Instructions

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download spaCy language model
python -m spacy download en_core_web_sm

# 3. Generate synthetic sample dataset (optional)
python generate_dummy_data.py
python generate_dummy_pdf.py

# 4. Launch Streamlit Web UI
streamlit run app.py

# 5. Run automated test suite (79 tests)
pytest tests/ -v
```

---

## Project Structure

```
PII-redaction-detect/
├── app.py                      # Streamlit UI dashboard (CSV + PDF + Audit viewer)
├── detector.py                 # Multi-rule PII detection module (Regex + NER + Bank accounts)
├── redactor.py                 # Redaction, masking & PDF compliance certificate generator
├── audit_logger.py             # Structured JSON Lines compliance audit logger
├── page_classifier.py          # PDF page classification (native-text vs image-based)
├── ocr_engine.py               # Tesseract OCR engine with bounding box extraction
├── generate_dummy_data.py      # Synthetic employee CSV dataset generator
├── generate_dummy_pdf.py       # Synthetic hybrid PDF generator
├── requirements.txt            # Dependency specifications
├── PROGRESS.md                 # Project progress and roadmap tracker
├── .streamlit/
│   └── config.toml             # Streamlit visual theme configuration
├── data/
│   ├── dummy_input.csv         # Synthetic input CSV records
│   ├── dummy_hybrid.pdf        # Synthetic hybrid PDF document
│   ├── output_redacted.csv     # Redacted CSV export
│   ├── output_redacted.pdf     # Redacted PDF export
│   └── audit_trail.log         # Structured compliance audit ledger
├── tests/
│   ├── test_detector.py        # Detector unit tests (23 tests)
│   ├── test_redactor.py        # Redactor unit tests (15 tests)
│   ├── test_validation.py      # Targeted validation suite (37 tests)
│   └── test_audit_and_reporting.py # Audit logger & PDF report tests (4 tests)
└── docs/
    ├── Prototype_Build_Guide_Antigravity.md
    ├── Solution_Brief_PII_Redaction_System.md
    └── OCR_Hybrid_Document_Build_Guide.md
```

---

*Last updated: September 2, 2026*

