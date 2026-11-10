"""Explicit typed knowledge comparison over two captured inputs (#59/#148).

The rule compares recorded representations, not physical equivalence, biological
identity, causality or free-text meaning. A caller map is an input assertion of
correspondence, never an alignment computed or scientifically validated here.
"""

from copy import deepcopy

from ..errors import ArgumentError
from ..snapshot import canonical_json
from .rules import make_derivation

RULE = "card_knowledge_diff@2"


def _fields(card):
    return {
        path: deepcopy(card.get(path))
        for path in card.list_fields()
        if isinstance(card.get(path), dict) and "source_assertion_ids" in card.get(path)
    }


def _sequence(card):
    value = (card.get("sequence.primary") or {}).get("value")
    return value if isinstance(value, str) else None


def _axis(card):
    prefix = "sabueso:protein:uniprot:"
    return "UniProt:" + card.id[len(prefix) :] if card.id.startswith(prefix) else None


def _mapping(card, other, mapping):
    if mapping is not None and (
        not isinstance(mapping, dict)
        or any(
            type(k) is not int or type(v) is not int or min(k, v) < 1
            for k, v in mapping.items()
        )
        or len(set(mapping.values())) != len(mapping)
    ):
        raise ArgumentError(
            "card_knowledge_diff@2 requires a one-to-one positive integer residue map or None."
        )
    lengths = [
        None if _sequence(c) is None else len(_sequence(c)) for c in (card, other)
    ]
    if mapping is not None and any(
        lengths[side] is not None and any(p > lengths[side] for p in positions)
        for side, positions in enumerate((mapping.keys(), mapping.values()))
    ):
        raise ArgumentError(
            "A supplied map position exceeds a stated input sequence length."
        )
    return {
        "basis": "not_supplied"
        if mapping is None
        else "caller_supplied_position_pairs",
        "pairs": None
        if mapping is None
        else [[k, mapping[k]] for k in sorted(mapping)],
        "self_axis": _axis(card),
        "other_axis": _axis(other),
        "sequence_lengths": lengths,
        "bounds": "checked_where_sequence_is_stated",
        "alignment_performed": False,
        "identity_inferred": False,
        "scientific_correspondence_validated": False,
    }


def _positions(item, axis, available):
    if not isinstance(item, dict):
        return None, "unrecognized_annotation"
    location = item.get("location")
    sequence = location.get("sequence") if isinstance(location, dict) else None
    if (
        not isinstance(sequence, dict)
        or axis is None
        or sequence.get("sequence_id") != axis
    ):
        return None, "unstated_or_foreign_sequence_axis"
    if sequence.get("indexing") not in (None, "1-based"):
        return None, "unrecognized_coordinate_indexing"
    spans = sequence.get("fragments") if "fragments" in sequence else [sequence]
    if not isinstance(spans, list) or not spans:
        return None, "unplaced_or_unrecognized_positions"
    intervals = []
    for span in spans:
        if not isinstance(span, dict):
            return None, "unplaced_or_unrecognized_positions"
        if any(
            span.get(k) not in (None, "EXACT")
            for k in ("start_modifier", "end_modifier")
        ):
            return None, "uncertain_position_boundaries"
        start = span.get("start")
        end = span.get("end", start)
        if end is None:
            end = start
        if type(start) is not int or type(end) is not int or start < 1 or end < start:
            return None, "unplaced_or_unrecognized_positions"
        intervals.append((start, end))
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = merged[-1][0], max(merged[-1][1], end)
        else:
            merged.append((start, end))
    # Do not expand an arbitrary source interval: a complete map must cover every
    # unique position first, so this allocation is bounded by the supplied map.
    covered = tuple(sorted(p for p in available if any(a <= p <= b for a, b in merged)))
    if len(covered) != sum(b - a + 1 for a, b in merged):
        return None, "incomplete_residue_map"
    return covered, None


def _without_coordinates(item):
    value = deepcopy(item)
    sequence = value["location"]["sequence"]
    for key in ("sequence_id", "start", "end", "fragments"):
        sequence.pop(key, None)
    if not sequence:
        value["location"].pop("sequence")
    if not value["location"]:
        value.pop("location")
    return value


def _items(path, mine, theirs, mapping, axes):
    from .item_identity import ITEM_IDENTITY

    positional = path.startswith("features_positional.")
    if path in ITEM_IDENTITY and ITEM_IDENTITY[path] is None:
        return {"status": "not_compared", "reason": "free text"}
    if positional and mapping is None:
        return {"status": "not_compared", "reason": "no residue mapping"}
    groups = [{}, {}]
    rejected = [[], []]
    for side, items in enumerate((mine, theirs)):
        available = (
            set(mapping if side == 0 else mapping.values()) if positional else set()
        )
        for index, item in enumerate(items):
            probe = deepcopy(item)
            positions = None
            if positional:
                positions, reason = _positions(item, axes[side], available)
                if reason:
                    rejected[side].append(
                        {"index": index, "item": deepcopy(item), "reason": reason}
                    )
                    continue
                if side == 0:
                    probe["location"]["sequence"] = {
                        "sequence_id": axes[1],
                        "fragments": [
                            {"start": mapping[p], "end": mapping[p]} for p in positions
                        ],
                    }
            try:
                identity = ITEM_IDENTITY.get(path)
                key = canonical_json(identity(probe) if identity is not None else probe)
            except (AttributeError, KeyError, TypeError, ValueError):
                rejected[side].append(
                    {
                        "index": index,
                        "item": deepcopy(item),
                        "reason": "unrecognized_item_identity",
                    }
                )
                continue
            groups[side].setdefault(key, []).append(
                {"index": index, "item": deepcopy(item)}
            )
    out = {
        k: []
        for k in (
            "both",
            "differ",
            "only_self",
            "only_other",
            "ambiguous",
            "unresolved_self",
            "unresolved_other",
        )
    }
    for key in sorted(set(groups[0]) | set(groups[1])):
        left, right = groups[0].get(key, []), groups[1].get(key, [])
        if left and right and (len(left) != 1 or len(right) != 1):
            out["ambiguous"].append(
                {
                    "self": left,
                    "other": right,
                    "reason": "multiple_items_share_comparison_identity",
                }
            )
        elif left and right:
            a, b = left[0]["item"], right[0]["item"]
            comparable_a, comparable_b = (
                (_without_coordinates(a), _without_coordinates(b))
                if positional
                else (a, b)
            )
            pair = {"self": left[0], "other": right[0]}
            out[
                "both"
                if canonical_json(comparable_a) == canonical_json(comparable_b)
                else "differ"
            ].append(pair)
        elif left:
            out["unresolved_self" if rejected[1] else "only_self"].extend(left)
        elif rejected[0]:
            out["unresolved_other"].extend(right)
        else:
            out["only_other"].extend(right)
    out["not_comparable_self"], out["not_comparable_other"] = rejected
    out["status"] = (
        "partial"
        if any(
            (
                rejected[0],
                rejected[1],
                out["ambiguous"],
                out["unresolved_self"],
                out["unresolved_other"],
            )
        )
        else "differs"
        if any((out["differ"], out["only_self"], out["only_other"]))
        else "same"
    )
    return out


def _support(card, path, node):
    identifiers = node.get("source_assertion_ids") if isinstance(node, dict) else []
    valid = isinstance(identifiers, list) and all(
        isinstance(i, str) for i in identifiers
    )
    identifiers = identifiers if valid else []
    subject = card.id.split(":", 2)[2] if card.id.startswith("sabueso:") else None
    records, missing, bindings = [], [], []
    from .source import assertion_value

    for identifier in identifiers:
        source = card.source_assertion_store.get(identifier)
        if source is None:
            missing.append(identifier)
            continue
        records.append(deepcopy(source))
        value = assertion_value(source)
        selected = node.get("value")
        value_binding = (
            "exact_selected_field"
            if canonical_json(value) == canonical_json(selected)
            else "exact_selected_list_member"
            if isinstance(selected, list)
            and any(canonical_json(value) == canonical_json(item) for item in selected)
            else "binding_mismatch"
        )
        bindings.append(
            {
                "id": identifier,
                "state": "retained_reference"
                if (
                    source.get("field_path") == path
                    and source.get("subject_ref") == subject
                    and value_binding != "binding_mismatch"
                )
                else "binding_mismatch",
                "value_binding": value_binding,
            }
        )
    alternatives = [
        deepcopy(r)
        for r in card.source_assertion_store.find_by_field(path)
        if r["id"] not in identifiers
    ]
    return {
        "present": node is not None,
        "field": deepcopy(node),
        "state": "retained_references"
        if valid
        and identifiers
        and not missing
        and all(r["state"] == "retained_reference" for r in bindings)
        else "partial"
        if node is not None
        else "not_stated_in_capture",
        "selected_source_assertions": records,
        "missing_source_assertion_ids": missing,
        "bindings": bindings,
        "other_field_assertions": alternatives,
        "quality_conflicts": [
            deepcopy(c)
            for c in card.quality.get("conflicts", [])
            if c.get("field") == path
        ],
        "scope": "Original field membership only; list item-level source attribution is not reconstructed.",
    }


def compare(card, other, residue_map=None):
    """Read typed values and supplied correspondence; never mutate or acquire."""
    from .item_identity import ITEM_IDENTITY

    if any(
        not isinstance(c.id, str) or not c.id.startswith("sabueso:")
        for c in (card, other)
    ):
        raise ArgumentError("card_knowledge_diff@2 requires identified input Cards.")
    mapping = deepcopy(residue_map)
    mapping_info = _mapping(card, other, mapping)
    mine, theirs = _fields(card), _fields(other)
    fields = {}
    for path in sorted(set(mine) | set(theirs)):
        a, b = mine.get(path), theirs.get(path)
        left, right = (
            {"value": deepcopy(n.get("value")), "unit": n["unit"]}
            if n is not None and "unit" in n
            else n.get("value")
            if n is not None
            else None
            for n in (a, b)
        )
        if a is None or b is None:
            comparison = {"status": "only_other" if a is None else "only_self"}
        elif path in ITEM_IDENTITY and ITEM_IDENTITY[path] is None:
            comparison = {"status": "not_compared", "reason": "free text"}
        elif isinstance(left, list) and isinstance(right, list):
            comparison = _items(path, left, right, mapping, (_axis(card), _axis(other)))
        elif path.startswith("features_positional."):
            comparison = {
                "status": "not_compared",
                "reason": "unrecognized annotation list",
            }
        else:
            comparison = {
                "status": "same"
                if canonical_json(left) == canonical_json(right)
                else "differs"
            }
        fields[path] = {
            **comparison,
            "self": deepcopy(left),
            "other": deepcopy(right),
            "comparison_basis": "caller_supplied_residue_map_and_typed_item_content"
            if path.startswith("features_positional.")
            else "typed_stored_values_and_declared_item_identity",
            "support": {
                "self": _support(card, path, a),
                "other": _support(other, path, b),
            },
        }
    stores = [c.relationship_store.to_list() for c in (card, other)]
    relationship_sources = {}
    for role, owner, records in zip(("self", "other"), (card, other), stores):
        sources, missing = {}, []
        for record in records:
            for identifier in record.get("source_assertion_ids", []):
                if identifier in sources or identifier in missing:
                    continue
                source = owner.source_assertion_store.get(identifier)
                if source is None:
                    missing.append(identifier)
                else:
                    sources[identifier] = deepcopy(source)
        relationship_sources[role] = {
            "assertions": sources,
            "missing_source_assertion_ids": missing,
            "scope": "Recorded relationship references only; source claims are not independently verified.",
        }
    predicates = sorted({r["predicate"] for records in stores for r in records})
    relationships = {}
    for predicate in predicates:
        records = [
            [deepcopy(r) for r in store if r["predicate"] == predicate]
            for store in stores
        ]
        a, b = ({r["object_ref"] for r in rows} for rows in records)
        relationships[predicate] = {
            "both": sorted(a & b),
            "only_self": sorted(a - b),
            "only_other": sorted(b - a),
            "self_records": records[0],
            "other_records": records[1],
            "comparison_basis": "exact recorded object references; direction, channels, qualifiers and derivations remain original, not equated",
        }
    state_inputs = [deepcopy(c.knowledge_state()) for c in (card, other)]
    grouped = [{}, {}]
    for side, state in enumerate(state_inputs):
        for row in state["rows"]:
            grouped[side].setdefault((row["area"], row["source"]), []).append(row)
    changed = []
    for area, source in sorted(set(grouped[0]) | set(grouped[1])):
        a, b = (g.get((area, source), []) for g in grouped)
        if sorted(map(canonical_json, a)) != sorted(map(canonical_json, b)):
            changed.append(
                {
                    "area": area,
                    "source": source,
                    "self": deepcopy(a),
                    "other": deepcopy(b),
                }
            )
    pins = [c.pinned_ref() for c in (card, other)]
    return {
        "self": card.id,
        "other": other.id,
        "inputs": {"self": pins[0], "other": pins[1]},
        "fields": fields,
        "relationships": relationships,
        "relationship_sources": relationship_sources,
        "knowledge_states": changed,
        "state_inputs": state_inputs,
        "residue_map": mapping_info,
        "scope": "Typed original stored representations, not physical equivalence or source claim verification. Unmatched inputs do not establish absence. Free text is not compared. Caller maps do not establish alignment or identity.",
        "rule": make_derivation(
            RULE,
            inputs=pins,
            parameters={
                "residue_map": mapping_info["pairs"],
                "positional_without_map": "not_compared",
                "free_text": "not_compared",
                "multiple_identity_candidates": "ambiguous",
            },
        ),
    }
