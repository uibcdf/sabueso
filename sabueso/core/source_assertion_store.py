"""SourceAssertion records and the SourceAssertionStore.

A SourceAssertion records what an external source asserts about an entity or property.
It is not project Evidence (a Nextia concept) and not Provenance in general: it is a
knowledge object that carries its own provenance (source, record, version, retrieval).

Field names follow the conceptual contract of MOLI Platform Architecture 1.0
(``uibcdf/moli``, ``schemas/sabueso_source_assertion_conceptual_schema.md``).
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, TypedDict

# Namespaces used to build stable, location-independent subject references
# (``<namespace>:<record_id>``). The syntax is provisional: MOLI Architecture 1.0
# freezes stable referencability, not the identifier format.
SOURCE_NAMESPACES: Dict[str, str] = {
    "UniProt": "uniprot",
    "RCSB PDB": "pdb",
    "PDB CCD": "pdb.ligand",  # wwPDB Chemical Component Dictionary (served by RCSB)
    "UniChem": "unichem",
    "PubChem": "pubchem",
    "ChEMBL": "chembl",
    "GO": "go",
    "InterPro": "interpro",
    "STRING": "string",
    "BioGRID": "biogrid",
    "CATH": "cath",
    "SCOPe": "scope",
    "TED": "ted",
    "PhosphoSitePlus": "phosphositeplus",
}


class SourceRef(TypedDict, total=False):
    """Identity of the external source record behind a SourceAssertion."""

    type: str  # database | literature | patent | curated | other
    name: str
    record_id: str
    version: str


class SourceAssertion(TypedDict, total=False):
    """What an external source asserts about a field of an entity."""

    id: str
    subject_ref: Optional[str]
    field_path: str
    asserted_value: Any
    normalized_value: Any  # only when Sabueso normalization changes the asserted value
    source: SourceRef
    retrieved_at: str
    source_metadata: Dict[
        str, Any
    ]  # source-native qualifiers (e.g., UniProt ECO codes)
    provenance_ref: str


def _stable_value_repr(value: Any) -> str:
    """Return a stable string representation for hashing."""
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, default=str)
    except TypeError:
        return str(value)


def source_namespace(source_name: str) -> str:
    """Return the reference namespace of a source (e.g., ``RCSB PDB`` -> ``pdb``)."""
    if source_name in SOURCE_NAMESPACES:
        return SOURCE_NAMESPACES[source_name]
    return re.sub(r"[^a-z0-9]+", "", (source_name or "").lower())


def make_subject_ref(source_name: str, record_id: str) -> Optional[str]:
    """Reference to the subject of a source record, e.g. ``uniprot:P52789``."""
    if not record_id:
        return None
    return f"{source_namespace(source_name)}:{record_id}"


def generate_source_assertion_id(
    source_name: str, record_id: str, field_path: str, asserted_value: Any
) -> str:
    """Generate a deterministic SourceAssertion id from source+record+field+value."""
    payload = "|".join(
        [
            source_name or "",
            record_id or "",
            field_path or "",
            _stable_value_repr(asserted_value),
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"SA_{source_name}_{record_id}_{digest}"


def make_source_assertion(
    field_path: str,
    asserted_value: Any,
    source_name: str,
    record_id: str,
    retrieved_at: str,
    source_type: str = "database",
    subject_ref: str | None = None,
) -> SourceAssertion:
    """Build a SourceAssertion with its deterministic id and subject reference.

    The subject defaults to ``<source namespace>:<record_id>``. Pass ``subject_ref`` when
    the source keys its record by another namespace, e.g. InterPro and PDBe-KB protein
    records are keyed by UniProt accession, so their subject is ``uniprot:<accession>``.
    """
    return {
        "id": generate_source_assertion_id(
            source_name, record_id, field_path, asserted_value
        ),
        "subject_ref": subject_ref or make_subject_ref(source_name, record_id),
        "field_path": field_path,
        "asserted_value": asserted_value,
        "source": {"type": source_type, "name": source_name, "record_id": record_id},
        "retrieved_at": retrieved_at,
    }


def assertion_value(assertion: SourceAssertion) -> Any:
    """Value used for resolution: the normalized value when present, else the asserted one."""
    if "normalized_value" in assertion:
        return assertion["normalized_value"]
    return assertion.get("asserted_value")


class SourceAssertionStore:
    """Registry of the SourceAssertions referenced by a card."""

    def __init__(self, assertions: List[SourceAssertion] | None = None) -> None:
        self.store: Dict[str, SourceAssertion] = {}
        for assertion in assertions or []:
            self.add(assertion)

    def add(self, assertion: SourceAssertion) -> str:
        """Add a SourceAssertion and return its id (generated if missing)."""
        if assertion.get("id"):
            assertion_id = assertion["id"]
        else:
            source = assertion.get("source", {}) or {}
            assertion_id = generate_source_assertion_id(
                source.get("name", ""),
                source.get("record_id", ""),
                assertion.get("field_path", ""),
                assertion.get("asserted_value"),
            )
            assertion["id"] = assertion_id

        self.store[assertion_id] = assertion
        return assertion_id

    def get(self, source_assertion_id: str) -> Optional[SourceAssertion]:
        return self.store.get(source_assertion_id)

    def find_by_field(self, field_path: str) -> List[SourceAssertion]:
        return [a for a in self.store.values() if a.get("field_path") == field_path]

    def to_list(self) -> List[SourceAssertion]:
        return list(self.store.values())
