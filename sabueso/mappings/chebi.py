"""A ChEBI entry → a small molecule's chemical identity, classes and roles (#83).

The entry joins a card only through the InChIKey ChEBI states for its structure
(``same_as`` ``chebi:<n>`` → ``inchikey:<key>``, backed by a ChEBI SourceAssertion).
It states:

- ``identifiers.chebi`` (``CHEBI:<n>``);
- ``names.canonical_name`` and ``properties.physchem.formula``: the native entry's
  name and formula, without deriving identity or rewriting their spelling;
- ``annotations.chemical_classes``: the classes ChEBI says the molecule is a member of
  (``is a``), ``{chebi_id, name}``;
- ``annotations.chemical_roles``: its roles, ``{chebi_id, name, direct, biological_role,
  chemical_role, application}``. ``direct`` roles are the entry's own ``has role``
  statements; the others ChEBI classifies it with through its classes or parent roles
  (e.g. "Bronsted base" through "tertiary amino compound");
- ``annotations.definition`` (``{text}``), as ChEBI writes it.

Each SourceAssertion records the entry's curation level (``stars``).
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, Tuple

from sabueso.core.errors import ConnectorError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.molecule_identity import anchor_ref, is_standard_inchikey

SOURCE = "ChEBI"


def map_chebi_identity(
    record: Dict[str, Any], retrieved_at: str
) -> Tuple[Dict[str, Any], str | None]:
    """ChEBI entry -> (mapping, the standard InChIKey it states, or None)."""
    data = record.get("data") or record
    chebi_id = data.get("chebi_accession")
    key = (data.get("default_structure") or {}).get("standard_inchi_key")
    mapping: Dict[str, Any] = {
        "fields": {},
        "field_source_assertions": {},
        "source_assertions": [],
        "relationships": [],
    }
    if not chebi_id or not is_standard_inchikey(key):
        return mapping, None
    chemical = data.get("chemical_data")
    if chemical is not None and not isinstance(chemical, dict):
        raise ConnectorError("ChEBI chemical_data must be a native object or null.")
    descriptive = {
        "names.canonical_name": data.get("name"),
        "properties.physchem.formula": (chemical or {}).get("formula"),
    }
    for path, value in descriptive.items():
        if value is not None and (
            not isinstance(value, str) or (value and not value.strip())
        ):
            raise ConnectorError(f"ChEBI {path} must be native text or null.")
    number = chebi_id.split(":", 1)[1]
    metadata = {"stars": data.get("stars"), "modified_on": data.get("modified_on")}

    def field(path: str, value: Any) -> None:
        if value in (None, "", []):
            return
        made = make_source_assertion(
            path, value, SOURCE, chebi_id, retrieved_at, subject_ref=f"chebi:{number}"
        )
        made["source_metadata"] = metadata
        mapping["source_assertions"].append(made)
        mapping["fields"][path] = value
        mapping["field_source_assertions"][path] = [made["id"]]

    relations = (data.get("ontology_relations") or {}).get("outgoing_relations") or []
    direct_roles = {
        r.get("final_id") for r in relations if r.get("relation_type") == "has role"
    }
    field("identifiers.chebi", chebi_id)
    for path, value in descriptive.items():
        field(path, value)
    field(
        "annotations.chemical_classes",
        [
            {"chebi_id": f"CHEBI:{r['final_id']}", "name": r.get("final_name")}
            for r in sorted(relations, key=lambda r: r.get("final_id") or 0)
            if r.get("relation_type") == "is a"
        ],
    )
    field(
        "annotations.chemical_roles",
        [
            {
                "chebi_id": role.get("chebi_accession") or f"CHEBI:{role.get('id')}",
                "name": role.get("name"),
                "direct": role.get("id") in direct_roles,
                "biological_role": bool(role.get("biological_role")),
                "chemical_role": bool(role.get("chemical_role")),
                "application": bool(role.get("application")),
            }
            for role in sorted(
                data.get("roles_classification") or [], key=lambda r: r.get("id") or 0
            )
        ],
    )
    if data.get("definition"):
        # As ChEBI writes it, with its markup (C<sub>46</sub>…); the value read is its
        # plain text (a normalization, kept beside the assertion).
        written = data["definition"]
        plain = html.unescape(re.sub(r"<[^>]+>", "", written))
        field("annotations.definition", {"text": written})
        if plain != written:
            (made,) = [
                sa
                for sa in mapping["source_assertions"]
                if sa["field_path"] == "annotations.definition"
            ]
            made["normalized_value"] = {"text": plain}
            mapping["fields"]["annotations.definition"] = {"text": plain}
    stated = make_source_assertion(
        "relationships.same_as",
        {"object_ref": anchor_ref(key), "inchikey": key},
        SOURCE,
        chebi_id,
        retrieved_at,
        subject_ref=f"chebi:{number}",
    )
    stated["source_metadata"] = metadata
    mapping["source_assertions"].append(stated)
    mapping["relationships"].append(
        make_relationship(
            f"chebi:{number}",
            "same_as",
            anchor_ref(key),
            source_assertion_ids=[stated["id"]],
        )
    )
    return mapping, key
