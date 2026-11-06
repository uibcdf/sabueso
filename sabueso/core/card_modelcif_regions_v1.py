"""Original native ModelCIF reference-interval questions and saved registration.

Explicit original reference declarations and sequence agreement support an
interval question. They never establish atomic or experimental equivalence.
Keep these predicates stable for original exploration format @12 reading.
"""

from copy import deepcopy

from ._card_ligand_site_scope_v1 import _conflict, reference
from ._card_modelcif_reference_v1 import FIELDS, bound_context
from .card_exploration_history import _HistoricalInput
from .card_model_regions_v2 import model_path
from .snapshot import canonical_json

RULE = "native_model_structure_request@1"
NAVIGATION_RULE = "retained_context_links@8"
FORMAT = "sabueso.card_exploration@12"
VERIFIER = "native_model_navigation_binding@1"


def native_path(explorer, location):
    if not model_path(explorer, location):
        return False
    row, _ = explorer.access._resolve(location)
    qualifiers = row.get("qualifiers") or {}
    if "native_modelcif" in qualifiers or "native_reference_context" in qualifiers:
        return True
    card = _HistoricalInput(explorer.access._focal)
    return any(
        isinstance((source := card.source_assertion_store.get(ref)), dict)
        and isinstance(source.get("asserted_value"), dict)
        and "modelcif_metadata" in source["asserted_value"]
        for ref in row.get("source_assertion_ids", [])
    )


def context(explorer, location):
    if not native_path(explorer, location):
        return None
    row, location = explorer.access._resolve(location)
    card = _HistoricalInput(explorer.access._focal)
    canonical = reference(card)
    original = bound_context(card, row)
    result = {
        "rule": RULE,
        "model_location": deepcopy(location),
        "state": "missing_prerequisite",
        "reason": None,
        "canonical_reference": canonical,
        "original_model_context": original,
        "position_scope": None,
        "request": None,
    }

    def stop(reason, state="missing_prerequisite"):
        return {**result, "state": state, "reason": reason}

    if canonical["status"] != "comparable" or _conflict(card, set(FIELDS)):
        return stop("A consistent source-supported canonical reference is required.")
    if row.get("subject_ref") != canonical["sequence_ref"]:
        return stop(
            "The native model declaration refers to another protein.", "unsupported"
        )
    if row.get("qualifier_conflicts"):
        return stop("Alternative native model qualifiers require explicit review.")
    if original is None or original["input_binding"] != "source_assertions":
        return stop(
            "The original source-bound native reference finding is not retained or cannot be verified."
        )
    if (
        original["state"] != "comparable_interval"
        or original["eligible_for_reference_interval"] is not True
    ):
        return stop(
            "The original native reference finding does not establish a comparable sequence interval.",
            original["state"],
        )
    refs = original["focal_input_assertion_ids"]
    for field in FIELDS:
        expected = [
            ref
            for ref in refs
            if card.source_assertion_store.get(ref)["field_path"] == field
        ]
        node = card.get(field)
        if not (
            isinstance(node, dict)
            and isinstance(node.get("source_assertion_ids"), list)
            and all(isinstance(ref, str) for ref in node["source_assertion_ids"])
            and expected
            and set(node["source_assertion_ids"]) == set(expected)
            and all(
                canonical_json(node.get("value"))
                == canonical_json(
                    card.source_assertion_store.get(ref)["asserted_value"]
                )
                for ref in expected
            )
        ):
            return stop(
                "The captured reference no longer selects the model's original sequence, length and checksum inputs."
            )
    begin, end = original["comparison"]["reference_interval"]
    scope = original["comparison"]["model_scope"]
    if not (
        type(begin) is int
        and type(end) is int
        and 1 <= begin <= end <= canonical["length"]
        and original["reference"]["length"] == canonical["length"]
        and scope in ("proper_fragment", "whole_reference")
        and (scope == "whole_reference") == ([begin, end] == [1, canonical["length"]])
    ):
        return stop(
            "The original native interval is incompatible with the captured reference.",
            "unsupported",
        )
    return {
        **result,
        "state": "ready",
        "reason": f"Original declared reference interval {begin}–{end}, supported by native sequence and reference CRC64 agreement. Sequence-version date agreement remains unknown. This does not establish observed atoms, experimental equivalence or biological assembly relevance.",
        "position_scope": "original_native_reference_interval",
        "request": {
            "question": "region_coverage",
            "options": {
                "sequence_ref": canonical["sequence_ref"],
                "region": [[begin, end]],
                "include_fragments": scope == "proper_fragment",
            },
        },
    }


def link(explorer, location):
    basis = context(explorer, location)
    if basis is None:
        return None
    support = deepcopy(explorer._support(location))
    refs = set(basis["canonical_reference"].get("inputs", []))
    original = basis["original_model_context"]
    if original is not None:
        refs.update(original["focal_input_assertion_ids"])
    for record in support:
        existing = {
            statement["id"]
            for statement in [
                *record.get("statements", []),
                *record.get("derivation_input_statements", []),
            ]
        }
        record.setdefault("derivation_input_statements", []).extend(
            explorer._statement(ref) for ref in sorted(refs - existing)
        )
    return {
        "role": "question",
        "label": "Experimental structures on this native model's reference interval",
        "target_ref": "region_coverage",
        "rule": NAVIGATION_RULE,
        "support": support,
        "candidates": [],
        "paths": [],
        "blocked_paths": [],
        "availability": "available" if basis["state"] == "ready" else basis["state"],
        "model_context": basis,
    }


def register_bundle(bundle):
    if not any(
        record["flags"]["_link_panel"]
        and isinstance(record["native_payload"], dict)
        and record["native_payload"].get("rule") == NAVIGATION_RULE
        for record in bundle["views"].values()
    ):
        return
    from .card_exploration_assembly_v2 import ADAPTERS

    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER
    bundle["capabilities"]["scientific_saved_adapters"] = list(ADAPTERS)
    bundle.setdefault("scientific_results", {})
