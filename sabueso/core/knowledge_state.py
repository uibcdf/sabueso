"""What a card knows, and what it knows it does not know (uibcdf/sabueso#56).

``knowledge_state(card)`` gives one row per knowledge area and source:

- ``known``: the source states it (``count`` items, where it applies);
- ``conflicting``: sources disagree about it (``quality.conflicts``);
- ``not_stated``: the source was consulted and states nothing. For example UniProt,
  at its release, has no subcellular location for the entry, or ChEMBL has no
  target;
- ``not_queried``: the enrichment that would answer it was not requested;
- ``unavailable``: the source failed, so nothing can be said.

These are knowledge states, not Evidence. "Not stated by UniProt at release 120" is a
fact about a source; what the absence means for a project is interpreted in Nextia.
Rule ``knowledge_state@1``.
"""

from __future__ import annotations

from typing import Any, Dict, List

KNOWLEDGE_STATE_RULE = "knowledge_state@1"

#: Protein enrichments: (area, source, which enrichment records answer it).
PROTEIN_ENRICHMENTS = (
    ("relationships.has_structure (entry details)", "RCSB PDB", {"source": "RCSB PDB"}),
    ("relationships.has_bioactivity", "ChEMBL", {"source": "ChEMBL"}),
    ("relationships.has_bioactivity", "BindingDB", {"source": "BindingDB"}),
    (
        "relationships.has_bioactivity",
        "PubChem BioAssay",
        {"source": "PubChem BioAssay"},
    ),
    ("relationships.functionally_associated_with", "STRING", {"source": "STRING"}),
    (
        "relationships.has_ligand_site",
        "PDBe-KB",
        {"source": "PDBe-KB", "data": "ligand_sites"},
    ),
    (
        "relationships.has_interface_with",
        "PDBe-KB",
        {"source": "PDBe-KB", "data": "interface_residues"},
    ),
    ("features_positional.family_site", "InterPro", {"source": "InterPro"}),
    (
        "relationships.has_predicted_structure",
        "AlphaFold DB",
        {"source": "AlphaFold DB"},
    ),
    ("annotations.taxonomy", "NCBI Taxonomy", {"source": "NCBI Taxonomy"}),
)


def _row(area, source, state, release=None, count=None, **basis) -> Dict[str, Any]:
    return {
        "area": area,
        "source": source,
        "release": release,
        "state": state,
        "count": count,
        "basis": {k: v for k, v in basis.items() if v is not None},
    }


def _enrichment_row(area: str, source: str, records: List[Dict[str, Any]]):
    if not records:
        return _row(area, source, "not_queried")
    statuses = [r.get("status") for r in records]
    count = sum(r.get("count") or 0 for r in records if r.get("status") == "added")
    releases = sorted({str(r["version"]) for r in records if r.get("version")})
    release = "; ".join(releases) or None
    details = sorted({r["detail"] for r in records if r.get("detail")})
    basis = dict(
        requests=len(records),
        not_found=statuses.count("not_found") or None,
        errors=statuses.count("error") or None,
        detail="; ".join(details) or None,
    )
    if count:
        return _row(area, source, "known", release, count, **basis)
    if "error" in statuses:
        # Nothing stated, and at least one request failed: nothing can be said.
        return _row(area, source, "unavailable", release, **basis)
    return _row(area, source, "not_stated", release, 0, **basis)


def _supporting_sources(card: Any, ids: List[str]) -> Dict[str, set]:
    by_source: Dict[str, set] = {}
    for sa_id in ids:
        sa = card.source_assertion_store.get(sa_id) or {}
        source = (sa.get("source") or {}).get("name")
        if source:
            by_source.setdefault(source, set()).add(
                str((sa.get("source") or {}).get("version") or "")
            )
    return by_source


def knowledge_state(card: Any) -> Dict[str, Any]:
    """``{"rows": [...], "rule": {...}}``; see the module docstring."""
    from sabueso.mappings.uniprot import STATED_FIELDS, STATED_PREDICATES

    from .relationship_store import make_derivation

    rows: List[Dict[str, Any]] = []
    conflicting = {c.get("field") for c in card.quality.get("conflicts", [])}
    fields = {}
    for path in card.list_fields():
        node = card.get(path)
        if isinstance(node, dict) and "source_assertion_ids" in node:
            fields[path] = node

    # Fields, by the sources that state them.
    for path in sorted(fields):
        sources = _supporting_sources(card, fields[path]["source_assertion_ids"])
        for source, releases in sorted(sources.items()):
            value = fields[path].get("value")
            rows.append(
                _row(
                    path,
                    source,
                    "conflicting" if path in conflicting else "known",
                    "; ".join(sorted(r for r in releases if r)) or None,
                    len(value) if isinstance(value, list) else None,
                )
            )

    is_protein = card.meta.get("entity_type") == "protein"
    uniprot = [
        s
        for s in (
            ((card.quality.get("entity_resolution") or {}).get("decision") or {}).get(
                "sources"
            )
            or []
        )
        if s.get("name") == "UniProt" and s.get("record")
    ]
    if is_protein and (uniprot or "identifiers.uniprot" in fields):
        release = None
        if "identifiers.uniprot" in fields:
            (release,) = _supporting_sources(
                card, fields["identifiers.uniprot"]["source_assertion_ids"]
            ).get("UniProt", {None}) or {None}
        # What UniProt could have stated and did not.
        for path in sorted(STATED_FIELDS - set(fields)):
            rows.append(_row(path, "UniProt", "not_stated", release or None, 0))
        relationships = card.relationship_store.to_list()
        for predicate in sorted(STATED_PREDICATES):
            count = sum(
                1
                for r in relationships
                if r["predicate"] == predicate
                and "UniProt"
                in _supporting_sources(card, r.get("source_assertion_ids") or [])
            )
            rows.append(
                _row(
                    f"relationships.{predicate}",
                    "UniProt",
                    "known" if count else "not_stated",
                    release or None,
                    count,
                )
            )

    enrichments = card.quality.get("enrichments") or []
    if is_protein:
        stated = {(r["area"], r["source"]) for r in rows}
        for area, source, match in PROTEIN_ENRICHMENTS:
            if (area, source) in stated:
                continue  # the field's own row already says what the source states
            records = [
                r for r in enrichments if all(r.get(k) == v for k, v in match.items())
            ]
            rows.append(_enrichment_row(area, source, records))
    else:
        by_source: Dict[str, List[Dict[str, Any]]] = {}
        for record in enrichments:
            by_source.setdefault(record.get("source") or "unknown", []).append(record)
        for source, records in sorted(by_source.items()):
            rows.append(_enrichment_row("records", source, records))

    return {
        "rows": rows,
        "rule": make_derivation(
            KNOWLEDGE_STATE_RULE,
            inputs=[
                "sections",
                "relationships",
                "quality.enrichments",
                "quality.conflicts",
            ],
            parameters={
                "states": [
                    "known",
                    "conflicting",
                    "not_stated",
                    "not_queried",
                    "unavailable",
                ],
                "uniprot_fields": sorted(STATED_FIELDS),
                "uniprot_predicates": sorted(STATED_PREDICATES),
            },
        ),
    }
