"""RCSB PDB entry → has_structure relationships (polymer entities mapped to UniProt).

Each UniProt accession aligned to a polymer entity of the entry yields one
``uniprot:<acc> has_structure pdb:<id>`` relationship. It is backed by an RCSB PDB
SourceAssertion whose subject is the structure record (``pdb:<id>``), so structure facts
keep their own subject. Qualifiers add what UniProt cross-references cannot state: polymer
entities, the other entities present (complexes) and bound ligands.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.core.structures import coverage, merge_ranges, normalize_methods


def _entities(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for pe in entry.get("polymer_entities") or []:
        ids = pe.get("rcsb_polymer_entity_container_identifiers") or {}
        ranges: Dict[str, List[List[int]]] = {}
        for align in pe.get("rcsb_polymer_entity_align") or []:
            if align.get("reference_database_name") != "UniProt":
                continue
            acc = align.get("reference_database_accession")
            for region in align.get("aligned_regions") or []:
                beg, length = region.get("ref_beg_seq_id"), region.get("length")
                if acc and beg is not None and length:
                    ranges.setdefault(acc, []).append([beg, beg + length - 1])
        out.append(
            {
                "polymer_entity": str(ids.get("entity_id")),
                "description": (pe.get("rcsb_polymer_entity") or {}).get(
                    "pdbx_description"
                ),
                "chains": sorted(ids.get("auth_asym_ids") or []),
                "uniprot": sorted(set(ids.get("uniprot_ids") or []) | set(ranges)),
                "ranges": ranges,
            }
        )
    return out


def map_structure_entities(
    entry: Dict[str, Any],
    retrieved_at: str,
    subjects: Iterable[str] | None = None,
    reference_lengths: Dict[str, int] | None = None,
) -> Dict[str, Any]:
    """Map an RCSB entry (GraphQL ``entry``) to has_structure relationships.

    ``subjects`` restricts the output to these UniProt accessions (e.g. the card's
    entity); ``reference_lengths`` gives canonical lengths used to compute coverage.
    """
    pdb_id = entry["rcsb_id"]
    structure_ref = f"pdb:{pdb_id}"
    methods = [m.get("method") for m in entry.get("exptl") or []]
    resolutions = (entry.get("rcsb_entry_info") or {}).get("resolution_combined") or []
    ligands = [
        {
            "comp_id": (
                n.get("rcsb_nonpolymer_entity_container_identifiers") or {}
            ).get("nonpolymer_comp_id"),
            "description": (n.get("rcsb_nonpolymer_entity") or {}).get(
                "pdbx_description"
            ),
        }
        for n in entry.get("nonpolymer_entities") or []
    ]
    entities = _entities(entry)
    wanted = set(subjects) if subjects is not None else None
    lengths = reference_lengths or {}

    source_assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    accessions = sorted({acc for e in entities for acc in e["uniprot"]})
    for acc in accessions:
        if wanted is not None and acc not in wanted:
            continue
        mine = [e for e in entities if acc in e["uniprot"]]
        others = [
            {k: e[k] for k in ("polymer_entity", "description", "uniprot")}
            for e in entities
            if acc not in e["uniprot"]
        ]
        ranges = merge_ranges([r for e in mine for r in e["ranges"].get(acc, [])])
        stated = {
            "subject_ref": f"uniprot:{acc}",
            "object_ref": structure_ref,
            "methods": methods,
            "resolution_combined": resolutions,
            "polymer_entities": [
                {k: e[k] for k in ("polymer_entity", "description", "chains")}
                | {"aligned_ranges": e["ranges"].get(acc, [])}
                for e in mine
            ],
        }
        assertion = make_source_assertion(
            "relationships.has_structure", stated, "RCSB PDB", pdb_id, retrieved_at
        )
        source_assertions.append(assertion)
        qualifiers: Dict[str, Any] = {
            "method": normalize_methods(methods),
            "resolution_angstrom": resolutions[0] if resolutions else None,
            "chains": sorted({c for e in mine for c in e["chains"]}),
            "ranges": ranges,
            "polymer_entities": [e["polymer_entity"] for e in mine],
            "other_entities": others,
            "ligands": ligands,
        }
        if lengths.get(acc):
            qualifiers["coverage"] = coverage(ranges, lengths[acc])
        relationships.append(
            make_relationship(
                f"uniprot:{acc}",
                "has_structure",
                structure_ref,
                qualifiers=qualifiers,
                source_assertion_ids=[assertion["id"]],
            )
        )
    return {
        "fields": {},
        "source_assertions": source_assertions,
        "field_source_assertions": {},
        "relationships": relationships,
    }
