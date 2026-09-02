"""
tests/test_validation.py
Targeted validation tests per the Prototype Build Guide checklist:

1. NIK regex correctly captures exactly 16-digit numbers (not 15, not 17, not mixed)
2. Phone regex correctly captures 08xx and +62 formats (and rejects non-mobile patterns)
3. Redaction preserves non-PII columns (e.g. salary is never modified)
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detector import detect_pii_regex, detect_pii_in_value, PATTERNS
from redactor import redact_dataframe


# ═════════════════════════════════════════════════════
# SECTION 1: NIK Regex — Exact 16-Digit Capture
# ═════════════════════════════════════════════════════

class TestNIKRegexValidation:
    """
    Validates that the NIK regex captures exactly 16 consecutive digits
    and rejects anything shorter, longer, or non-numeric.
    """

    # ── Positive: must detect ──

    def test_exactly_16_digits_standalone(self):
        """A standalone 16-digit string must be detected as NIK."""
        result = detect_pii_regex("3201150708900001")
        assert "NIK" in result
        assert result["NIK"] == ["3201150708900001"]

    def test_16_digits_embedded_in_text(self):
        """NIK inside running text must still be captured."""
        result = detect_pii_regex("NIK karyawan: 1234567890123456 tercatat")
        assert "NIK" in result
        assert "1234567890123456" in result["NIK"]

    def test_16_digits_all_zeros(self):
        """Edge case: 16 zeros should still match the digit pattern."""
        result = detect_pii_regex("0000000000000000")
        assert "NIK" in result

    def test_16_digits_all_nines(self):
        """Edge case: 16 nines should still match."""
        result = detect_pii_regex("9999999999999999")
        assert "NIK" in result

    def test_multiple_niks_in_one_string(self):
        """Two separate 16-digit numbers should both be captured."""
        text = "NIK A: 1111111111111111, NIK B: 2222222222222222"
        result = detect_pii_regex(text)
        assert "NIK" in result
        assert len(result["NIK"]) == 2

    # ── Negative: must NOT detect ──

    def test_15_digits_rejected(self):
        """15 digits must not match the NIK pattern."""
        result = detect_pii_regex("123456789012345")
        assert "NIK" not in result

    def test_17_digits_rejected(self):
        """17 digits must not match (word boundary prevents it)."""
        result = detect_pii_regex("12345678901234567")
        assert "NIK" not in result

    def test_12_digits_rejected(self):
        """12 digits must not match."""
        result = detect_pii_regex("123456789012")
        assert "NIK" not in result

    def test_alphabetic_string_rejected(self):
        """Pure text strings must not trigger NIK detection."""
        result = detect_pii_regex("abcdefghijklmnop")
        assert "NIK" not in result

    def test_mixed_alpha_numeric_rejected(self):
        """A 16-char mixed string (letters+digits) must not match."""
        result = detect_pii_regex("32AB150708CD0001")
        assert "NIK" not in result

    def test_empty_string_rejected(self):
        """Empty input must return no detections."""
        result = detect_pii_regex("")
        assert "NIK" not in result


# ═════════════════════════════════════════════════════
# SECTION 2: Phone Regex — 08xx and +62 Formats
# ═════════════════════════════════════════════════════

class TestPhoneRegexValidation:
    """
    Validates that the phone regex captures Indonesian mobile numbers
    in 08xx, +62, and 62 prefix formats, and rejects non-mobile patterns.
    """

    # ── Positive: 08xx formats ──

    def test_0812_prefix(self):
        result = detect_pii_regex("081234567890")
        assert "NO_HP" in result

    def test_0852_prefix(self):
        result = detect_pii_regex("085234567890")
        assert "NO_HP" in result

    def test_0877_prefix(self):
        result = detect_pii_regex("087734567890")
        assert "NO_HP" in result

    def test_0895_prefix(self):
        result = detect_pii_regex("089534567890")
        assert "NO_HP" in result

    def test_0813_short_number(self):
        """Shorter valid mobile number (11 digits total) must be captured."""
        result = detect_pii_regex("08131234567")
        assert "NO_HP" in result

    def test_08xx_in_text(self):
        """Phone number embedded in sentence must be captured."""
        result = detect_pii_regex("Contact at 081298765432 for details")
        assert "NO_HP" in result

    # ── Positive: +62 formats ──

    def test_plus62_prefix(self):
        result = detect_pii_regex("+6281234567890")
        assert "NO_HP" in result

    def test_plus62_different_operator(self):
        result = detect_pii_regex("+6285298765432")
        assert "NO_HP" in result

    def test_plus62_in_text(self):
        result = detect_pii_regex("Call +6287812345678 immediately")
        assert "NO_HP" in result

    # ── Positive: 62 (no plus) format ──

    def test_62_without_plus(self):
        result = detect_pii_regex("6281234567890")
        assert "NO_HP" in result

    # ── Negative: must NOT detect ──

    def test_landline_021_rejected(self):
        """Jakarta landline (021) must not match mobile pattern."""
        result = detect_pii_regex("0211234567")
        assert "NO_HP" not in result

    def test_landline_022_rejected(self):
        """Bandung landline (022) must not match."""
        result = detect_pii_regex("0221234567")
        assert "NO_HP" not in result

    def test_too_short_rejected(self):
        """A number with too few digits after prefix must not match."""
        result = detect_pii_regex("081234")
        assert "NO_HP" not in result

    def test_plain_text_rejected(self):
        """Non-numeric text must not trigger phone detection."""
        result = detect_pii_regex("this is not a phone number")
        assert "NO_HP" not in result

    def test_international_non_indonesian_rejected(self):
        """Non-Indonesian international format must not match."""
        result = detect_pii_regex("+14155551234")
        assert "NO_HP" not in result

    def test_empty_string_rejected(self):
        result = detect_pii_regex("")
        assert "NO_HP" not in result


# ═════════════════════════════════════════════════════
# SECTION 3: Non-PII Column Preservation
# ═════════════════════════════════════════════════════

class TestNonPIIColumnPreservation:
    """
    Validates that the redaction engine never modifies columns
    that are explicitly outside the PII scope (salary/gaji, etc.).
    Tests both partial masking and full redaction modes.
    """

    @pytest.fixture
    def sample_employee_df(self):
        """Standard multi-row employee DataFrame for integrity testing."""
        return pd.DataFrame({
            "nama": ["Budi Santoso", "Siti Rahayu", "Andi Prasetyo"],
            "nik": ["3201150708900001", "3202230411850002", "3301010101010003"],
            "no_hp": ["081234567890", "085298765432", "087712345678"],
            "email": ["budi@gmail.com", "siti@yahoo.co.id", "andi@company.com"],
            "alamat": ["Jl. Merdeka No. 1", "Gg. Kenanga No. 5", "Jl. Sudirman No. 10"],
            "gaji": ["Rp 15.000.000", "Rp 8.500.000", "Rp 22.000.000"],
            "npwp": ["12.345.678.9-012.345", "98.765.432.1-098.765", "11.222.333.4-555.666"],
        })

    # ── Partial Masking Mode ──

    def test_salary_intact_after_partial_mask(self, sample_employee_df):
        """Every salary value must be byte-identical after partial masking."""
        original_salaries = sample_employee_df["gaji"].tolist()
        df_redacted, _, _ = redact_dataframe(sample_employee_df, mode="mask", use_ner=False)
        redacted_salaries = df_redacted["gaji"].tolist()
        assert original_salaries == redacted_salaries

    def test_nik_changed_after_partial_mask(self, sample_employee_df):
        """NIK values must be modified (confirming redaction works on PII columns)."""
        df_redacted, _, _ = redact_dataframe(sample_employee_df, mode="mask", use_ner=False)
        for idx in range(len(sample_employee_df)):
            assert df_redacted.at[idx, "nik"] != sample_employee_df.at[idx, "nik"]
            assert "*" in df_redacted.at[idx, "nik"]

    def test_email_changed_after_partial_mask(self, sample_employee_df):
        """Email values must be masked (confirming other PII columns are redacted)."""
        df_redacted, _, _ = redact_dataframe(sample_employee_df, mode="mask", use_ner=False)
        for idx in range(len(sample_employee_df)):
            assert "*" in df_redacted.at[idx, "email"]

    def test_phone_changed_after_partial_mask(self, sample_employee_df):
        """Phone values must be masked."""
        df_redacted, _, _ = redact_dataframe(sample_employee_df, mode="mask", use_ner=False)
        for idx in range(len(sample_employee_df)):
            assert "*" in df_redacted.at[idx, "no_hp"]

    # ── Full Redaction Mode ──

    def test_salary_intact_after_full_redaction(self, sample_employee_df):
        """Salary must remain untouched even in full redaction mode."""
        original_salaries = sample_employee_df["gaji"].tolist()
        df_redacted, _, _ = redact_dataframe(sample_employee_df, mode="full", use_ner=False)
        redacted_salaries = df_redacted["gaji"].tolist()
        assert original_salaries == redacted_salaries

    def test_nik_fully_redacted(self, sample_employee_df):
        """NIK must be replaced with [REDACTED-*] tokens in full mode."""
        df_redacted, _, _ = redact_dataframe(sample_employee_df, mode="full", use_ner=False)
        for idx in range(len(sample_employee_df)):
            assert "[REDACTED" in df_redacted.at[idx, "nik"]

    # ── Edge: single-column salary-only DataFrame ──

    def test_salary_only_dataframe_unchanged(self):
        """A DataFrame with only salary data must pass through completely untouched."""
        df = pd.DataFrame({"gaji": ["Rp 5.000.000", "Rp 10.000.000", "Rp 25.000.000"]})
        df_redacted, _, summary = redact_dataframe(df, mode="mask", use_ner=False)
        assert df.equals(df_redacted)
        assert len(summary) == 0  # no PII detected at all

    # ── Edge: row count and column count integrity ──

    def test_row_count_preserved(self, sample_employee_df):
        """Redaction must not add or remove rows."""
        df_redacted, _, _ = redact_dataframe(sample_employee_df, mode="mask", use_ner=False)
        assert len(df_redacted) == len(sample_employee_df)

    def test_column_count_preserved(self, sample_employee_df):
        """Redaction must not add or remove columns."""
        df_redacted, _, _ = redact_dataframe(sample_employee_df, mode="mask", use_ner=False)
        assert list(df_redacted.columns) == list(sample_employee_df.columns)

    def test_address_column_has_no_masking_on_non_pii(self):
        """Address column without phone/email/NIK/NPWP patterns should remain unchanged."""
        df = pd.DataFrame({
            "alamat": ["Jl. Merdeka No. 1, Jakarta"],
            "gaji": ["Rp 7.000.000"],
        })
        df_redacted, _, _ = redact_dataframe(df, mode="mask", use_ner=False)
        assert df_redacted.at[0, "alamat"] == "Jl. Merdeka No. 1, Jakarta"
        assert df_redacted.at[0, "gaji"] == "Rp 7.000.000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
