"""Frozen original model context and input binding from qualified 1bfc9e9.

Independent navigation/history verification only. Do not delegate to current
mapping/model readers or reinterpret the original source input contract.
"""

import re
from copy import deepcopy

from .snapshot import canonical_json

RULE = "alphafold_sequence_context@1"
FIELDS = {"sequence.checksums", "sequence.length", "annotations.isoforms"}
QUALIFIER_PATHS = ["isoform", "sequence_matches", "sequence_context"]


def md5(value):
    return (
        value.lower()
        if isinstance(value, str) and re.fullmatch(r"[a-fA-F0-9]{32}", value)
        else None
    )


def original_inputs(assertions, accession):
    """Exact source inputs; no selected Card field or foreign entry can substitute."""
    rows = [
        row
        for row in assertions or []
        if isinstance(row, dict)
        and isinstance(row.get("id"), str)
        and isinstance(row.get("source"), dict)
        and row.get("subject_ref") == f"uniprot:{accession}"
        and row.get("field_path") in FIELDS
        and (row.get("source") or {}).get("name") == "UniProt"
        and (row.get("source") or {}).get("record_id") == accession
    ]
    return list(
        {row["id"]: row for row in sorted(rows, key=lambda row: row["id"])}.values()
    )


def interpret(model, accession, sequence_md5, assertions=None):
    """A detached versioned finding over precisely supplied original inputs.

    The current prediction API defines sequenceChecksum as MD5. The older
    BigQuery column with that name uses CRC64; it is not this input contract.
    Partial model checksums cannot be compared to the whole focal sequence.
    """
    rows = original_inputs(assertions, accession)
    checks = [r for r in rows if r["field_path"] == "sequence.checksums"]
    lengths = [r for r in rows if r["field_path"] == "sequence.length"]
    isoforms = [r for r in rows if r["field_path"] == "annotations.isoforms"]
    reasons = []
    modelled = model.get("uniprotAccession")
    stated_isoforms = []
    if isinstance(modelled, str) and modelled:
        for row in isoforms:
            value = row.get("asserted_value")
            if not isinstance(value, dict):
                continue
            ids = value.get("isoform_ids") or [value.get("isoform_id")]
            if isinstance(ids, list) and modelled in ids:
                stated_isoforms.append(row["id"])
        identity = (
            "focal_entry"
            if modelled == accession
            else (
                "source_stated_isoform"
                if stated_isoforms
                else "different_accession_unclassified"
            )
        )
    else:
        identity = (
            "model_accession_not_stated"
            if modelled is None
            else "invalid_model_accession"
        )
    if identity != "focal_entry":
        reasons.append(identity)

    # Keep all original values/ids. Normalizing a digest's hex case is not an
    # identity merge, nor does it resolve incompatible source inputs.
    raw_checks = [
        (r.get("asserted_value") or {}).get("md5")
        if isinstance(r.get("asserted_value"), dict)
        else None
        for r in checks
    ]
    normalized = [md5(value) for value in raw_checks]
    supplied = md5(sequence_md5)
    if assertions is None:
        focal_md5 = supplied
        binding = "supplied_argument"
        reasons.append("focal_source_support_not_supplied")
    else:
        binding = "source_assertions"
        focal_md5 = (
            normalized[0]
            if normalized and all(normalized) and len(set(normalized)) == 1
            else None
        )
        if not focal_md5:
            reasons.append(
                "focal_checksum_not_retained"
                if not checks
                else "invalid_focal_checksum"
                if not all(normalized)
                else "conflicting_focal_checksums"
            )
        elif not supplied:
            focal_md5 = None
            reasons.append("focal_checksum_argument_missing_or_invalid")
        elif supplied != focal_md5:
            focal_md5 = None
            reasons.append("supplied_checksum_differs_from_original_support")
    model_md5 = md5(model.get("sequenceChecksum"))
    if not model_md5:
        reasons.append(
            "model_checksum_not_stated"
            if model.get("sequenceChecksum") is None
            else "invalid_model_checksum"
        )
    checksum_equal = model_md5 == focal_md5 if model_md5 and focal_md5 else None
    raw_lengths = [r.get("asserted_value") for r in lengths]
    length = (
        raw_lengths[0]
        if raw_lengths
        and all(type(v) is int and v > 0 for v in raw_lengths)
        and len(set(raw_lengths)) == 1
        else None
    )
    start, end = model.get("uniprotStart"), model.get("uniprotEnd")
    length_state = (
        "recorded"
        if length is not None
        else "not_retained"
        if not raw_lengths
        else "invalid"
        if not all(type(v) is int and v > 0 for v in raw_lengths)
        else "conflicting"
    )
    whole = (
        type(start) is int
        and type(end) is int
        and length is not None
        and start == 1
        and end == length
    )
    if not whole:
        reasons.append("whole_focal_sequence_scope_not_established")
    matches = (
        checksum_equal
        if identity == "focal_entry" and whole and binding == "source_assertions"
        else None
    )
    if matches is False:
        reasons.append("whole_sequence_checksums_differ")
    return deepcopy(
        {
            "rule": RULE,
            "focal_accession": accession,
            "model_accession": modelled,
            "identity_state": identity,
            "isoform_source_assertion_ids": stated_isoforms,
            "input_binding": binding,
            "checksum_comparison": {
                "algorithm": "md5",
                "model_value": model.get("sequenceChecksum"),
                "focal_values": raw_checks
                if assertions is not None
                else [sequence_md5],
                "equal": checksum_equal,
                "source_assertion_ids": [r["id"] for r in checks],
            },
            "focal_length": {
                "value": length,
                "state": length_state,
                "source_assertion_ids": [r["id"] for r in lengths],
            },
            "model_range": [start, end],
            "sequence_matches": matches,
            "coverage": 1.0 if matches is True else None,
            "coverage_state": "computed_whole_sequence"
            if matches is True
            else "not_computed",
            "source_assertion_ids": sorted({r["id"] for r in rows}),
            "reasons": reasons,
        }
    )


CONTEXT_RULE = RULE


def bound_context(card, relationship, *, allow_alternatives=False):
    """Replay only the actual stored inputs; never use present sequence fields."""
    q = relationship.get("qualifiers")
    if not isinstance(q, dict):
        return None
    context = q.get("sequence_context")
    if not isinstance(context, dict):
        return None
    if relationship.get("qualifier_conflicts") is not None and not isinstance(
        relationship["qualifier_conflicts"], dict
    ):
        return None
    alternatives = relationship.get("qualifier_conflicts") or {}
    if (
        not allow_alternatives
        and isinstance(alternatives, dict)
        and any(key in alternatives for key in QUALIFIER_PATHS)
    ):
        # Different original contexts are not silently replaced by the first one.
        # They may be scientifically compatible; this slice does not establish
        # that agreement or choose a historical execution for the researcher.
        return None
    applications = relationship.get("derivation_applications")
    if not isinstance(applications, list):
        return None
    for application in applications:
        if not isinstance(application, dict):
            continue
        if application.get("binding") != "original_output":
            continue
        derivation = application.get("derivation") or {}
        if not isinstance(derivation, dict):
            continue
        params = derivation.get("parameters") or {}
        if not isinstance(params, dict) or derivation.get("rule") != CONTEXT_RULE:
            continue
        if params.get("qualifier_paths") != QUALIFIER_PATHS or params.get(
            "model_input_path"
        ) != ["asserted_value", "model"]:
            continue
        focal = params.get("focal_accession")
        if (
            not isinstance(focal, str)
            or relationship.get("subject_ref") != f"uniprot:{focal}"
        ):
            continue
        recorded = application.get("qualifiers") or {}
        if not isinstance(recorded, dict):
            continue
        if canonical_json(
            {key: recorded.get(key) for key in QUALIFIER_PATHS}
        ) != canonical_json({key: q.get(key) for key in QUALIFIER_PATHS}):
            continue
        refs = params.get("focal_input_assertion_ids")
        inputs = derivation.get("inputs")
        if (
            not isinstance(refs, list)
            or not isinstance(inputs, list)
            or not all(isinstance(ref, str) for ref in refs + inputs)
        ):
            continue
        rows = [card.source_assertion_store.get(ref) for ref in refs]
        if any(row is None for row in rows) or {
            r["id"] for r in original_inputs(rows, focal)
        } != set(refs):
            continue
        for model_ref in relationship.get("source_assertion_ids", []):
            source = card.source_assertion_store.get(model_ref) or {}
            value = source.get("asserted_value") or {}
            if not isinstance(value, dict) or not isinstance(value.get("model"), dict):
                continue
            if (
                source.get("field_path") != "relationships.has_predicted_structure"
                or not isinstance(source.get("source"), dict)
                or source["source"].get("name") != "AlphaFold DB"
                or source.get("subject_ref") != relationship["subject_ref"]
                or value.get("object_ref") != relationship["object_ref"]
            ):
                continue
            if set(inputs) != {model_ref, *refs}:
                continue
            binding = params.get("input_binding")
            if binding not in ("source_assertions", "supplied_argument") or (
                binding == "supplied_argument" and refs
            ):
                continue
            replay = interpret(
                value["model"],
                focal,
                params.get("sequence_md5_argument"),
                rows if binding == "source_assertions" else None,
            )
            if canonical_json(replay) == canonical_json(context) and canonical_json(
                q.get("range")
            ) == canonical_json(replay["model_range"]):
                return deepcopy(context)
    return None
