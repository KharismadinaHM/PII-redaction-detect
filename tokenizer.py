"""
tokenizer.py
Consistent Pseudo-anonymization / Tokenization Module.

Maintains a persistent mapping of original PII values to deterministic
tokens (e.g., [EMP_001], [NIK_001]) ensuring the same input always
produces the same output across an entire document or batch.
"""

import json
import threading
from typing import Dict, Optional


# Token prefixes per PII type
TOKEN_PREFIXES = {
    "NAMA": "EMP",
    "NIK": "NIK",
    "NO_HP": "PHONE",
    "EMAIL": "EMAIL",
    "NPWP": "NPWP",
    "NO_REKENING": "ACCT",
}


class PIITokenizer:
    """
    Thread-safe tokenizer that maps raw PII values to consistent
    pseudo-anonymous tokens.

    Usage:
        tokenizer = PIITokenizer()
        token = tokenizer.tokenize("Budi Santoso", "NAMA")
        # Returns "[EMP_001]"
        token = tokenizer.tokenize("Budi Santoso", "NAMA")
        # Returns "[EMP_001]" again (same input = same output)
    """

    def __init__(self):
        self._lock = threading.Lock()
        # {pii_type: {original_value: token_string}}
        self._mappings: Dict[str, Dict[str, str]] = {}
        # {pii_type: current_counter}
        self._counters: Dict[str, int] = {}

    def tokenize(self, value: str, pii_type: str) -> str:
        """
        Returns a consistent token for the given PII value.

        If the value has been seen before (for this PII type),
        returns the same token. Otherwise, assigns a new one.

        Args:
            value: The raw PII string (e.g., "Budi Santoso").
            pii_type: The PII category (e.g., "NAMA", "NIK").

        Returns:
            Token string like "[EMP_001]".
        """
        value_key = str(value).strip()
        if not value_key:
            return value

        with self._lock:
            if pii_type not in self._mappings:
                self._mappings[pii_type] = {}
                self._counters[pii_type] = 0

            if value_key in self._mappings[pii_type]:
                return self._mappings[pii_type][value_key]

            self._counters[pii_type] += 1
            prefix = TOKEN_PREFIXES.get(pii_type, pii_type)
            token = f"[{prefix}_{self._counters[pii_type]:03d}]"
            self._mappings[pii_type][value_key] = token
            return token

    def get_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Returns the complete mapping dictionary.

        Returns:
            Nested dictionary: {pii_type: {original_value: token}}.
        """
        with self._lock:
            return {
                pii_type: dict(mapping)
                for pii_type, mapping in self._mappings.items()
            }

    def get_reverse_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Returns the reverse mapping (token -> original value).

        Returns:
            Nested dictionary: {pii_type: {token: original_value}}.
        """
        with self._lock:
            return {
                pii_type: {v: k for k, v in mapping.items()}
                for pii_type, mapping in self._mappings.items()
            }

    def export_json(self) -> str:
        """
        Exports the mapping as a JSON string.

        Returns:
            JSON-formatted mapping string.
        """
        return json.dumps(self.get_mapping(), ensure_ascii=False, indent=2)

    def import_json(self, json_str: str) -> None:
        """
        Imports a mapping from a JSON string, merging with existing state.

        Args:
            json_str: JSON-formatted mapping string.
        """
        data = json.loads(json_str)
        with self._lock:
            for pii_type, mapping in data.items():
                if pii_type not in self._mappings:
                    self._mappings[pii_type] = {}
                    self._counters[pii_type] = 0
                for original, token in mapping.items():
                    self._mappings[pii_type][original] = token
                    # Update counter to max seen index
                    try:
                        idx = int(token.split("_")[-1].rstrip("]"))
                        if idx > self._counters[pii_type]:
                            self._counters[pii_type] = idx
                    except (ValueError, IndexError):
                        pass

    def reset(self) -> None:
        """Clears all mappings and counters."""
        with self._lock:
            self._mappings.clear()
            self._counters.clear()

    @property
    def total_tokens(self) -> int:
        """Returns total number of unique tokens assigned."""
        with self._lock:
            return sum(len(m) for m in self._mappings.values())
