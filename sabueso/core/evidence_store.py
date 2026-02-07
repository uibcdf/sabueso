"""EvidenceStore implementation."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


def _stable_value_repr(value: Any) -> str:
    """Return a stable string representation for hashing."""
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, default=str)
    except TypeError:
        return str(value)


def generate_evidence_id(source_name: str, record_id: str, field: str, value: Any) -> str:
    """Generate a deterministic evidence_id from source+record+field+value."""
    payload = "|".join(
        [
            source_name or "",
            record_id or "",
            field or "",
            _stable_value_repr(value),
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"E_{source_name}_{record_id}_{digest}"


class EvidenceStore:
    """Registry of evidence objects referenced by cards."""

    def __init__(self) -> None:
        self.store: Dict[str, Dict[str, Any]] = {}

    def add(self, evidence: Dict[str, Any]) -> str:
        """Add evidence and return evidence_id (generated if missing)."""
        if "evidence_id" in evidence and evidence["evidence_id"]:
            evidence_id = evidence["evidence_id"]
        else:
            source = evidence.get("source", {}) or {}
            source_name = source.get("name", "")
            record_id = source.get("record_id", "")
            field = evidence.get("field", "")
            value = evidence.get("value")
            evidence_id = generate_evidence_id(source_name, record_id, field, value)
            evidence["evidence_id"] = evidence_id

        self.store[evidence_id] = evidence
        return evidence_id

    def get(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        return self.store.get(evidence_id)

    def find_by_field(self, field_path: str) -> List[Dict[str, Any]]:
        return [e for e in self.store.values() if e.get("field") == field_path]
