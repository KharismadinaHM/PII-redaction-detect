"""
test_new_features.py
Tests for Indonesian name gazetteer, PIITokenizer, and role-based policies.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detector import (
    detect_name_gazetteer,
    detect_name_hybrid,
    detect_all_pii,
    detect_pii_in_value,
)
from tokenizer import PIITokenizer
from redaction_policy import (
    get_policy,
    get_field_mode,
    POLICY_PROFILES,
    MODE_VISIBLE,
    MODE_MASK,
    MODE_FULL,
)
from redactor import redact_value


# ═══════════════════════════════════════════════
# 1. Indonesian Name Gazetteer Tests
# ═══════════════════════════════════════════════

class TestIndonesianNameGazetteer(unittest.TestCase):
    """Tests for the Indonesian name gazetteer detection."""

    def test_detect_common_male_name(self):
        result = detect_name_gazetteer("Data karyawan Budi Santoso departemen IT")
        self.assertTrue(any("Budi" in n and "Santoso" in n for n in result))

    def test_detect_common_female_name(self):
        result = detect_name_gazetteer("Siti Rahayu adalah manajer baru")
        self.assertTrue(any("Siti" in n and "Rahayu" in n for n in result))

    def test_detect_batak_surname(self):
        result = detect_name_gazetteer("Herman Simanjuntak bergabung bulan lalu")
        self.assertTrue(any("Simanjuntak" in n for n in result))

    def test_no_match_random_text(self):
        result = detect_name_gazetteer("Jumlah total pengeluaran adalah 5000000")
        self.assertEqual(len(result), 0)

    def test_single_first_name_no_match(self):
        """Single first name without surname should not trigger."""
        result = detect_name_gazetteer("Budi saja")
        # "Budi saja" - "saja" is not a known name, so should be empty
        self.assertEqual(len(result), 0)

    def test_multiple_names_in_text(self):
        text = "Peserta: Agus Pratama dan Dewi Lestari hadir"
        result = detect_name_gazetteer(text)
        self.assertGreaterEqual(len(result), 2)

    def test_hybrid_combines_ner_and_gazetteer(self):
        """Hybrid should return at least what gazetteer finds."""
        text = "Budi Santoso bekerja di Jakarta"
        gaz_result = detect_name_gazetteer(text)
        hybrid_result = detect_name_hybrid(text, use_ner=True)
        # Hybrid should find at least as many as gazetteer
        self.assertGreaterEqual(len(hybrid_result), len(gaz_result))

    def test_detect_all_pii_includes_gazetteer_names(self):
        text = "NIK: 3201150708900001. Nama: Budi Santoso"
        result = detect_all_pii(text, use_ner=False)
        # Should detect NIK and NAMA via gazetteer (even without NER)
        self.assertIn("NIK", result)
        self.assertIn("NAMA", result)

    def test_column_context_still_works(self):
        """Column-based detection should still tag names correctly."""
        result = detect_pii_in_value("Reza Firmansyah", column_name="nama")
        self.assertIn("NAMA", result)

    def test_gazetteer_case_insensitive(self):
        result = detect_name_gazetteer("BUDI SANTOSO adalah karyawan")
        # Should still match since we lowercase during comparison
        self.assertTrue(any("BUDI" in n for n in result))


# ═══════════════════════════════════════════════
# 2. PIITokenizer Consistency Tests
# ═══════════════════════════════════════════════

class TestPIITokenizer(unittest.TestCase):
    """Tests for consistent pseudo-anonymization."""

    def setUp(self):
        self.tokenizer = PIITokenizer()

    def test_same_value_same_token(self):
        t1 = self.tokenizer.tokenize("Budi Santoso", "NAMA")
        t2 = self.tokenizer.tokenize("Budi Santoso", "NAMA")
        self.assertEqual(t1, t2)

    def test_different_values_different_tokens(self):
        t1 = self.tokenizer.tokenize("Budi Santoso", "NAMA")
        t2 = self.tokenizer.tokenize("Siti Rahayu", "NAMA")
        self.assertNotEqual(t1, t2)

    def test_token_format(self):
        token = self.tokenizer.tokenize("3201150708900001", "NIK")
        self.assertTrue(token.startswith("[NIK_"))
        self.assertTrue(token.endswith("]"))

    def test_incrementing_counters(self):
        t1 = self.tokenizer.tokenize("Alice", "NAMA")
        t2 = self.tokenizer.tokenize("Bob", "NAMA")
        self.assertEqual(t1, "[EMP_001]")
        self.assertEqual(t2, "[EMP_002]")

    def test_cross_type_independence(self):
        t_name = self.tokenizer.tokenize("Budi", "NAMA")
        t_nik = self.tokenizer.tokenize("1234567890123456", "NIK")
        self.assertEqual(t_name, "[EMP_001]")
        self.assertEqual(t_nik, "[NIK_001]")

    def test_total_tokens(self):
        self.tokenizer.tokenize("A", "NAMA")
        self.tokenizer.tokenize("B", "NAMA")
        self.tokenizer.tokenize("C", "NIK")
        self.assertEqual(self.tokenizer.total_tokens, 3)

    def test_export_import_json(self):
        self.tokenizer.tokenize("Budi", "NAMA")
        json_str = self.tokenizer.export_json()
        new_tokenizer = PIITokenizer()
        new_tokenizer.import_json(json_str)
        # After import, same value should get same token
        token = new_tokenizer.tokenize("Budi", "NAMA")
        self.assertEqual(token, "[EMP_001]")

    def test_reset(self):
        self.tokenizer.tokenize("Budi", "NAMA")
        self.tokenizer.reset()
        self.assertEqual(self.tokenizer.total_tokens, 0)

    def test_empty_value(self):
        result = self.tokenizer.tokenize("", "NAMA")
        self.assertEqual(result, "")

    def test_reverse_mapping(self):
        self.tokenizer.tokenize("Budi Santoso", "NAMA")
        reverse = self.tokenizer.get_reverse_mapping()
        self.assertIn("NAMA", reverse)
        self.assertIn("[EMP_001]", reverse["NAMA"])
        self.assertEqual(reverse["NAMA"]["[EMP_001]"], "Budi Santoso")


# ═══════════════════════════════════════════════
# 3. Role-Based Policy Tests
# ═══════════════════════════════════════════════

class TestRedactionPolicy(unittest.TestCase):
    """Tests for role-based redaction policies."""

    def test_hr_manager_policy_exists(self):
        policy = get_policy("hr_manager")
        self.assertIsNotNone(policy)
        self.assertEqual(policy["NAMA"], MODE_VISIBLE)
        self.assertEqual(policy["NIK"], MODE_MASK)

    def test_external_auditor_all_full(self):
        policy = get_policy("external_auditor")
        for pii_type, mode in policy.items():
            self.assertEqual(mode, MODE_FULL)

    def test_finance_npwp_visible(self):
        policy = get_policy("finance")
        self.assertEqual(policy["NPWP"], MODE_VISIBLE)

    def test_get_field_mode_with_fallback(self):
        policy = {"NIK": MODE_FULL}
        mode = get_field_mode(policy, "NO_HP", fallback=MODE_MASK)
        self.assertEqual(mode, MODE_MASK)

    def test_nonexistent_policy(self):
        policy = get_policy("nonexistent")
        self.assertIsNone(policy)

    def test_policy_applied_in_redact_value_visible(self):
        """When policy says visible, value should not change."""
        pii = {"NAMA": ["Budi Santoso"]}
        policy = {"NAMA": MODE_VISIBLE}
        result = redact_value("Budi Santoso", pii, mode="mask", policy=policy)
        self.assertEqual(result, "Budi Santoso")

    def test_policy_applied_in_redact_value_full(self):
        """When policy says full, value should be fully redacted."""
        pii = {"NIK": ["3201150708900001"]}
        policy = {"NIK": MODE_FULL}
        result = redact_value("3201150708900001", pii, mode="mask", policy=policy)
        self.assertIn("[REDACTED", result)

    def test_policy_override_tokenize(self):
        """When policy says tokenize for a field, it should use tokenizer."""
        tokenizer = PIITokenizer()
        pii = {"NIK": ["3201150708900001"]}
        policy = {"NIK": "tokenize"}
        result = redact_value("3201150708900001", pii, mode="mask",
                              policy=policy, tokenizer=tokenizer)
        self.assertTrue(result.startswith("[NIK_"))

    def test_all_profiles_cover_all_types(self):
        """Every profile should have entries for all standard PII types."""
        expected_types = {"NAMA", "NIK", "NO_HP", "EMAIL", "NPWP", "NO_REKENING"}
        for profile_name, profile in POLICY_PROFILES.items():
            self.assertEqual(set(profile.keys()), expected_types,
                             f"Profile {profile_name} missing types")


# ═══════════════════════════════════════════════
# 4. Tokenize Mode Integration
# ═══════════════════════════════════════════════

class TestTokenizeIntegration(unittest.TestCase):
    """Integration tests for tokenize mode in redactor."""

    def test_redact_value_tokenize_mode(self):
        tokenizer = PIITokenizer()
        pii = {"NO_HP": ["081234567890"]}
        result = redact_value("081234567890", pii, mode="tokenize", tokenizer=tokenizer)
        self.assertEqual(result, "[PHONE_001]")

    def test_redact_value_tokenize_consistency(self):
        tokenizer = PIITokenizer()
        pii = {"EMAIL": ["test@example.com"]}
        r1 = redact_value("test@example.com", pii, mode="tokenize", tokenizer=tokenizer)
        r2 = redact_value("test@example.com", pii, mode="tokenize", tokenizer=tokenizer)
        self.assertEqual(r1, r2)

    def test_redact_value_tokenize_without_tokenizer_falls_back(self):
        """Without a tokenizer, tokenize mode should fall back to mask."""
        pii = {"NIK": ["3201150708900001"]}
        result = redact_value("3201150708900001", pii, mode="tokenize", tokenizer=None)
        # Should fall back to mask behavior
        self.assertIn("****", result)


# ═══════════════════════════════════════════════
# 5. Human-in-the-Loop (HITL) Review Tests
# ═══════════════════════════════════════════════

class TestHumanInTheLoopReview(unittest.TestCase):
    """Tests for interactive manual review & spot-checking."""

    def setUp(self):
        import pandas as pd
        self.sample_df = pd.DataFrame({
            "nama": ["Budi Santoso", "Siti Rahayu"],
            "nik": ["3201150708900001", "3202230411850002"],
            "gaji": ["Rp 15.000.000", "Rp 8.500.000"],
        })

    def test_scan_dataframe_for_review(self):
        from redactor import scan_dataframe_for_review
        records, detail, summary = scan_dataframe_for_review(self.sample_df, use_ner=False)
        self.assertGreater(len(records), 0)
        # All items should default to approved=True
        for rec in records:
            self.assertTrue(rec["approved"])
            self.assertIn("row", rec)
            self.assertIn("column", rec)
            self.assertIn("pii_type", rec)
            self.assertIn("matched_text", rec)

    def test_redact_with_selective_approval(self):
        """Disapproving an item should prevent it from being redacted."""
        from redactor import scan_dataframe_for_review, redact_dataframe_with_review
        records, _, _ = scan_dataframe_for_review(self.sample_df, use_ner=False)

        # Unapprove the first NIK (row 0)
        for rec in records:
            if rec["column"] == "nik" and rec["_row_idx"] == 0:
                rec["approved"] = False

        df_redacted, filtered_detail, summary = redact_dataframe_with_review(
            self.sample_df, records, mode="mask"
        )

        # Row 0 NIK should remain untouched (not redacted)
        self.assertEqual(df_redacted.at[0, "nik"], "3201150708900001")
        # Row 1 NIK should be redacted
        self.assertIn("****", df_redacted.at[1, "nik"])

    def test_redact_with_all_disapproved(self):
        """If all items are disapproved, dataframe should be unchanged."""
        from redactor import scan_dataframe_for_review, redact_dataframe_with_review
        records, _, _ = scan_dataframe_for_review(self.sample_df, use_ner=False)
        for rec in records:
            rec["approved"] = False

        df_redacted, filtered_detail, summary = redact_dataframe_with_review(
            self.sample_df, records, mode="mask"
        )
        self.assertEqual(df_redacted.at[0, "nik"], "3201150708900001")
        self.assertEqual(df_redacted.at[1, "nik"], "3202230411850002")
        self.assertEqual(len(summary), 0)

    def test_scan_pdf_for_review(self):
        """PDF pre-scan should extract review items without redacting."""
        from redactor import scan_pdf_for_review
        with open("data/dummy_hybrid.pdf", "rb") as f:
            pdf_bytes = f.read()

        records, page_infos = scan_pdf_for_review(pdf_bytes, use_ner=False, ocr_dpi=150)
        self.assertGreater(len(records), 0)
        self.assertGreater(len(page_infos), 0)
        for rec in records:
            self.assertTrue(rec["approved"])
            self.assertIn("page", rec)
            self.assertIn("pii_type", rec)

    def test_redact_pdf_with_review(self):
        """Redacting PDF with approved records returns valid PDF bytes."""
        from redactor import scan_pdf_for_review, redact_pdf_with_review
        with open("data/dummy_hybrid.pdf", "rb") as f:
            pdf_bytes = f.read()

        records, _ = scan_pdf_for_review(pdf_bytes, use_ner=False, ocr_dpi=150)
        output_bytes, page_meta, summary = redact_pdf_with_review(
            pdf_bytes, records, mode="mask", ocr_dpi=150
        )
        self.assertIsInstance(output_bytes, bytes)
        self.assertGreater(len(output_bytes), 1000)
        self.assertGreater(len(summary), 0)


if __name__ == "__main__":
    unittest.main()

