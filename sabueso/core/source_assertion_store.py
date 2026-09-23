"""SourceAssertion records and the SourceAssertionStore.

A SourceAssertion records what an external source asserts about an entity or property.
It is not project Evidence (a Nextia concept) and not Provenance in general: it is a
knowledge object that carries its own provenance (source, record, version, retrieval).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, TypedDict


class SourceRef(TypedDict, total=False):
    """Identity of the external source record behind a SourceAssertion."""

    type: str
    name: str
    record_id: str
    version: str


class SourceAssertion(TypedDict, total=False):
    """What an external source asserts about a field of an entity."""

    source_assertion_id: str
    field: str
    value: Any
    source: SourceRef
    retrieved_at: str
    source_meta: Dict[str, Any]


def _stable_value_repr(value: Any) -> str:
    """Return a stable string representation for hashing."""
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, default=str)
    except TypeError:
        return str(value)


def generate_source_assertion_id(source_name: str, record_id: str, field: str, value: Any) -> str:
    """Generate a deterministic source_assertion_id from source+record+field+value."""
    payload = "|".join(
        [
            source_name or "",
            record_id or "",
            field or "",
            _stable_value_repr(value),
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"SA_{source_name}_{record_id}_{digest}"


def make_source_assertion(
    field: str,
    value: Any,
    source_name: str,
    record_id: str,
    retrieved_at: str,
    source_type: str = "database",
) -> SourceAssertion:
    """Build a SourceAssertion with its deterministic id."""
    return {
        "field": field,
        "value": value,
        "source": {"type": source_type, "name": source_name, "record_id": record_id},
        "retrieved_at": retrieved_at,
        "source_assertion_id": generate_source_assertion_id(source_name, record_id, field, value),
    }


class SourceAssertionStore:
    """Registry of the SourceAssertions referenced by a card."""

    def __init__(self, assertions: List[SourceAssertion] | None = None) -> None:
        self.store: Dict[str, SourceAssertion] = {}
        for assertion in assertions or []:
            self.add(assertion)

    def add(self, assertion: SourceAssertion) -> str:
        """Add a SourceAssertion and return its id (generated if missing)."""
        if "source_assertion_id" in assertion and assertion["source_assertion_id"]:
            assertion_id = assertion["source_assertion_id"]
        else:
            source = assertion.get("source", {}) or {}
            source_name = source.get("name", "")
            record_id = source.get("record_id", "")
            field = assertion.get("field", "")
            value = assertion.get("value")
            assertion_id = generate_source_assertion_id(source_name, record_id, field, value)
            assertion["source_assertion_id"] = assertion_id

        self.store[assertion_id] = assertion
        return assertion_id

    def get(self, source_assertion_id: str) -> Optional[SourceAssertion]:
        return self.store.get(source_assertion_id)

    def find_by_field(self, field_path: str) -> List[SourceAssertion]:
        return [a for a in self.store.values() if a.get("field") == field_path]

    def to_list(self) -> List[SourceAssertion]:
        return list(self.store.values())
