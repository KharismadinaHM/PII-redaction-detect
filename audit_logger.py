"""
audit_logger.py
Enterprise Structured Audit Logging Module for PII Redaction Events.

Logs all redaction operations in structured JSON Lines format to data/audit_trail.log
for compliance tracking (e.g. Indonesian Personal Data Protection Act / UU PDP).
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional

AUDIT_LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "audit_trail.log"
)


def compute_sha256(data: bytes) -> str:
    """Computes SHA-256 hash of document bytes for data integrity tracking."""
    return hashlib.sha256(data).hexdigest()


def log_redaction_event(
    document_name: str,
    document_type: str,
    total_records_or_pages: int,
    redaction_mode: str,
    summary: Dict[str, int],
    file_bytes: Optional[bytes] = None,
    user_id: str = "system_operator",
) -> Dict[str, Any]:
    """
    Appends a structured audit event to the audit trail log.

    Args:
        document_name: Name of the processed document.
        document_type: "csv" or "pdf".
        total_records_or_pages: Number of rows (CSV) or pages (PDF).
        redaction_mode: "mask" or "full".
        summary: Dictionary mapping PII types to entity counts.
        file_bytes: Optional raw file bytes to compute SHA-256 integrity hash.
        user_id: Identifier of operator executing the redaction.

    Returns:
        The logged audit entry dictionary.
    """
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)

    file_hash = compute_sha256(file_bytes) if file_bytes else "N/A"
    total_pii = sum(summary.values())

    event = {
        "event_id": f"AUDIT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{os.urandom(3).hex()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "document_name": document_name,
        "document_type": document_type.upper(),
        "file_sha256": file_hash,
        "total_records_or_pages": total_records_or_pages,
        "redaction_mode": redaction_mode,
        "detected_entities_summary": summary,
        "total_pii_entities_redacted": total_pii,
        "compliance_standard": "Indonesian Personal Data Protection Law (UU PDP No. 27/2022)",
    }

    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


def read_audit_log(max_entries: int = 50) -> list:
    """
    Reads the most recent audit log entries.

    Args:
        max_entries: Maximum number of recent log entries to return.

    Returns:
        List of audit event dictionaries, latest first.
    """
    if not os.path.exists(AUDIT_LOG_FILE):
        return []

    entries = []
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return entries[-max_entries:][::-1]
