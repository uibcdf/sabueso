"""RCSB PDB entry → has_structure relationships (polymer entities mapped to UniProt).

Each UniProt accession aligned to a polymer entity of the entry yields one
``uniprot:<acc> has_structure pdb:<id>`` relationship. It is backed by an RCSB PDB
SourceAssertion whose subject is the structure record (``pdb:<id>``), so structure facts
keep their own subject. Qualifiers add what UniProt cross-references cannot state: polymer
entities, the other entities present (complexes) and bound ligands.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from sabueso.core.quantities import LENGTH_UNIT, quantity_node
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.core.structures import coverage, merge_ranges, normalize_methods


def _entities(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for pe in entry.get("polymer_entities") or []:
        ids = pe.get("rcsb_polymer_entity_container_identifiers") or {}
        ranges: Dict[str, List[List[int]]] = {}
        regions: Dict[str, List[tuple]] = {}
        for align in pe.get("rcsb_polymer_entity_align") or []:
            if align.get("reference_database_name") != "UniProt":
                continue
            acc = align.get("reference_database_accession")
            for region in align.get("aligned_regions") or []:
                beg, length = region.get("ref_beg_seq_id"), region.get("length")
                entity_beg = region.get("entity_beg_seq_id")
                if acc and beg is not None and length:
                    ranges.setdefault(acc, []).append([beg, beg + length - 1])
                    if entity_beg is not None:
                        regions.setdefault(acc, []).append((entity_beg, beg, length))
        out.append(
            {
                "polymer_entity": str(ids.get("entity_id")),
                "description": (pe.get("rcsb_polymer_entity") or {}).get(
                    "pdbx_description"
                ),
                "chains": sorted(ids.get("auth_asym_ids") or []),
                "uniprot": sorted(set(ids.get("uniprot_ids") or []) | set(ranges)),
                "ranges": ranges,
                "regions": regions,
                "instances": pe.get("polymer_entity_instances") or [],
            }
        )
    # RCSB returns entities in no fixed order: sort, so that two retrievals of one entry
    # state the same qualifiers.
    return sorted(out, key=lambda e: _entity_order(e["polymer_entity"]))


def _entity_order(entity_id: str) -> tuple:
    return (0, int(entity_id), "") if entity_id.isdigit() else (1, 0, entity_id)


def _uniprot_position(entity: Dict[str, Any], seq_id: int) -> tuple:
    """(accession, UniProt position) of an entity residue, from the RCSB alignment."""
    for acc, regions in sorted(entity["regions"].items()):
        for entity_beg, ref_beg, length in regions:
            if entity_beg <= seq_id < entity_beg + length:
                return acc, ref_beg + (seq_id - entity_beg)
    return None, None


def _ligand_contacts(entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Residues near each ligand instance, per chemical component.

    RCSB states the neighbours of each ligand instance per polymer chain, in structure
    numbering. Each residue is mapped to UniProt numbering through the entity alignment,
    and keeps the shortest distance RCSB states for it. Instances are kept apart: two
    copies of a ligand in two chains are not one ligand contacting both.
    """
    by_instance: Dict[tuple, Dict[str, Any]] = {}
    for entity in entities:
        for instance in entity["instances"]:
            chain = (
                instance.get("rcsb_polymer_entity_instance_container_identifiers") or {}
            ).get("auth_asym_id")
            for row in instance.get("rcsb_ligand_neighbors") or []:
                if row.get("seq_id") is None or not row.get("ligand_comp_id"):
                    continue
                key = (row["ligand_comp_id"], row.get("ligand_asym_id"))
                found = by_instance.setdefault(
                    key,
                    {
                        "asym_id": key[1],
                        "is_bound": row.get("ligand_is_bound"),
                        "contacts": {},
                    },
                )
                residue = (chain, row["seq_id"])
                acc, position = _uniprot_position(entity, row["seq_id"])
                previous = found["contacts"].get(residue)
                distance = row.get("distance")
                if previous is None:
                    found["contacts"][residue] = {
                        "chain": chain,
                        "seq_id": row["seq_id"],
                        "residue": row.get("comp_id"),
                        "uniprot": acc,
                        "position": position,
                        "min_distance": quantity_node(distance, LENGTH_UNIT),
                    }
                elif distance is not None and (
                    previous["min_distance"] is None
                    or distance < previous["min_distance"]["value"]
                ):
                    previous["min_distance"] = quantity_node(distance, LENGTH_UNIT)
    out: Dict[str, List[Dict[str, Any]]] = {}
    for (comp_id, _), found in sorted(
        by_instance.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))
    ):
        contacts = sorted(
            found["contacts"].values(), key=lambda c: (str(c["chain"]), c["seq_id"])
        )
        out.setdefault(comp_id, []).append(
            {
                "asym_id": found["asym_id"],
                "is_bound": found["is_bound"],
                "chains": sorted({str(c["chain"]) for c in contacts}),
                "contacts": contacts,
            }
        )
    return out


def _ligand(entity: Dict[str, Any]) -> Dict[str, Any]:
    """A ligand of the entry, with the PDB "subject of investigation" flag.

    The flag says whether the ligand is what the structure was determined to study. It is
    declared by the depositor (provenance ``Author``) or assigned by RCSB for older
    entries (``RCSB``). A ligand not flagged is not declared of interest: it is often an
    additive or an ion, but it is not asserted to be irrelevant. ``None`` means the entry
    states nothing.
    """
    flags, provenance = set(), set()
    for instance in entity.get("nonpolymer_entity_instances") or []:
        for score in instance.get("rcsb_nonpolymer_instance_validation_score") or []:
            if score.get("is_subject_of_investigation") in ("Y", "N"):
                flags.add(score["is_subject_of_investigation"])
            if score.get("is_subject_of_investigation_provenance"):
                provenance.add(score["is_subject_of_investigation_provenance"])
    return {
        "comp_id": (
            entity.get("rcsb_nonpolymer_entity_container_identifiers") or {}
        ).get("nonpolymer_comp_id"),
        "description": (entity.get("rcsb_nonpolymer_entity") or {}).get(
            "pdbx_description"
        ),
        "subject_of_investigation": ("Y" in flags) if flags else None,
        "subject_of_investigation_provenance": sorted(provenance) or None,
    }


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
    entities = _entities(entry)
    contacts = _ligand_contacts(entities)
    ligands = sorted(
        (_ligand(n) for n in entry.get("nonpolymer_entities") or []),
        key=lambda lig: (lig["comp_id"] or "", lig["description"] or ""),
    )
    for ligand in ligands:
        ligand["instances"] = contacts.get(ligand["comp_id"], [])
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
            "nonpolymer_entities": ligands,
        }
        assertion = make_source_assertion(
            "relationships.has_structure", stated, "RCSB PDB", pdb_id, retrieved_at
        )
        source_assertions.append(assertion)
        qualifiers: Dict[str, Any] = {
            "method": normalize_methods(methods),
            "resolution": quantity_node(resolutions[0], LENGTH_UNIT)
            if resolutions
            else None,
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
