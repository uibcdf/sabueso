"""Frozen source-declared experimental projection primitives (#170).

Original mapping arithmetic, now used by a named retained-input view. These
functions neither create SourceAssertions nor call current mapping engines.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .card_exploration_structure_v1 import _v1_merge_ranges as merge_ranges

SECONDARY_FEATURES = {"HELIX_P": "helix", "SHEET": "strand"}


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


def _author_numbering(
    entities: List[Dict[str, Any]], acc: str
) -> Dict[str, List[list]] | None:
    """Per chain, the author residue numbers of the UniProt positions (#73).

    RCSB states each instance's author numbering (``auth_to_entity_poly_seq_mapping``,
    one author id per entity residue); the entity alignment places entity residues in
    UniProt numbering. Stored compactly as ``[uniprot_begin, uniprot_end, author_begin]``
    segments where both run on together; an author id with an insertion code (``"52A"``)
    is its own segment, ``[position, position, "52A"]``. None when RCSB did not state
    the author numbering.
    """
    out: Dict[str, List[list]] = {}
    for entity in entities:
        if acc not in entity["uniprot"]:
            continue
        for instance in entity["instances"]:
            ids = (
                instance.get("rcsb_polymer_entity_instance_container_identifiers") or {}
            )
            mapping = ids.get("auth_to_entity_poly_seq_mapping")
            if not mapping:
                continue
            segments: List[list] = []
            for entity_beg, ref_beg, length in entity["regions"].get(acc, []):
                for k in range(length):
                    index = entity_beg + k - 1
                    if not 0 <= index < len(mapping):
                        continue
                    author, position = str(mapping[index]), ref_beg + k
                    number = int(author) if author.lstrip("-").isdigit() else None
                    last = segments[-1] if segments else None
                    if (
                        number is not None
                        and last is not None
                        and isinstance(last[2], int)
                        and position == last[1] + 1
                        and number == last[2] + (last[1] - last[0]) + 1
                    ):
                        last[1] = position
                    else:
                        segments.append(
                            [
                                position,
                                position,
                                number if number is not None else author,
                            ]
                        )
            out[str(ids.get("auth_asym_id"))] = segments
    return out or None


def _secondary_structure(
    entities: List[Dict[str, Any]], acc: str
) -> Dict[str, Dict[str, Any]] | None:
    """Per chain, the helices and strands the entry assigns, in UniProt numbering (#80).

    RCSB states them as instance features (``HELIX_P``, ``SHEET``), in entity numbering,
    with the program that assigned them (``provenance_source``, e.g. PROMOTIF or DSSP).
    Each segment is placed in UniProt numbering through the entity alignment, and split
    where the alignment has a gap. Sheets are not kept, only their strands. A chain is
    listed only when the entry assigns
    secondary structure to it (``UNASSIGNED_SEC_STRUCT`` counts as an assignment): a
    chain without any is not stated, never coil.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for entity in entities:
        if acc not in entity["uniprot"]:
            continue
        for instance in entity["instances"]:
            features = [
                f
                for f in instance.get("rcsb_polymer_instance_feature") or []
                if f.get("type") in (*SECONDARY_FEATURES, "UNASSIGNED_SEC_STRUCT")
            ]
            if not features:
                continue
            chain = str(
                (
                    instance.get("rcsb_polymer_entity_instance_container_identifiers")
                    or {}
                ).get("auth_asym_id")
            )
            item: Dict[str, Any] = {
                "assigned_by": sorted(
                    {
                        f["provenance_source"]
                        for f in features
                        if f.get("provenance_source")
                    }
                ),
                **{element: [] for element in SECONDARY_FEATURES.values()},
            }
            for f in features:
                element = SECONDARY_FEATURES.get(f["type"])
                if element is None:
                    continue
                for pos in f.get("feature_positions") or []:
                    beg = pos.get("beg_seq_id")
                    if beg is None:
                        continue
                    end = pos.get("end_seq_id") or beg
                    positions = [
                        p
                        for i in range(int(beg), int(end) + 1)
                        for a, p in [_uniprot_position(entity, i, acc)]
                        if a is not None
                    ]
                    item[element].extend(merge_ranges([[p, p] for p in positions]))
            # A strand shared by two sheets (the closing strand of a barrel) is stated
            # twice; it is one segment. Adjacent segments stay apart, as stated.
            for element in SECONDARY_FEATURES.values():
                item[element] = sorted({tuple(r) for r in item[element]})
                item[element] = [list(r) for r in item[element]]
            out[chain] = item
    return out or None
