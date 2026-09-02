"""
tests/test_redactor.py
Unit tests for redactor.py module.
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redactor import (
    mask_nik, mask_phone, mask_email, mask_npwp, mask_name,
    redact_value, redact_dataframe,
)


class TestMaskNIK:
    def test_mask_16_digit(self):
        result = mask_nik("3201150708900001")
        assert result == "3201********0001"
        assert len(result) == 16

    def test_mask_short(self):
        result = mask_nik("1234")
        assert "*" in result


class TestMaskPhone:
    def test_mask_12_digit(self):
        result = mask_phone("081234567890")
        assert result.startswith("0812")
        assert result.endswith("7890")
        assert "****" in result

    def test_mask_preserves_length(self):
        original = "081234567890"
        result = mask_phone(original)
        assert len(result) == len(original)


class TestMaskEmail:
    def test_mask_email_basic(self):
        result = mask_email("budi.santoso@gmail.com")
        assert result.startswith("bu")
        assert "@gmail.com" in result
        assert "*" in result

    def test_mask_email_short_local(self):
        result = mask_email("ab@test.com")
        assert "@test.com" in result


class TestMaskNPWP:
    def test_mask_npwp(self):
        result = mask_npwp("12.345.678.9-012.345")
        assert result.startswith("12.")
        assert "*" in result


class TestMaskName:
    def test_mask_two_words(self):
        result = mask_name("Budi Santoso")
        assert result.startswith("B")
        assert "S" in result
        assert "*" in result

    def test_mask_single_word(self):
        result = mask_name("Budi")
        assert result.startswith("B")
        assert "*" in result


class TestRedactValue:
    def test_mask_mode(self):
        pii = {"NAMA": ["Budi Santoso"]}
        result = redact_value("Budi Santoso", pii, mode="mask")
        assert "B" in result
        assert "*" in result

    def test_full_mode(self):
        pii = {"NAMA": ["Budi Santoso"]}
        result = redact_value("Budi Santoso", pii, mode="full")
        assert "[REDACTED-NAMA]" in result


class TestRedactDataframe:
    def test_salary_preserved(self):
        """Salary column values must remain intact after redaction."""
        df = pd.DataFrame({
            "nama": ["Budi Santoso"],
            "nik": ["3201150708900001"],
            "gaji": ["Rp 15.000.000"],
        })
        df_redacted, _, _ = redact_dataframe(df, mode="mask", use_ner=False)
        assert df_redacted.at[0, "gaji"] == "Rp 15.000.000"

    def test_nik_redacted(self):
        """National ID must be masked in the redacted output DataFrame."""
        df = pd.DataFrame({
            "nama": ["Budi"],
            "nik": ["3201150708900001"],
            "gaji": ["Rp 5.000.000"],
        })
        df_redacted, _, _ = redact_dataframe(df, mode="mask", use_ner=False)
        assert df_redacted.at[0, "nik"] != "3201150708900001"
        assert "*" in df_redacted.at[0, "nik"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
