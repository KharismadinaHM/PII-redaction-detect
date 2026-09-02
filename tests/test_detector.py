"""
tests/test_detector.py
Unit tests for detector.py module.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detector import detect_pii_regex, detect_pii_in_value, PATTERNS


class TestNIKDetection:
    """Tests for Indonesian 16-digit National ID (NIK) detection."""

    def test_nik_valid_16_digit(self):
        result = detect_pii_regex("3201150708900001")
        assert "NIK" in result
        assert "3201150708900001" in result["NIK"]

    def test_nik_in_sentence(self):
        result = detect_pii_regex("Employee NIK reference 3201150708900001 recorded.")
        assert "NIK" in result

    def test_nik_15_digit_not_match(self):
        result = detect_pii_regex("320115070890000")  # 15 digits
        assert "NIK" not in result

    def test_nik_17_digit_not_match(self):
        result = detect_pii_regex("32011507089000011")  # 17 digits
        assert "NIK" not in result


class TestPhoneDetection:
    """Tests for Indonesian mobile phone number detection."""

    def test_phone_08xx(self):
        result = detect_pii_regex("081234567890")
        assert "NO_HP" in result

    def test_phone_plus62(self):
        result = detect_pii_regex("+6281234567890")
        assert "NO_HP" in result

    def test_phone_62(self):
        result = detect_pii_regex("6281234567890")
        assert "NO_HP" in result

    def test_phone_various_prefixes(self):
        phones = ["08521234567", "08771234567", "08951234567"]
        for phone in phones:
            result = detect_pii_regex(phone)
            assert "NO_HP" in result, f"Detection failed for: {phone}"

    def test_non_phone_not_match(self):
        result = detect_pii_regex("0211234567")  # landline, non-mobile
        assert "NO_HP" not in result


class TestEmailDetection:
    """Tests for email pattern detection."""

    def test_email_basic(self):
        result = detect_pii_regex("budi.santoso@gmail.com")
        assert "EMAIL" in result

    def test_email_with_plus(self):
        result = detect_pii_regex("user+tag@domain.co.id")
        assert "EMAIL" in result

    def test_email_in_text(self):
        result = detect_pii_regex("Please reach out at budi@company.com soon")
        assert "EMAIL" in result

    def test_non_email_not_match(self):
        result = detect_pii_regex("this is not an email address")
        assert "EMAIL" not in result


class TestNPWPDetection:
    """Tests for Indonesian Tax Identification Number (NPWP) detection."""

    def test_npwp_valid_format(self):
        result = detect_pii_regex("12.345.678.9-012.345")
        assert "NPWP" in result

    def test_npwp_in_text(self):
        result = detect_pii_regex("Tax record NPWP: 12.345.678.9-012.345 verified")
        assert "NPWP" in result


class TestColumnAwareness:
    """Tests column-aware disambiguation rules."""

    def test_kolom_nama_detected_as_nama(self):
        result = detect_pii_in_value("Budi Santoso", column_name="nama", use_ner=False)
        assert "NAMA" in result

    def test_kolom_gaji_skipped(self):
        result = detect_pii_in_value("Rp 15.000.000", column_name="gaji", use_ner=False)
        assert len(result) == 0, "Salary column should be preserved without redaction"

    def test_kolom_salary_skipped(self):
        result = detect_pii_in_value("15000000", column_name="salary", use_ner=False)
        assert len(result) == 0

    def test_empty_value_returns_empty(self):
        result = detect_pii_in_value("", column_name="nama", use_ner=False)
        assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
