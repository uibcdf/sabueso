# Frozen original B4 predicates from 2eb6114 / SDK200.
# Private consistency expectations only; preserve these meanings.
"""Opt-in declared-copy families and uncertain measurement correspondence (#186).

Original measurement_identity@1 remains in measurements.py. Numeric/publication
coincidence is a candidate, never an identity edge or an independence claim here.
"""

import hashlib
import math
from collections import defaultdict
from copy import deepcopy
from itertools import combinations

from ..errors import ArgumentError, SchemaError
from .measurements import _blocks, _molecules, _publications, half_unit, record_source
from .rules import make_derivation

RULE = "measurement_identity@2"
LEGACY_RULE = "measurement_identity@1"
COUNT_SCOPE = (
    "Retained groups under the selected policy; not a count of independent experiments. "
    "Possible correspondence and unresolved copies remain explicit."
)


def validate_measurement_rule(value):
    if isinstance(value, str) and value in (LEGACY_RULE, RULE):
        return value
    raise ArgumentError(
        'measurement_rule requires "measurement_identity@1" or "measurement_identity@2".',
        argument="measurement_rule",
    )


def _mapping(value, field, rid):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise SchemaError(
            f"Cannot interpret measurement correspondence: {field} of {rid} must be a mapping. "
            "Inspect the original has_bioactivity relationship and its source assertions."
        )
    return value


def _numeric(measurement):
    """Only well-defined exact scalars enter the numerical candidate comparison."""
    from .bioactivities import is_range
    from .quantities import normalized_measurement

    if (
        measurement.get("relation") != "="
        or is_range(measurement)
        or any(
            measurement.get(k) is not None
            for k in ("uncertainty", "normalized_uncertainty")
        )
    ):
        return None
    value, units = measurement.get("value"), measurement.get("units")
    if type(value) not in (int, float) or value <= 0:
        return None
    try:
        if not math.isfinite(value):
            return None
    except OverflowError:
        return None
    if not isinstance(units, str):
        return None
    node = normalized_measurement(value, units)
    if node is None or not math.isfinite(node["value"]) or node["value"] <= 0:
        return None
    try:
        precision = half_unit(measurement)
    except (TypeError, ValueError, OverflowError):
        return None
    if precision is None or not math.isfinite(precision):
        return None
    return {"value": node["value"], "unit": node["unit"], "half_last_digit": precision}


def _agreement(a, b):
    if a is None or b is None or a["unit"] != b["unit"]:
        return False
    return (
        abs(a["value"] - b["value"])
        <= max(a["half_last_digit"], b["half_last_digit"]) + 1e-9
    )


def _context(left, right):
    fields = ("description", "organism", "tax_id", "variant_mutation")
    rows = []
    for name in fields:
        a, b = left["context"].get(name), right["context"].get(name)
        missing_a, missing_b = a in (None, ""), b in (None, "")
        rows.append(
            {
                "field": "assay." + name,
                "left": a,
                "right": b,
                "state": "missing_on_both"
                if missing_a and missing_b
                else "missing_on_one"
                if missing_a or missing_b
                else "literal_equal"
                if a == b
                else "different_retained_values",
            }
        )
    return rows


def measurement_groups(card, *, measurement_rule=LEGACY_RULE, _support=None):
    selected = validate_measurement_rule(measurement_rule)
    if selected == LEGACY_RULE:
        from .measurements import measurement_groups as original

        return original(card, _support=_support)
    return _groups(card, _support=_support)


def _groups(card, *, _support=None):
    rels = card.relationships("has_bioactivity")
    info = {}
    support_ids = {}
    for rel in rels:
        rid = rel["id"]
        for name in ("subject_ref", "object_ref"):
            if not isinstance(rel.get(name), str) or not rel[name]:
                raise SchemaError(
                    f"Cannot interpret measurement correspondence: {name} of {rid} must be a nonempty string."
                )
        q = _mapping(rel.get("qualifiers"), "qualifiers", rid)
        m = _mapping(q.get("measurement"), "measurement", rid)
        assay = _mapping(q.get("assay"), "assay", rid)
        _mapping(q.get("document"), "document", rid)
        copy = _mapping(q.get("copy_of"), "copy_of", rid)
        if q.get("source") is not None and (
            not isinstance(q["source"], str) or not q["source"]
        ):
            raise SchemaError(
                f"Cannot interpret measurement correspondence: source of {rid} must be a nonempty string."
            )
        source = record_source(q)
        if not isinstance(source, str) or not source:
            raise SchemaError(
                f"Cannot interpret measurement correspondence: source of {rid} must be a nonempty string."
            )
        activity = q.get("activity_id")
        if activity is not None and type(activity) not in (str, int):
            raise SchemaError(
                f"Cannot interpret measurement correspondence: activity_id of {rid} must be a string or integer."
            )
        for name in ("id",):
            if assay.get(name) is not None and not isinstance(assay[name], str):
                raise SchemaError(
                    f"Cannot interpret measurement correspondence: assay.{name} of {rid} must be a string."
                )
        if m.get("type") is not None and not isinstance(m["type"], str):
            raise SchemaError(
                f"Cannot interpret measurement correspondence: measurement.type of {rid} must be a string."
            )
        if copy and (
            not isinstance(copy.get("source"), str)
            or not copy["source"]
            or (
                copy.get("activity_id") is not None
                and type(copy["activity_id"]) not in (str, int)
            )
            or (copy.get("assay") is not None and not isinstance(copy["assay"], str))
        ):
            raise SchemaError(
                f"Cannot interpret measurement correspondence: copy_of of {rid} requires a source and valid original selectors."
            )
        refs = (rel["object_ref"], q.get("molecule_ref"))
        if any(ref is not None and not isinstance(ref, str) for ref in refs):
            raise SchemaError(
                f"Cannot interpret measurement correspondence: molecule references of {rid} must be strings."
            )
        info[rid] = {
            "source": source,
            "publications": _publications(q),
            "molecules": {ref for ref in refs if ref},
            "subject_ref": rel["subject_ref"],
            "type": m.get("type"),
            "relation": m.get("relation"),
            "measurement": m,
            "activity_id": activity,
            "assay": assay.get("id"),
            "copy_of": copy,
            "context": assay,
            "numeric": _numeric(m),
        }
        support_ids[rid] = list(rel.get("source_assertion_ids") or [])

    entities = _molecules(card)
    for row in info.values():
        row["molecules"] = {entities.get(ref, ref) for ref in row["molecules"]}

    by_activity = defaultdict(list)
    for rid, row in info.items():
        if row["activity_id"] is not None:
            by_activity[(row["source"], row["activity_id"])].append(rid)
    edges, selectors, ambiguous, unresolved, review = [], {}, [], [], []
    for rid, row in sorted(info.items()):
        copy = row["copy_of"]
        if not copy:
            continue
        basis = "source_activity_id"
        reason = "original_activity_not_on_card"
        if copy.get("activity_id") is not None:
            found = by_activity.get((copy["source"], copy["activity_id"]), [])
        elif copy.get("assay"):
            named_assay = [
                other
                for other, candidate in info.items()
                if candidate["source"] == copy["source"]
                and candidate["assay"] == copy["assay"]
            ]
            in_assay = [
                other
                for other in named_assay
                if not row["type"]
                or not info[other]["type"]
                or row["type"] == info[other]["type"]
            ]
            reason = (
                "molecule_not_resolved_in_named_assay"
                if in_assay
                else "measurement_type_differs_in_named_assay"
                if named_assay
                else "named_original_assay_not_on_card"
            )
            found = [
                other
                for other in in_assay
                if row["molecules"] & info[other]["molecules"]
            ]
            basis = "named_assay_molecule"
            if not found:
                found = [
                    other
                    for other in in_assay
                    if _blocks(row["molecules"]) & _blocks(info[other]["molecules"])
                ]
                basis = "named_assay_connectivity"
        else:
            found = []
            reason = "original_selector_not_stated"
        found = sorted(found)
        if len(found) == 1:
            other = found[0]
            edges.append((rid, other, "provenance"))
            selectors[(rid, other)] = {"basis": basis, "precision_used": False}
            if basis == "named_assay_connectivity":
                review.append(
                    {
                        "records": sorted([rid, other]),
                        "reason": "stereo_differs",
                        "note": "Declared copy selected by connectivity within its named assay; no molecule identity is inferred.",
                    }
                )
        else:
            if found:
                ambiguous.append(
                    {"record": rid, "source": copy["source"], "candidates": found}
                )
            unresolved.append(
                {
                    "record": rid,
                    "copy_of": copy,
                    "reason": "ambiguous_original" if found else reason,
                }
            )

    # Copy links form a directed graph with at most one selected original per row.
    # A cycle cannot supply a resolved original, including links entering the cycle.
    originals = {a: b for a, b, _ in edges}
    cyclic = set()
    for rid in originals:
        seen, current = set(), rid
        while current in originals:
            if current in seen:
                cyclic.update(seen)
                break
            seen.add(current)
            current = originals[current]
    for rid in sorted(cyclic):
        unresolved.append(
            {"record": rid, "copy_of": info[rid]["copy_of"], "reason": "copy_cycle"}
        )
    edges = [edge for edge in edges if edge[0] not in cyclic]
    selectors = {key: value for key, value in selectors.items() if key[0] not in cyclic}
    parent = {rid: rid for rid in info}

    def find(rid):
        while parent[rid] != rid:
            rid = parent[rid]
        return rid

    for a, b, _ in edges:
        parent[find(a)] = find(b)
    members = defaultdict(list)
    for rid in info:
        members[find(rid)].append(rid)
    groups, group_of = [], {}
    for records in members.values():
        records.sort()
        gid = (
            "MG_" + hashlib.sha256("|".join(records).encode()).hexdigest()[:16]
            if len(records) > 1
            else records[0]
        )
        group_of.update(dict.fromkeys(records, gid))
        if len(records) > 1:
            groups.append(
                {
                    "id": gid,
                    "records": records,
                    "sources": sorted({info[r]["source"] for r in records}),
                    "basis": ["provenance"],
                }
            )
            sources = [info[r]["source"] for r in records]
            if len(set(sources)) != len(sources):
                review.append(
                    {
                        "records": records,
                        "reason": "same_source_copy_family",
                        "note": "Multiple records of one source retain explicit copy links; source count does not establish independence.",
                    }
                )

    # Possible numeric correspondence never contributes an identity edge or vote.
    buckets = defaultdict(set)
    eligible, not_compared = [], []
    for rid, row in info.items():
        reasons = []
        if row["copy_of"]:
            reasons.append("declared_copy_compared_by_its_original_pointer")
        if not row["numeric"]:
            reasons.append("exact_positive_scalar_context_not_available")
        if not row["type"]:
            reasons.append("measurement_type_not_stated")
        if not row["publications"]:
            reasons.append("publication_not_stated")
        if reasons:
            not_compared.append({"record": rid, "reasons": reasons})
            continue
        eligible.append(rid)
        for publication in row["publications"]:
            buckets[(publication, row["subject_ref"], row["type"])].add(rid)
    pairs = set()
    possible = []
    for bucket in buckets.values():
        for a, b in combinations(sorted(bucket), 2):
            if (a, b) in pairs:
                continue
            pairs.add((a, b))
            left, right = info[a], info[b]
            if left["source"] == right["source"]:
                continue
            if not _agreement(left["numeric"], right["numeric"]):
                continue
            if not left["molecules"] & right["molecules"]:
                keys = [
                    {key for key in row["molecules"] if key.startswith("inchikey:")}
                    for row in (left, right)
                ]
                reason = (
                    "molecule_unresolved"
                    if not all(keys)
                    else "stereo_differs"
                    if _blocks(keys[0]) & _blocks(keys[1])
                    else "molecule_differs"
                )
                review.append(
                    {
                        "records": [a, b],
                        "sources": sorted({left["source"], right["source"]}),
                        "reason": reason,
                        "molecules": sorted(left["molecules"] | right["molecules"]),
                        "note": "Numeric/publication coincidence with no shared molecule identity; records are not grouped.",
                    }
                )
                continue
            possible.append(
                {
                    "records": [a, b],
                    "state": "possible_correspondence",
                    "measurement_identity": "not_established",
                    "independence_status": "not_established",
                    "shared_publications": [
                        {"namespace": ns, "id": identifier}
                        for ns, identifier in sorted(
                            left["publications"] & right["publications"]
                        )
                    ],
                    "shared_molecule_keys": sorted(
                        left["molecules"] & right["molecules"]
                    ),
                    "subject_ref": left["subject_ref"],
                    "measurement_type": left["type"],
                    "relation": "=",
                    "precision": {
                        **{
                            side: {
                                "normalized": {
                                    "value": row["numeric"]["value"],
                                    "unit": row["numeric"]["unit"],
                                },
                                "half_last_digit": {
                                    "value": row["numeric"]["half_last_digit"],
                                    "unit": row["numeric"]["unit"],
                                },
                            }
                            for side, row in (("left", left), ("right", right))
                        },
                        "numerical_slack": {
                            "value": 1e-9,
                            "unit": left["numeric"]["unit"],
                        },
                    },
                    "context": _context(left, right),
                    "source_assertion_ids": {r: support_ids[r] for r in (a, b)},
                    "unassessed": [
                        "construct_identity",
                        "isoform_reference",
                        "experimental_protocol",
                        "measurement_locator",
                        "prose_semantics",
                        "experimental_independence",
                    ],
                    "interpretation": "These source records may describe one result; retained context does not establish the same measurement or independent experiments.",
                }
            )
    copy_diagnostics = []
    for a, b, _ in edges:
        left, right = info[a], info[b]
        differences = [
            key
            for key in ("type", "relation", "value", "units", "stated_value")
            if left["measurement"].get(key) != right["measurement"].get(key)
        ]
        copy_diagnostics.append(
            {
                "records": [a, b],
                "selector": selectors[(a, b)],
                "reported_measurement_differences": differences,
                "context": _context(left, right),
                "subject_refs": [left["subject_ref"], right["subject_ref"]],
                "interpretation": "Source-declared copy; all reported differences are retained. Literal differences need not be experimental contradictions.",
            }
        )
    if _support is not None:
        _support.update(info=info, edges=edges, selectors=selectors)
    return deepcopy(
        {
            "rule": make_derivation(
                RULE,
                inputs=["has_bioactivity", "entities"],
                parameters={
                    "identity_edges": "explicit source copy links with a unique original selector; cycles refused",
                    "statement_matches": "exact scalar numerical/publication candidates only; never identity edges",
                    "named_assay_ambiguity": "multiple eligible originals stay ambiguous; numeric similarity does not select one",
                    "copy_missing_type": "missing type does not constrain a declared-copy pointer; a unique named-assay/molecule original is required and no endpoint is filled in",
                    "experimental_independence": "not established by grouping, source count, text or numeric agreement",
                    "assay_context": "literal retained fields; no construct, protocol or prose equivalence inference",
                },
            ),
            "groups": sorted(groups, key=lambda g: g["id"]),
            "group_of": group_of,
            "ambiguous": ambiguous,
            "unresolved_copies": unresolved,
            "review": review,
            "possible_correspondences": sorted(possible, key=lambda p: p["records"]),
            "comparison_scope": {
                "eligible_records": sorted(eligible),
                "not_compared": sorted(not_compared, key=lambda row: row["record"]),
                "bucket_pair_count": len(pairs),
                "basis": "exact scalar records sharing a publication, target and type; candidates additionally require different sources and compatible stated molecule/numeric context",
                "interpretation": "An empty candidate list does not establish absence of duplicate or independent experiments. Complete experimental methods and independence were not assessed.",
            },
            "copy_diagnostics": copy_diagnostics,
            "counting": {
                "scope": "all_retained_has_bioactivity_relationships",
                "record_count": len(info),
                "group_count": len(set(group_of.values())),
                "resolved_copy_links": len(edges),
                "possible_correspondence_count": len(possible),
                "independence_status": "not_established",
                "interpretation": COUNT_SCOPE,
            },
        }
    )
