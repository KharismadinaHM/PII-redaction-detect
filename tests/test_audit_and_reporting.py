"""
tests/test_audit_and_reporting.py
Unit tests for audit logging and PDF compliance certificate generation.
"""

import sys
import os
import pytest
import json
import fitz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit_logger import log_redaction_event, read_audit_log, compute_sha256
from redactor import generate_pdf_report


class TestAuditLogger:
    """Tests for structured audit trail logging."""

    def test_compute_sha256(self):
        sample = b"test content for hashing"
        hash_val = compute_sha256(sample)
        assert len(hash_val) == 64
        assert hash_val == compute_sha256(sample)

    def test_log_redaction_event_csv(self):
        summary = {"NIK": 5, "EMAIL": 3, "NO_REKENING": 2}
        event = log_redaction_event(
            document_name="test_employees.csv",
            document_type="csv",
            total_records_or_pages=10,
            redaction_mode="mask",
            summary=summary,
            file_bytes=b"dummy csv content",
        )
        assert event["document_name"] == "test_employees.csv"
        assert event["document_type"] == "CSV"
        assert event["total_pii_entities_redacted"] == 10
        assert "event_id" in event
        assert "timestamp" in event

    def test_read_audit_log(self):
        entries = read_audit_log(max_entries=5)
        assert isinstance(entries, list)
        if entries:
            assert "event_id" in entries[0]
            assert "timestamp" in entries[0]


class TestPDFReportGenerator:
    """Tests for PDF compliance certificate generation."""

    def test_generate_pdf_report_valid_pdf(self):
        summary = {"NAMA": 2, "NIK": 2, "NO_HP": 2, "EMAIL": 2, "NPWP": 2, "NO_REKENING": 1}
        pdf_bytes = generate_pdf_report(
            summary=summary,
            total_records_or_pages=2,
            document_name="contract_sample.pdf",
            document_type="PDF",
            mode="mask",
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 500

        # Validate that PyMuPDF can open and read the generated PDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        assert len(doc) == 1
        page_text = doc[0].get_text()
        assert "DATA PRIVACY COMPLIANCE AUDIT CERTIFICATE" in page_text
        assert "contract_sample.pdf" in page_text
        assert "UU PDP" in page_text
        doc.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
