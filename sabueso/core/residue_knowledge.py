"""Read independent residue observations with their exact source sequence scope."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from .errors import SchemaError, StorageError
from .residues import canonical_sequence, item_support, residue_view
from .snapshot import canonical_json, digest
from .source_assertion_store import assertion_value

RULE = "residue_knowledge@1"
TYPE_PROPERTIES = "amino_acid.properties."
TYPE_STATISTICS = "amino_acid.statistics."
TRACKS = "sequence.residue_tracks."


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _type_reference(path):
    return path == "amino_acid.indices" or path.startswith(
        (TYPE_PROPERTIES, TYPE_STATISTICS)
    )


def _sequence(assertion, subject):
    """Validate an explicit source sequence declaration; equality is not identity."""
    metadata = assertion.get("source_metadata") or {}
    stated = metadata.get("sequence")
    if not isinstance(stated, dict):
        return None, "source sequence not stated"
    sequence_id, value = stated.get("id"), stated.get("value")
    if (
        not _text(sequence_id)
        or not isinstance(value, str)
        or not re.fullmatch(r"[A-Z]+", value)
    ):
        return None, "source sequence declaration malformed"
    if stated.get("uniprot_ref") != subject:
        return None, "source sequence subject differs"
    sha256 = hashlib.sha256(value.encode()).hexdigest()
    if stated.get("sha256") is not None and stated["sha256"] != sha256:
        return None, "source sequence digest differs"
    return {"id": sequence_id, "value": value, "sha256": sha256}, None


def _support(assertion, origin, index):
    """Pin the complete original record, including revisions and metadata."""
    if not (
        all(_text(assertion.get(key)) for key in ("id", "subject_ref", "field_path"))
        and "asserted_value" in assertion
        and isinstance(assertion.get("source"), dict)
        and all(_text(assertion["source"].get(key)) for key in ("name", "record_id"))
        and isinstance(assertion.get("source_metadata", {}), dict)
    ):
        raise SchemaError(
            "Residue knowledge requires identified SourceAssertion records."
        )
    try:
        snapshot = digest(canonical_json(assertion))
    except (TypeError, ValueError, StorageError) as error:
        raise SchemaError(
            "Residue SourceAssertions must contain finite JSON values."
        ) from error
    return {
        "origin": origin,
        "input_index": index,
        "source_assertion_id": assertion["id"],
        "snapshot_id": snapshot,
        "assertion": deepcopy(assertion),
    }


def _scalar(value, metric):
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return metric != "probability" or 0 <= value <= 1
    return (
        metric != "probability"
        and isinstance(value, dict)
        and set(value) == {"value", "unit"}
        and isinstance(value["value"], (int, float))
        and not isinstance(value["value"], bool)
        and _text(value["unit"])
    )


def _track(value, sequence_id, length, position):
    """Select one native observation, without interpolating or converting units."""
    if value.get("sequence_id") != sequence_id or value.get("indexing") != "1-based":
        return None, "track sequence or indexing differs"
    metric = value.get("metric")
    if not _text(metric):
        return None, "track metric not stated"
    dense, sparse = "values" in value, "observations" in value
    if dense == sparse:
        return None, "track must state exactly one dense or sparse representation"
    if dense:
        samples = value["values"]
        if not isinstance(samples, list) or len(samples) != length:
            return None, "dense track length differs from its source sequence"
        samples = {i: sample for i, sample in enumerate(samples, 1)}
    else:
        rows = value["observations"]
        if not isinstance(rows, list):
            return None, "sparse track observations malformed"
        samples = {}
        native_rows = {}
        for row in rows:
            if not isinstance(row, dict) or "value" not in row:
                return None, "sparse track observation malformed"
            index = row.get("position")
            if (
                isinstance(index, bool)
                or not isinstance(index, int)
                or not 1 <= index <= length
                or index in samples
            ):
                return None, "sparse track position invalid or repeated"
            samples[index] = row["value"]
            native_rows[index] = row
    if any(
        sample is not None and not _scalar(sample, metric)
        for sample in samples.values()
    ):
        return None, "track value invalid for its declared metric"
    if position not in samples or samples[position] is None:
        return None, "value not stated at selected position"
    context = {
        k: deepcopy(v) for k, v in value.items() if k not in {"values", "observations"}
    }
    if sparse:
        context["native_observation"] = deepcopy(native_rows[position])
    return {**context, "value": deepcopy(samples[position])}, None


def residue_knowledge(card, position, sequence_ref, supplied):
    """Detached named view; no new card field, source query or source assertion."""
    canonical, canonical_id, canonical_node = canonical_sequence(card)
    subject = f"uniprot:{card.get('identifiers.uniprot')['value']}"
    inputs = []
    for origin, assertions in (
        ("card_store", card.source_assertion_store.to_list()),
        ("supplied", supplied or []),
    ):
        for index, assertion in enumerate(assertions):
            path = assertion.get("field_path", "")
            supported = isinstance(path, str) and (
                path == "disorder.regions"
                or _type_reference(path)
                or path.startswith(TRACKS)
            )
            if origin == "card_store" and not supported:
                continue
            support = _support(assertion, origin, index)
            inputs.append((assertion, support))

    selected = {
        "id": canonical_id,
        "value": canonical,
        "sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    }
    sequence_support = item_support(card, "sequence.primary", canonical_node, canonical)
    if sequence_ref != "canonical":
        candidates = []
        for assertion, support in inputs:
            if assertion["subject_ref"] != subject:
                continue
            declared, _ = _sequence(assertion, subject)
            if declared and declared["id"] == sequence_ref:
                candidates.append((declared, support))
        if not candidates:
            raise SchemaError(
                "Selected source sequence has no valid subject-bound declaration."
            )
        if len({candidate[0]["value"] for candidate in candidates}) != 1:
            raise SchemaError(
                "Selected source sequence has contradictory declarations."
            )
        selected = candidates[0][0]
        sequence_support = {
            "basis": "source_sequence_declaration",
            "support": [s for _, s in candidates],
        }
    if position > len(selected["value"]):
        raise IndexError(
            f"Residue position {position} exceeds sequence length {len(selected['value'])}"
        )

    canonical_view = (
        residue_view(card, position) if sequence_ref == "canonical" else None
    )
    output = {
        "rule": RULE,
        "card_ref": card.pinned_ref() if card.id else None,
        "subject_ref": subject,
        "sequence_ref": selected["id"],
        "sequence_sha256": selected["sha256"],
        "sequence_basis": "stored_canonical"
        if canonical_view
        else "source_sequence_declaration",
        "sequence_support": sequence_support,
        "position": position,
        "indexing": "1-based",
        "amino_acid": selected["value"][position - 1],
        "stored_annotations": canonical_view,
        "amino_acid_type_properties": [],
        "amino_acid_type_statistics": [],
        "residue_tracks": [],
        "source_annotations": [],
        "missing_values": [],
        "unmapped": [],
    }
    for assertion, support in inputs:
        path, value = assertion["field_path"], assertion_value(assertion)
        item = {"field_path": path, "value": deepcopy(value), "support": support}
        if _type_reference(path):
            amino_acid = assertion["subject_ref"].removeprefix("amino_acid:")
            if assertion["subject_ref"] != f"amino_acid:{output['amino_acid']}":
                if not assertion["subject_ref"].startswith("amino_acid:"):
                    output["unmapped"].append(
                        {**item, "reason": "type reference subject differs"}
                    )
                continue
            if not isinstance(value, dict) or value.get("amino_acid") != amino_acid:
                output["unmapped"].append(
                    {**item, "reason": "type reference amino acid differs"}
                )
                continue
            native_key = "native_value" if path == "amino_acid.indices" else "value"
            if native_key not in value:
                output["unmapped"].append(
                    {**item, "reason": "type reference value not stated"}
                )
                continue
            item["value_status"] = (
                "not_stated"
                if (
                    value[native_key] is None
                    or path == "amino_acid.indices"
                    and value[native_key] == "NA"
                )
                else "stated"
            )
            key = (
                "amino_acid_type_statistics"
                if path.startswith(TYPE_STATISTICS)
                else "amino_acid_type_properties"
            )
            output[key].append(item)
            continue
        if path != "disorder.regions" and not path.startswith(TRACKS):
            output["unmapped"].append({**item, "reason": "unsupported assertion field"})
            continue
        declared, reason = _sequence(assertion, subject)
        if assertion["subject_ref"] != subject:
            reason = "assertion subject differs"
        elif declared and declared != selected:
            reason = "source sequence identity or content differs"
        if reason:
            output["unmapped"].append({**item, "reason": reason})
            continue
        if not isinstance(value, dict):
            output["unmapped"].append(
                {**item, "reason": "positional assertion value malformed"}
            )
            continue
        if path.startswith(TRACKS):
            observation, reason = _track(
                value, selected["id"], len(selected["value"]), position
            )
            if reason:
                key = (
                    "missing_values"
                    if reason == "value not stated at selected position"
                    else "unmapped"
                )
                output[key].append({**item, "reason": reason})
            else:
                output["residue_tracks"].append({**item, "value": observation})
        else:
            location = value.get("location")
            if not isinstance(location, dict):
                location = {}
            coords = location.get("sequence")
            if not isinstance(coords, dict):
                coords = {}
            begin, end = coords.get("start"), coords.get("end")
            native_disorder = value.get("term_id") == "IDPO:0000002" or (
                assertion.get("source", {}).get("name") == "MobiDB"
                and value.get("feature") == "disorder"
            )
            if (
                location.get("kind") != "sequence"
                or coords.get("sequence_id") != selected["id"]
                or coords.get("indexing") != "1-based"
                or any(
                    isinstance(n, bool) or not isinstance(n, int) for n in (begin, end)
                )
                or not 1 <= begin <= end <= len(selected["value"])
                or not native_disorder
            ):
                output["unmapped"].append(
                    {**item, "reason": "native disorder location or term invalid"}
                )
            elif begin <= position <= end:
                output["source_annotations"].append(item)
    return output
