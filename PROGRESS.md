# PROGRESS.md — PII Detection & Redaction Prototype

> **This document tracks development progress and roadmap items for the PII Detection & Redaction Prototype.**
> Future sessions and contributors can seamlessly resume development from this checkpoint.

---

## Current Status: Phase 3 — Complete (All Prototype Features Implemented)

Referencing design specifications from:
- [`docs/Prototype_Build_Guide_Antigravity.md`](docs/Prototype_Build_Guide_Antigravity.md)
- [`docs/Solution_Brief_PII_Redaction_System.md`](docs/Solution_Brief_PII_Redaction_System.md)
- [`docs/OCR_Hybrid_Document_Build_Guide.md`](docs/OCR_Hybrid_Document_Build_Guide.md)

---

## Completed Milestones

### 1. Project Architecture & Setup
- [x] `app.py` — Streamlit UI entry point (enterprise high-contrast theme)
- [x] `detector.py` — Multi-pattern PII detection module (Regex + spaCy NER + Indonesian Gazetteer)
- [x] `redactor.py` — Masking, tokenization & redaction transformation engine
- [x] `tokenizer.py` — Deterministic pseudo-anonymization module
- [x] `redaction_policy.py` — Role-based per-field policy configuration
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
- [x] Bank Account Number Regex (`NO_REKENING`) with context heuristics
- [x] spaCy NER (Named Entity Recognition) for person names (`PERSON` entities)
- [x] Column context awareness (automatic name column identification; financial compensation/salary column preserved)
- [x] Lazy-loading for language models (`en_core_web_sm` with fallback to `xx_ent_wiki_sm`)

### 3. Redaction & Transformation Engine (`redactor.py`, `tokenizer.py`, `redaction_policy.py`)
- [x] Partial Masking Mode: NIK -> `3201********0001`, Phone -> `0812****7890`, Email -> `bu**@gmail.com`, Name -> `B*** S***`, NPWP -> `12.***.***.* -***. ***`, Bank -> `1234****90`
- [x] Full Redaction Mode: Replaces entities with typed placeholders (`[REDACTED-NIK]`, `[REDACTED-NAMA]`, etc.)
- [x] Pseudo-anonymization / Tokenization: Deterministic mapping (`[EMP_001]`, `[NIK_001]`) with JSON export/import
- [x] Role-Based Policies: Preset profiles (HR Manager, Finance, Auditor, IT Admin) and custom per-field toggles
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
- [x] Redacted CSV download capability (preserving original name + `_redacted.csv`)
- [x] Sidebar configuration: toggle partial masking vs full redaction vs pseudo-anonymization
- [x] Sidebar configuration: toggle spaCy NER
- [x] Sidebar configuration: role-based policy selector with custom per-field toggles
- [x] In-app synthetic dataset generator (CSV + PDF)
- [x] High-volume record advisory banner
- [x] Expandable per-row PII detection breakdown
- [x] Enterprise-grade styling: dark slate typography on crisp white cards, WCAG-compliant contrast, no emojis/emoticons

### 6. Hybrid PDF Processing & OCR Pipeline (`page_classifier.py`, `ocr_engine.py`)
- [x] **Page Classifier (`page_classifier.py`)**: Automatic distinction between native-text and image-based/scanned pages via PyMuPDF.
- [x] **OCR Engine (`ocr_engine.py`)**: Tesseract OCR wrapper extracting text and per-word bounding box coordinates.
- [x] **OCR-Aware Detection (`detector.py`)**: Bounding box coordinate mapping for detected PII entities.
- [x] **Hybrid PDF Redactor (`redactor.py`)**: Native redaction annotations for text pages + solid black bounding box overlay for scanned pages.
- [x] **Embedded Image Processing (Hybrid Pages)**: Added capability to selectively extract, OCR, and redact images embedded within native text pages without double-processing native text.
- [x] **Streamlit Multi-Format UI (`app.py`)**: Parallel CSV and PDF workflows, per-page classification badges, visual before/after page rendering, and redacted PDF export.
- [x] **Hybrid Test PDF Generator (`generate_dummy_pdf.py`)**: Generates 3-page mixed PDF (2 native text pages + 1 rasterized scan image, including a page with an embedded scan).

### 7. Compliance Audit Suite & Reporting (`audit_logger.py`, `redactor.py`)
- [x] **Structured Audit Logging (`audit_logger.py`)**: Automatic event logging in JSON Lines (`data/audit_trail.log`) with SHA-256 document hashing, timestamping, and entity metrics conforming to UU PDP.
- [x] **PDF Compliance Audit Certificate (`redactor.py`)**: One-click downloadable official PDF compliance certificate with attestation statement and category breakdown.
- [x] **Live Audit Log Viewer in UI (`app.py`)**: Interactive real-time audit ledger panel displayed on the Streamlit interface.

### 8. Indonesian Name Gazetteer — Fine-Tuned NER (`detector.py`)
- [x] **Indonesian First Name Dictionary**: ~200 common Indonesian male and female first names.
- [x] **Indonesian Surname Dictionary**: ~100 common Indonesian and Batak/Javanese/Sundanese family names.
- [x] **Gazetteer Detection (`detect_name_gazetteer`)**: Token-level scanning for known first name + surname pairs (up to 3 tokens).
- [x] **Hybrid Detection (`detect_name_hybrid`)**: Combined spaCy NER + gazetteer results with automatic deduplication.
- [x] **Integration**: Wired into `detect_all_pii` and `detect_pii_in_value` — gazetteer always active, spaCy NER optional.

### 9. Containerized Deployment (`Dockerfile`, `docker-compose.yml`)
- [x] **Dockerfile**: Python 3.9-slim base with Tesseract OCR, spaCy model pre-downloaded, Streamlit entrypoint, healthcheck.
- [x] **docker-compose.yml**: Single-service definition with `data/` volume mount and environment variables.
- [x] **.dockerignore**: Excludes development artifacts from build context.

### 10. Automated Unit & Integration Testing (111 tests passing)
- [x] **Detector Unit Tests** (`test_detector.py` — 23 tests): Regex patterns, name detection, column context, bank account heuristics.
- [x] **Redactor Unit Tests** (`test_redactor.py` — 15 tests): Masking functions, dataframe redaction, salary preservation.
- [x] **Validation Suite** (`test_validation.py` — 37 tests): Exact boundary checks, prefix edge cases, non-PII column integrity.
- [x] **Audit & Reporting Tests** (`test_audit_and_reporting.py` — 4 tests): Hash verification, JSONL persistence, certificate generation.
- [x] **New Feature Tests** (`test_new_features.py` — 32 tests): Indonesian gazetteer, tokenizer consistency, role-based policy overrides.

---

## Product Roadmap & Backlog

### Phase 2 Next Steps
- [x] Fine-tune custom NER models for Indonesian person names
- [x] Add Bank Account Number pattern detection (with contextual disambiguation against NIK)
- [x] PDF export for compliance audit reports
- [x] Structured file logging with audit trail metadata

### Phase 3 — Human-in-the-Loop MVP
- [x] Interactive manual review & spot-check dashboard
- [x] Optical Character Recognition (OCR) for scanned ID cards and physical employment contracts
- [x] Consistent pseudo-anonymization / Tokenization (`[EMP_001]` consistent mapping across documents)
- [x] Role-based redaction policies (granular field visibility based on role)
- [x] Extended document parser support (CSV + Hybrid PDF)

### Phase 4 — Enterprise Production
- [ ] Single Sign-On (SSO) & Role-Based Access Control (RBAC) — *Deferred: requires external identity provider*
- [x] Permanent database/file audit logging & compliance tracking
- [ ] Automated HRIS system API integrations (Workday / SAP SuccessFactors) — *Deferred: requires sandbox credentials*
- [x] Containerized deployment with Docker and Kubernetes

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

# 5. Run automated test suite (111 tests)
pytest tests/ -v

# 6. Docker deployment (alternative)
docker-compose up --build
```

---

## Project Structure

```
PII-redaction-detect/
├── app.py                      # Streamlit UI dashboard (CSV + PDF + Audit viewer + Policy selector)
├── detector.py                 # Multi-rule PII detection (Regex + NER + Indonesian Gazetteer)
├── redactor.py                 # Redaction, masking, tokenization & PDF compliance certificate
├── tokenizer.py                # Consistent pseudo-anonymization (PIITokenizer)
├── redaction_policy.py         # Role-based per-field redaction policies
├── audit_logger.py             # Structured JSON Lines compliance audit logger
├── page_classifier.py          # PDF page classification (native-text vs image-based)
├── ocr_engine.py               # Tesseract OCR engine with bounding box extraction
├── generate_dummy_data.py      # Synthetic employee CSV dataset generator
├── generate_dummy_pdf.py       # Synthetic hybrid PDF generator
├── requirements.txt            # Dependency specifications
├── Dockerfile                  # Container image build definition
├── docker-compose.yml          # Docker Compose service configuration
├── .dockerignore               # Build context exclusions
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
│   ├── test_audit_and_reporting.py # Audit logger & PDF report tests (4 tests)
│   └── test_new_features.py    # Gazetteer, tokenizer & policy tests (32 tests)
└── docs/
    ├── Prototype_Build_Guide_Antigravity.md
    ├── Solution_Brief_PII_Redaction_System.md
    └── OCR_Hybrid_Document_Build_Guide.md
```

---

*Last updated: September 2, 2026*
