"""
redaction_policy.py
Role-Based Redaction Policy Module.

Defines preset policy profiles that determine how each PII type should be
handled (visible, masked, or fully redacted) based on organizational role.
"""

from typing import Dict, Optional


# Redaction modes per field
MODE_VISIBLE = "visible"    # No redaction — field is shown as-is
MODE_MASK = "mask"          # Partial masking (e.g., 0812****5678)
MODE_FULL = "full"          # Full redaction (e.g., [REDACTED-NIK])
MODE_TOKENIZE = "tokenize"  # Pseudo-anonymized token (e.g., [EMP_001])


# ──────────────────────────────────────────────
# Preset Policy Profiles
# ──────────────────────────────────────────────

POLICY_PROFILES: Dict[str, Dict[str, str]] = {
    "hr_manager": {
        "NAMA": MODE_VISIBLE,
        "NIK": MODE_MASK,
        "NO_HP": MODE_MASK,
        "EMAIL": MODE_VISIBLE,
        "NPWP": MODE_MASK,
        "NO_REKENING": MODE_MASK,
    },
    "finance": {
        "NAMA": MODE_MASK,
        "NIK": MODE_FULL,
        "NO_HP": MODE_FULL,
        "EMAIL": MODE_MASK,
        "NPWP": MODE_VISIBLE,
        "NO_REKENING": MODE_MASK,
    },
    "external_auditor": {
        "NAMA": MODE_FULL,
        "NIK": MODE_FULL,
        "NO_HP": MODE_FULL,
        "EMAIL": MODE_FULL,
        "NPWP": MODE_FULL,
        "NO_REKENING": MODE_FULL,
    },
    "it_admin": {
        "NAMA": MODE_MASK,
        "NIK": MODE_MASK,
        "NO_HP": MODE_MASK,
        "EMAIL": MODE_MASK,
        "NPWP": MODE_MASK,
        "NO_REKENING": MODE_MASK,
    },
}


# Human-readable labels for the UI
POLICY_LABELS = {
    "hr_manager": "HR Manager",
    "finance": "Finance Department",
    "external_auditor": "External Auditor",
    "it_admin": "IT Administrator",
    "custom": "Custom Policy",
}


PII_TYPE_LABELS = {
    "NAMA": "Full Name",
    "NIK": "National ID (NIK)",
    "NO_HP": "Phone Number",
    "EMAIL": "Email Address",
    "NPWP": "Tax ID (NPWP)",
    "NO_REKENING": "Bank Account",
}

ALL_PII_TYPES = ["NAMA", "NIK", "NO_HP", "EMAIL", "NPWP", "NO_REKENING"]

MODE_OPTIONS = [MODE_VISIBLE, MODE_MASK, MODE_FULL, MODE_TOKENIZE]

MODE_LABELS = {
    MODE_VISIBLE: "Visible (No Redaction)",
    MODE_MASK: "Partial Masking",
    MODE_FULL: "Full Redaction",
    MODE_TOKENIZE: "Tokenized",
}


def get_policy(policy_name: str) -> Optional[Dict[str, str]]:
    """
    Retrieves a preset policy profile by name.

    Args:
        policy_name: One of the preset profile keys (e.g., "hr_manager").

    Returns:
        Dictionary mapping PII type to redaction mode, or None if not found.
    """
    return POLICY_PROFILES.get(policy_name)


def get_field_mode(policy: Dict[str, str], pii_type: str, fallback: str = MODE_MASK) -> str:
    """
    Returns the redaction mode for a specific PII type within a policy.

    Args:
        policy: Policy dictionary {pii_type: mode}.
        pii_type: The PII category to look up.
        fallback: Default mode if the type is not in the policy.

    Returns:
        Redaction mode string.
    """
    return policy.get(pii_type, fallback)
