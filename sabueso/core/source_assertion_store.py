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


#: How a statement entered (#92). ``database``: imported from a source's record;
#: ``curation``: a person read the publication and recorded it; ``rule_extraction`` and
#: ``model_extraction``: extracted from a text by a named tool or model.
ACQUISITION_METHODS = ("database", "curation", "rule_extraction", "model_extraction")
#: What a database states about how its own record was obtained, when it states it.
ORIGINS = ("text_mining",)


class Acquisition(TypedDict, total=False):
    """How a SourceAssertion entered (#92): never how true it is."""

    method: str
    tool: str  # extraction: the tool or model
    version: str  # extraction: its version
    configuration: Dict[str, Any]  # extraction: its settings
    origin: str  # database: how the source states its record was obtained
    validated_by: Dict[str, Any]  # extraction: the curator who confirmed it, and when


def make_acquisition(
    method: str,
    tool: str | None = None,
    version: str | None = None,
    configuration: Dict[str, Any] | None = None,
    origin: str | None = None,
) -> "Acquisition":
    """An acquisition record. An extraction names its tool and version: a statement
    whose extractor cannot be named cannot be reproduced or weighed."""
    from .errors import SchemaError

    if method not in ACQUISITION_METHODS:
        raise SchemaError(f"Unknown acquisition method {method!r}")
    if origin is not None and (method != "database" or origin not in ORIGINS):
        raise SchemaError(f"An origin {origin!r} describes a database's own record")
    extraction = method.endswith("_extraction")
    if extraction and not (tool and version):
        raise SchemaError(f"A {method} names its tool and its version")
    if not extraction and (tool or version or configuration):
        raise SchemaError("Only an extraction has a tool, version and configuration")
    record: Acquisition = {"method": method}
    for key, value in (
        ("tool", tool),
        ("version", version),
        ("configuration", configuration),
        ("origin", origin),
    ):
        if value is not None:
            record[key] = value
    return record


def acquisition_of(assertion: "SourceAssertion") -> Dict[str, Any]:
    """How a SourceAssertion entered, or ``{"method": "not_recorded"}`` for one made
    before acquisition was recorded (card schema 0.3.6 and older)."""
    return dict(assertion.get("acquisition") or {"method": "not_recorded"})


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
    acquisition: Acquisition


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
    acquisition: Acquisition | None = None,
) -> SourceAssertion:
    """Build a SourceAssertion with its deterministic id and subject reference.

    The subject defaults to ``<source namespace>:<record_id>``. Pass ``subject_ref`` when
    the source keys its record by another namespace, e.g. InterPro and PDBe-KB protein
    records are keyed by UniProt accession, so their subject is ``uniprot:<accession>``.

    ``acquisition`` says how the statement entered (#92); a source's record is
    ``{"method": "database"}``.
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
        "acquisition": dict(acquisition or {"method": "database"}),
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
