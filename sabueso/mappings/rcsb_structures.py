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
        features = pe.get("rcsb_polymer_entity_feature")
        hosts = pe.get("rcsb_entity_host_organism")
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
                "length": (pe.get("entity_poly") or {}).get(
                    "rcsb_sample_sequence_length"
                ),
                "sequence": (pe.get("entity_poly") or {}).get(
                    "pdbx_seq_one_letter_code_can"
                ),
                # None when the entry was fetched without them (before schema 0.3.4).
                "features": None
                if features is None and "rcsb_polymer_entity_feature" not in pe
                else features or [],
                "hosts": None
                if "rcsb_entity_host_organism" not in pe
                else [
                    {"name": name, "taxon_id": taxon}
                    for name, taxon in sorted(
                        {
                            (h.get("ncbi_scientific_name"), h.get("ncbi_taxonomy_id"))
                            for h in hosts or []
                            if h.get("ncbi_scientific_name")
                            or h.get("ncbi_taxonomy_id")
                        },
                        key=lambda h: (str(h[0]), str(h[1])),
                    )
                ],
            }
        )
    # RCSB returns entities in no fixed order: sort, so that two retrievals of one entry
    # state the same qualifiers.
    return sorted(out, key=lambda e: _entity_order(e["polymer_entity"]))


def _entity_order(entity_id: str) -> tuple:
    return (0, int(entity_id), "") if entity_id.isdigit() else (1, 0, entity_id)


def _uniprot_position(
    entity: Dict[str, Any], seq_id: int, accession: str | None = None
) -> tuple:
    """(accession, UniProt position) of an entity residue, from the RCSB alignment;
    only for ``accession`` when given."""
    for acc, regions in sorted(entity["regions"].items()):
        if accession is not None and acc != accession:
            continue
        for entity_beg, ref_beg, length in regions:
            if entity_beg <= seq_id < entity_beg + length:
                return acc, ref_beg + (seq_id - entity_beg)
    return None, None


def _feature_seq_ids(feature: Dict[str, Any]) -> List[int]:
    out: List[int] = []
    for pos in feature.get("feature_positions") or []:
        beg = pos.get("beg_seq_id")
        if beg is None:
            continue
        end = pos.get("end_seq_id") or beg
        out.extend(range(int(beg), int(end) + 1))
    return out


def _residue(sequence: str | None, position: int | None) -> str | None:
    if not sequence or position is None or not 0 < position <= len(sequence):
        return None
    return sequence[position - 1]


def _construct(
    entities: List[Dict[str, Any]], acc: str, reference: str | None
) -> Dict[str, Any]:
    """What was crystallised (or measured) for protein ``acc``, as RCSB states it.

    - ``construct``: per polymer entity, its sample length, expression host and the
      segments RCSB marks as artifacts (expression tags, linkers), in entity numbering.
    - ``mutations``: the residues RCSB marks as mutations (``engineered mutation``,
      ``modified residue``...), with the residue in the structure and, through the
      entity alignment, the UniProt position and the reference residue there.
    - ``sequence_differences``: every aligned residue of the entity that differs from
      the reference sequence, stated or not as a mutation (``None`` without a reference
      sequence or an entity sequence).
    - ``observed``: per chain, the UniProt ranges with coordinates, i.e. the aligned
      ranges minus RCSB's unobserved residues. ``None`` when the entry was fetched
      without instance features.
    """
    construct, mutations = [], []
    differences: List[Dict[str, Any]] | None = [] if reference else None
    observed: Dict[str, List[List[int]]] | None = {}
    for entity in entities:
        if acc not in entity["uniprot"]:
            continue
        features = entity["features"]
        tags = []
        for f in features or []:
            if f.get("type") == "artifact":
                seq_ids = _feature_seq_ids(f)
                if seq_ids:
                    tags.append(
                        {
                            "name": f.get("name"),
                            "seq_ids": merge_ranges([[i, i] for i in seq_ids]),
                        }
                    )
            elif f.get("type") == "mutation":
                for seq_id in _feature_seq_ids(f):
                    found, position = _uniprot_position(entity, seq_id, acc)
                    mutations.append(
                        {
                            "polymer_entity": entity["polymer_entity"],
                            "seq_id": seq_id,
                            "position": position if found else None,
                            "residue": _residue(entity["sequence"], seq_id),
                            "reference": _residue(reference, position)
                            if found
                            else None,
                            "name": f.get("name"),
                        }
                    )
        construct.append(
            {
                "polymer_entity": entity["polymer_entity"],
                "length": entity["length"],
                "expression_host": entity["hosts"],
                "tags": None
                if features is None
                else sorted(tags, key=lambda t: t["seq_ids"]),
            }
        )
        if differences is not None and entity["sequence"]:
            for entity_beg, ref_beg, length in entity["regions"].get(acc, []):
                for k in range(length):
                    mine = _residue(entity["sequence"], entity_beg + k)
                    theirs = _residue(reference, ref_beg + k)
                    if mine and theirs and mine != theirs:
                        differences.append(
                            {
                                "polymer_entity": entity["polymer_entity"],
                                "seq_id": entity_beg + k,
                                "position": ref_beg + k,
                                "reference": theirs,
                                "residue": mine,
                            }
                        )
        elif differences is not None:
            differences = None
        for instance in entity["instances"]:
            if observed is None or "rcsb_polymer_instance_feature" not in instance:
                observed = None
                continue
            chain = (
                instance.get("rcsb_polymer_entity_instance_container_identifiers") or {}
            ).get("auth_asym_id")
            missing = {
                i
                for f in instance.get("rcsb_polymer_instance_feature") or []
                if f.get("type") == "UNOBSERVED_RESIDUE_XYZ"
                for i in _feature_seq_ids(f)
            }
            positions = [
                ref_beg + k
                for entity_beg, ref_beg, length in entity["regions"].get(acc, [])
                for k in range(length)
                if entity_beg + k not in missing
            ]
            observed[str(chain)] = merge_ranges([[p, p] for p in positions])
    key = lambda m: (_entity_order(m["polymer_entity"]), m["seq_id"])  # noqa: E731
    return {
        "construct": construct,
        "mutations": sorted(mutations, key=key),
        "sequence_differences": None
        if differences is None
        else sorted(differences, key=key),
        "observed": observed if observed else None,
    }


def _refinement(entry: Dict[str, Any]) -> List[Dict[str, Any]] | None:
    """R-free and R-work per refinement, as RCSB states them; None when not stated."""
    if not entry.get("refine"):
        return None
    return [
        {
            "method": normalize_methods([r.get("pdbx_refine_id") or ""]),
            "r_free": r.get("ls_R_factor_R_free"),
            "r_work": r.get("ls_R_factor_R_work"),
        }
        for r in entry["refine"]
    ]


def _date(value: str | None) -> str | None:
    return value[:10] if value else None


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


def _assemblies(entry: Dict[str, Any]) -> List[Dict[str, Any]] | None:
    """The entry's biological assemblies as RCSB states them, or None when the entry
    carries no assembly data (never an empty list standing for "unknown").

    ``defined_by`` says who defined the assembly (author, software or both) and
    ``method`` the software (e.g. PISA). ``oligomeric_state`` and ``stoichiometry`` are
    RCSB's symmetry annotation, where stoichiometry letters label polymer entities.
    """
    if "assemblies" not in entry or entry["assemblies"] is None:
        return None
    out = []
    for a in entry["assemblies"]:
        stated = a.get("pdbx_struct_assembly") or {}
        symmetry = [
            s
            for s in a.get("rcsb_struct_symmetry") or []
            if s.get("kind") == "Global Symmetry"
        ]
        out.append(
            {
                "id": (a.get("rcsb_assembly_container_identifiers") or {}).get(
                    "assembly_id"
                ),
                "oligomeric_details": stated.get("oligomeric_details"),
                "oligomeric_count": stated.get("oligomeric_count"),
                "defined_by": stated.get("details"),
                "method": stated.get("method_details"),
                "oligomeric_state": symmetry[0].get("oligomeric_state")
                if symmetry
                else None,
                "stoichiometry": symmetry[0].get("stoichiometry") if symmetry else None,
                "symmetry": symmetry[0].get("type") if symmetry else None,
            }
        )
    return sorted(out, key=lambda a: str(a["id"]).zfill(4))


def map_structure_entities(
    entry: Dict[str, Any],
    retrieved_at: str,
    subjects: Iterable[str] | None = None,
    reference_lengths: Dict[str, int] | None = None,
    reference_sequences: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """Map an RCSB entry (GraphQL ``entry``) to has_structure relationships.

    ``subjects`` restricts the output to these UniProt accessions (e.g. the card's
    entity); ``reference_lengths`` gives canonical lengths used to compute coverage, and
    ``reference_sequences`` canonical sequences used to state the reference residue of
    each mutation and the sequence differences.
    """
    pdb_id = entry["rcsb_id"]
    structure_ref = f"pdb:{pdb_id}"
    methods = [m.get("method") for m in entry.get("exptl") or []]
    resolutions = (entry.get("rcsb_entry_info") or {}).get("resolution_combined") or []
    assemblies = _assemblies(entry)
    citation = entry.get("rcsb_primary_citation")
    primary_citation = (
        {
            "pubmed": str(citation["pdbx_database_id_PubMed"])
            if citation.get("pdbx_database_id_PubMed")
            else None,
            "doi": citation.get("pdbx_database_id_DOI"),
            "title": citation.get("title"),
            "journal": citation.get("journal_abbrev"),
            "year": citation.get("year"),
        }
        if citation
        else None
    )
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
    sequences = reference_sequences or {}
    accession = entry.get("rcsb_accession_info")
    refinement = _refinement(entry)

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
                | {
                    k: e[k]
                    for k in ("length", "sequence", "features", "hosts")
                    if e[k] is not None
                }
                for e in mine
            ],
            "unobserved_residues": {
                str(
                    (
                        i.get("rcsb_polymer_entity_instance_container_identifiers")
                        or {}
                    ).get("auth_asym_id")
                ): [
                    f.get("feature_positions")
                    for f in i.get("rcsb_polymer_instance_feature") or []
                    if f.get("type") == "UNOBSERVED_RESIDUE_XYZ"
                ]
                for e in mine
                for i in e["instances"]
                if "rcsb_polymer_instance_feature" in i
            }
            or None,
            "refine": entry.get("refine"),
            "accession_info": accession,
            "nonpolymer_entities": ligands,
            "assemblies": assemblies,
            "primary_citation": primary_citation,
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
            # Other proteins the same polymer entities also map to: a chimera or fusion
            # (e.g. 3Q37, a TcTIM/TbTIM chimera). Empty for an ordinary entity.
            "chimeric_with": sorted({a for e in mine for a in e["uniprot"]} - {acc}),
            "other_entities": others,
            "ligands": ligands,
            "assemblies": assemblies,
            "primary_citation": primary_citation,
            "refinement": refinement,
            "deposited": _date((accession or {}).get("deposit_date")),
            "released": _date((accession or {}).get("initial_release_date")),
        }
        if any(e["features"] is not None for e in mine):
            qualifiers.update(_construct(mine, acc, sequences.get(acc)))
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
