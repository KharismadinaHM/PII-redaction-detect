# PII Detection & Redaction Prototype (PRAG)

Automated privacy protection and redaction tool for internal employee documents (CSV/Excel HR records), featuring rule-based regex detection, spaCy Named Entity Recognition (NER), partial masking / full redaction modes, and an enterprise Streamlit web dashboard.

---

## Key Features

- **Multi-Pattern PII Detection**:
  - **National ID (NIK)**: 16-digit Indonesian ID pattern validation (`\b\d{16}\b`)
  - **Mobile Phone Numbers**: Indonesian mobile prefixes 08xx, +62, 62 (`\b(?:\+62|62|0)8[1-9]\d{6,10}\b`)
  - **Email Addresses**: Standard RFC compliant email regex
  - **Tax ID (NPWP)**: Indonesian standard tax format (`\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b`)
  - **Person Names**: Named Entity Recognition (NER) via spaCy (`PERSON` entity) and column heuristics
- **Redaction Modes**:
  - **Partial Masking**: Masks sensitive segments while retaining operational context (e.g., `0812****5678`, `B*** S***`)
  - **Full Redaction**: Complete token replacement for external sharing (e.g., `[REDACTED-NIK]`)
- **Non-PII Integrity**: Ensures operational columns (such as employee salary/compensation) remain untouched.
- **Enterprise Streamlit UI**:
  - Drag-and-drop CSV file upload
  - Side-by-side & single-view data comparison (Before vs After)
  - Real-time aggregate metric cards and Plotly distribution charts
  - Per-row expandable PII detection inspection
  - Redacted CSV file export and text-based audit report generator
  - Built-in synthetic test dataset generator

---

## Project Structure

```
PII-redaction-detect/
├── app.py                      # Streamlit UI dashboard
├── detector.py                 # PII detection engine (Regex + spaCy NER)
├── redactor.py                 # Redaction & masking transformation module
├── generate_dummy_data.py      # Synthetic employee record generator
├── requirements.txt            # Python dependencies
├── PROGRESS.md                 # Development tracker and roadmap
├── .streamlit/
│   └── config.toml             # Streamlit visual theme configuration
├── data/
│   ├── dummy_input.csv         # Synthetic input records
│   └── output_redacted.csv     # Exported redacted dataset
├── tests/
│   ├── test_detector.py        # Detector unit tests
│   └── test_redactor.py        # Redactor unit tests
└── docs/
    ├── Prototype_Build_Guide_Antigravity.md
    ├── Solution_Brief_PII_Redaction_System.md
    └── OCR_Hybrid_Document_Build_Guide.md
```

---

## Quickstart

### 1. Clone & Setup Environment

```bash
git clone <repository-url>
cd PII-redaction-detect
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Download spaCy Language Model

```bash
python3 -m spacy download en_core_web_sm
```

### 3. Generate Test Dataset (Optional)

```bash
python3 generate_dummy_data.py
```

### 4. Run Streamlit Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

### 5. Run Automated Unit Tests

```bash
pytest tests/ -v
```

---

## Automated Test Coverage

The project includes 32 automated unit tests across detection patterns, masking functions, and dataframe integrity:

- National ID pattern matching & boundary rejection
- Mobile number validation and landline exclusion
- Email and Tax ID structure verification
- Salary column preservation during redaction
- All 32 tests passing (`pytest tests/ -v`)

---

## License

Internal Enterprise Compliance & Privacy Prototype.
