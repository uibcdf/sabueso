"""Frozen experimental coordinate admission over original retained inputs (#170).

Source-declared correspondences are checked, never inferred or aligned. This is
a new view computation, not reconstruction of an unrecorded mapping invocation.
"""

from copy import deepcopy
from math import isfinite

from ._card_ligand_site_scope_v1 import equal, reference
from .card_exploration_structure_v1 import _v1_coverage, _v1_merge_ranges
from .experimental_structure_admission_v1 import decision

RULE = "experimental_structure_coordinates@1"
INVENTORY_RULE = "structure_inventory@3"
STATE_RULE = "structure_state@3"
FIELDS = (
    "ranges",
    "polymer_entities",
    "chimeric_with",
    "mutations",
    "sequence_differences",
    "observed",
    "author_numbering",
    "secondary_structure",
)
POSITION_FIELDS = FIELDS
AXIS_FIELDS = (*FIELDS, "chains", "coverage")


def _integer(value):
    return type(value) is int and value > 0


def _region(region, canonical):
    """Validate requested positions before calling any historical arithmetic."""
    from .errors import ArgumentError

    if region is None:
        return None
    if not isinstance(region, (list, tuple, set)) or not region:
        raise ArgumentError("region requires positive positions or inclusive ranges.")
    positions = set()
    length = canonical["length"] if canonical["status"] == "comparable" else None
    for item in region:
        if _integer(item):
            begin = end = item
        elif (
            isinstance(item, (list, tuple))
            and len(item) == 2
            and all(_integer(p) for p in item)
            and item[0] <= item[1]
        ):
            begin, end = item
        else:
            raise ArgumentError(
                "region requires positive positions or inclusive ranges."
            )
        if length is not None and end > length:
            raise ArgumentError(
                "region extends outside the original source-backed canonical reference."
            )
        positions.update(range(begin, end + 1))
    return sorted(positions)


def _validate(entities, accession, length):
    """Reject ambiguous/broken original axes before bounded projection arithmetic."""
    if not isinstance(entities, list) or not entities:
        return "original_polymer_inputs_unavailable"
    selected, identities, chains = [], set(), set()
    for entity in entities:
        if not isinstance(entity, dict):
            return "original_polymer_shape_invalid"
        aligns = entity.get("rcsb_polymer_entity_align")
        if aligns is None:
            continue
        if not isinstance(aligns, list) or any(not isinstance(a, dict) for a in aligns):
            return "original_alignment_shape_invalid"
        mine = [
            a
            for a in aligns
            if a.get("reference_database_name") == "UniProt"
            and a.get("reference_database_accession") == accession
        ]
        if not mine:
            continue
        selected.append(entity)
        ids, poly = (
            entity.get("rcsb_polymer_entity_container_identifiers"),
            entity.get("entity_poly"),
        )
        if not isinstance(ids, dict) or not isinstance(poly, dict):
            return "original_entity_identity_or_sequence_unavailable"
        labels = ids.get("uniprot_ids")
        if labels is not None and (
            not isinstance(labels, list) or any(not isinstance(x, str) for x in labels)
        ):
            return "original_entity_identity_ambiguous"
        key = ids.get("entity_id")
        if not isinstance(key, str) or not key or key in identities:
            return "original_entity_identity_ambiguous"
        identities.add(key)
        sequence, size = (
            poly.get("pdbx_seq_one_letter_code_can"),
            poly.get("rcsb_sample_sequence_length"),
        )
        if not isinstance(sequence, str) or not _integer(size) or len(sequence) != size:
            return "original_entity_sequence_unavailable"
        forward, reverse = {}, {}
        for alignment in aligns:
            if alignment.get("reference_database_name") != "UniProt":
                continue
            target = alignment.get("reference_database_accession")
            if not isinstance(target, str) or not target:
                return "original_alignment_identity_unavailable"
            spans = alignment.get("aligned_regions")
            if not isinstance(spans, list) or not spans:
                return "original_alignment_unavailable"
            for span in spans:
                if not isinstance(span, dict):
                    return "original_alignment_shape_invalid"
                start, ref, count = (
                    span.get(k)
                    for k in ("entity_beg_seq_id", "ref_beg_seq_id", "length")
                )
                if (
                    not all(_integer(n) for n in (start, ref, count))
                    or start + count - 1 > size
                    or (alignment in mine and ref + count - 1 > length)
                ):
                    return "original_alignment_bounds_invalid"
                if alignment not in mine:
                    continue
                for offset in range(count):
                    a, b = start + offset, ref + offset
                    if (
                        a in forward
                        and forward[a] != b
                        or b in reverse
                        and reverse[b] != a
                    ):
                        return "original_alignment_ambiguous"
                    forward[a], reverse[b] = b, a
        entity_features = entity.get("rcsb_polymer_entity_feature")
        instances = entity.get("polymer_entity_instances")
        author_chains = ids.get("auth_asym_ids")
        if (
            not isinstance(entity_features, list)
            or not isinstance(instances, list)
            or not instances
            or not isinstance(author_chains, list)
            or not author_chains
            or any(not isinstance(c, str) or not c for c in author_chains)
            or len(set(author_chains)) != len(author_chains)
        ):
            return "original_feature_or_instance_scope_unavailable"
        features = list(entity_features)
        seen, instance_chains = set(), set()
        for instance in instances:
            if not isinstance(instance, dict):
                return "original_instance_shape_invalid"
            scope = instance.get("rcsb_polymer_entity_instance_container_identifiers")
            if not isinstance(scope, dict):
                return "original_instance_identity_unavailable"
            chain, asym = scope.get("auth_asym_id"), scope.get("asym_id")
            if (
                not isinstance(chain, str)
                or not chain
                or chain not in author_chains
                or not isinstance(asym, str)
                or not asym
            ):
                return "original_instance_identity_unavailable"
            if scope.get("entity_id", key) != key or chain in chains or asym in seen:
                return "original_instance_identity_ambiguous"
            chains.add(chain)
            seen.add(asym)
            instance_chains.add(chain)
            mapping = scope.get("auth_to_entity_poly_seq_mapping")
            if mapping is not None and (
                not isinstance(mapping, list)
                or len(mapping) != size
                or any(
                    type(label) not in (int, str)
                    or isinstance(label, str)
                    and not label.strip()
                    for label in mapping
                )
            ):
                return "original_author_numbering_invalid"
            held = instance.get("rcsb_polymer_instance_feature")
            if not isinstance(held, list):
                return "original_observation_scope_unavailable"
            features.extend(held)
        if instance_chains != set(author_chains):
            return "original_instance_scope_incomplete"
        for feature in features:
            if not isinstance(feature, dict):
                return "original_feature_shape_invalid"
            if not isinstance(feature.get("type"), str):
                return "original_feature_shape_invalid"
            if feature.get("name") is not None and not isinstance(feature["name"], str):
                return "original_feature_shape_invalid"
            if feature.get("type") not in {
                "artifact",
                "mutation",
                "UNOBSERVED_RESIDUE_XYZ",
                "HELIX_P",
                "SHEET",
                "UNASSIGNED_SEC_STRUCT",
            }:
                continue
            provenance = feature.get("provenance_source")
            if provenance is not None and not isinstance(provenance, str):
                return "original_feature_shape_invalid"
            positions = feature.get("feature_positions", [])
            if not isinstance(positions, list):
                return "original_feature_positions_invalid"
            for span in positions:
                if not isinstance(span, dict):
                    return "original_feature_positions_invalid"
                begin, end = (
                    span.get("beg_seq_id"),
                    span.get("end_seq_id", span.get("beg_seq_id")),
                )
                if end is None:
                    end = begin
                if (
                    not _integer(begin)
                    or not _integer(end)
                    or not 1 <= begin <= end <= size
                ):
                    return "original_feature_positions_invalid"
    return None if selected else "original_focal_alignment_unavailable"


def _projection(raw, accession, sequence, length):
    from .experimental_projection_v1 import (
        _author_numbering,
        _construct,
        _entities,
        _secondary_structure,
    )

    selected = [
        {
            key: value
            for key, value in entity.items()
            if key
            in {
                "rcsb_polymer_entity_container_identifiers",
                "entity_poly",
                "rcsb_polymer_entity_align",
                "rcsb_polymer_entity_feature",
                "polymer_entity_instances",
            }
        }
        for entity in raw
        if any(
            a.get("reference_database_name") == "UniProt"
            and a.get("reference_database_accession") == accession
            for a in entity.get("rcsb_polymer_entity_align") or []
        )
    ]
    entities = _entities({"polymer_entities": selected})
    mine = [e for e in entities if accession in e["uniprot"]]
    ranges = _v1_merge_ranges([r for e in mine for r in e["ranges"].get(accession, [])])
    return {
        "ranges": ranges,
        "coverage": _v1_coverage(ranges, length),
        "chains": sorted({chain for entity in mine for chain in entity["chains"]}),
        "polymer_entities": [e["polymer_entity"] for e in mine],
        "chimeric_with": sorted({a for e in mine for a in e["uniprot"]} - {accession}),
        **{
            k: v
            for k, v in _construct(mine, accession, sequence).items()
            if k != "construct"
        },
        "author_numbering": _author_numbering(mine, accession),
        "secondary_structure": _secondary_structure(mine, accession),
    }


def scope(card, relationship, canonical=None):
    canonical = reference(card) if canonical is None else canonical
    result = {
        "rule": RULE,
        "status": "not_computed",
        "reason": None,
        "basis": "original_source_declared_axis_and_exact_retained_reference",
        "relationship_id": relationship["id"],
        "reference": deepcopy(canonical),
        "source_assertion_ids": deepcopy(relationship.get("source_assertion_ids")),
        "projection_source_assertion_ids": [],
        "structure_reference_revision": "not_stated",
        "revision_note": "Source-declared accession axis; equal source/reference revisions are not inferred.",
    }

    def stop(reason):
        return {**result, "reason": reason}

    if canonical["status"] != "comparable":
        return stop(canonical["reason"])
    if decision(card, relationship)["status"] != "admitted":
        return stop("declaration_not_admitted")
    refs = relationship.get("source_assertion_ids")
    if (
        not isinstance(refs, list)
        or not refs
        or any(not isinstance(r, str) for r in refs)
    ):
        return stop("structure_source_support_unavailable")
    q = relationship.get("qualifiers")
    if not isinstance(q, dict):
        return stop("recorded_qualifiers_unavailable")
    conflicts = relationship.get("qualifier_conflicts")
    if conflicts is not None and (
        not isinstance(conflicts, dict) or any(k in conflicts for k in AXIS_FIELDS)
    ):
        return stop("conflicting_coordinate_qualifiers")
    projections = []
    for key in dict.fromkeys(refs):
        source = card.source_assertion_store.get(key)
        if not isinstance(source, dict):
            return stop("structure_source_support_unavailable")
        provider, value = source.get("source"), source.get("asserted_value")
        if not isinstance(provider, dict) or not isinstance(value, dict):
            return stop("structure_source_shape_invalid")
        if source.get("field_path") != "relationships.has_structure":
            return stop("structure_source_scope_incompatible")
        if provider.get("name") == "UniProt":
            if (
                source.get("subject_ref") != canonical["sequence_ref"]
                or value.get("object_ref") != relationship["object_ref"]
            ):
                return stop("structure_source_scope_incompatible")
            continue
        if provider.get("name") != "RCSB PDB":
            continue
        if (
            source.get("subject_ref") != relationship["object_ref"]
            or "pdb:" + str(provider.get("record_id")) != relationship["object_ref"]
            or value.get("subject_ref") != canonical["sequence_ref"]
            or value.get("object_ref") != relationship["object_ref"]
        ):
            return stop("structure_source_scope_incompatible")
        if "normalized_value" in source and not equal(
            source["normalized_value"], value
        ):
            return stop("native_structure_source_differs")
        raw = (
            (value.get("ligand_contact_inputs") or {}).get("polymer_entities")
            if isinstance(value.get("ligand_contact_inputs"), dict)
            else None
        )
        accession = canonical["sequence_ref"].split(":", 1)[1]
        problem = _validate(raw, accession, canonical["length"])
        if problem:
            return stop(problem)
        projected = _projection(
            raw, accession, card.get("sequence.primary")["value"], canonical["length"]
        )
        if any(not equal(q.get(field), projected.get(field)) for field in AXIS_FIELDS):
            return stop("recorded_coordinate_projection_differs")
        result["projection_source_assertion_ids"].append(key)
        projections.append(projected)
    if not projections:
        return stop("original_polymer_inputs_unavailable")
    if any(not equal(p, projections[0]) for p in projections[1:]):
        return stop("conflicting_original_coordinate_projections")
    return {**result, "status": "comparable"}


class _CoordinateCard:
    def __init__(self, card, region=None):
        self._card = card
        self.canonical = reference(card)
        self.region = _region(region, self.canonical)
        self.scopes = {}
        self.rows = []
        for rel in card.relationships("has_structure"):
            if decision(card, rel)["status"] != "admitted":
                self.rows.append(rel)
                continue
            bound = scope(card, rel, self.canonical)
            self.scopes[rel["id"]] = bound
            selected = deepcopy(rel)
            if bound["status"] != "comparable":
                if not isinstance(selected.get("qualifiers"), dict):
                    selected["qualifiers"] = {}
                for key in POSITION_FIELDS:
                    selected["qualifiers"].pop(key, None)
            coverage = selected["qualifiers"].get("coverage")
            if coverage is not None and (
                type(coverage) not in (int, float)
                or not isfinite(coverage)
                or not 0 <= coverage <= 1
            ):
                selected["qualifiers"].pop("coverage", None)
            self.rows.append(selected)

    def __getattr__(self, key):
        return getattr(self._card, key)

    def relationships(self, predicate=None, object_ref=None):
        if predicate not in (None, "has_structure"):
            return self._card.relationships(predicate, object_ref=object_ref)
        rows = (
            self.rows
            if predicate == "has_structure"
            else [
                r
                for r in self._card.relationships()
                if r["predicate"] != "has_structure"
            ]
            + self.rows
        )
        return [r for r in rows if object_ref is None or r["object_ref"] == object_ref]


def derivation(rule):
    return rule(
        RULE,
        inputs=[
            "original canonical SourceAssertions",
            "original RCSB polymer inputs",
            "has_structure",
        ],
        parameters={
            "scope": "source_declared_coordinate_axis",
            "missing_inputs": "not_computed",
        },
    )


def state_derivation(rule, declared):
    original = declared()
    return rule(
        STATE_RULE,
        inputs=original["inputs"] + [RULE],
        parameters={
            **original["parameters"],
            "coordinate_scope": RULE,
            "unknown": "Reference/coordinate inputs unavailable, unsupported or conflicting; original declarations remain inspectable.",
        },
    )


def _maps(cards, options):
    """A caller map names an admitted target axis; it never establishes identity."""
    from .errors import ArgumentError

    maps = options.get("residue_maps")
    if maps is None:
        return None
    if not isinstance(maps, dict):
        raise ArgumentError("residue_maps require explicit per-Card position mappings.")
    if not maps:
        return None
    by_id = {card.id: card for card in cards}
    reference_id = options.get("reference")
    target = by_id.get(reference_id) if isinstance(reference_id, str) else None
    if target is None or target.canonical["status"] != "comparable":
        raise ArgumentError(
            "residue_maps require an original source-backed reference Card in the deck."
        )
    for card_id, mapping in maps.items():
        source = by_id.get(card_id)
        if source is None or not isinstance(mapping, dict):
            raise ArgumentError(
                "residue_maps require known source Cards and position mappings."
            )
        if any(not _integer(a) or not _integer(b) for a, b in mapping.items()):
            raise ArgumentError("residue_maps require positive integer positions.")
        if len(set(mapping.values())) != len(mapping):
            raise ArgumentError(
                "residue_maps cannot map distinct source positions to one reference position."
            )
        if any(b > target.canonical["length"] for b in mapping.values()) or (
            source.canonical["status"] == "comparable"
            and any(a > source.canonical["length"] for a in mapping)
        ):
            raise ArgumentError(
                "residue_maps extend outside an original source-backed reference."
            )
        if card_id == target.id and any(a != b for a, b in mapping.items()):
            raise ArgumentError(
                "The reference Card uses its own numbering; a nonidentity self-map is incompatible."
            )
    return target.pinned_ref()


def view(card, *, summarize, rule, state, **options):
    scoped = _CoordinateCard(card, options.get("region"))
    options["region"] = scoped.region
    result = summarize(scoped, **options)
    for row in result["items"]:
        row["coordinate_scope"] = deepcopy(scoped.scopes[row["relationship_id"]])
    return {**result, "coordinate_rule": derivation(rule), "state_rule": state()}


def inventory(cards, *, summarize, rule, state, **options):
    regions = options.get("regions")
    if isinstance(regions, dict) and set(regions) - {card.id for card in cards}:
        from .errors import ArgumentError

        raise ArgumentError("regions must name protein Cards present in the deck.")
    scoped = [
        _CoordinateCard(c, regions.get(c.id) if isinstance(regions, dict) else regions)
        for c in cards
    ]
    if isinstance(regions, dict):
        options["regions"] = {
            key: next((c.region for c in scoped if c.id == key), value)
            for key, value in regions.items()
        }
    elif scoped:
        options["regions"] = scoped[0].region
    mapped_reference = _maps(scoped, options)
    result = summarize(scoped, **options)
    scopes = {c.id: c.scopes for c in scoped}
    for row in result["items"]:
        bound = deepcopy(scopes[row["card_id"]][row["relationship_id"]])
        row["coordinate_scope"] = bound
        if bound["status"] != "comparable":
            row["substitutions_in_reference"] = None
            existing = result["not_inventoried"].setdefault(row["card_id"], [])
            acquisition = {
                record["reason"]
                for record in existing
                if record["structure_ref"] == row["structure_ref"]
                and "relationship_id" not in record
                and record["reason"]
                in {"not_requested", "not_found", "error", "partial"}
            }
            existing[:] = [
                r
                for r in existing
                if r["structure_ref"] != row["structure_ref"] or "relationship_id" in r
            ]
            existing.append(
                {
                    "structure_ref": row["structure_ref"],
                    "relationship_id": row["relationship_id"],
                    "reason": next(iter(acquisition))
                    if len(acquisition) == 1
                    else bound["reason"],
                    "coordinate_reason": bound["reason"],
                }
            )
    old = result["rule"]
    result["rule"] = rule(
        INVENTORY_RULE,
        inputs=old["inputs"],
        parameters={
            **old["parameters"],
            "state_rule": STATE_RULE,
            "coordinate_rule": RULE,
            "residue_maps": deepcopy(options.get("residue_maps")),
            "reference_card_ref": mapped_reference,
            "map_basis": "caller_supplied_explicit_correspondence_not_identity_assertion",
        },
    )
    result["coordinate_rule"] = derivation(rule)
    return result
