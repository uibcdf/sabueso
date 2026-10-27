"""Frozen source-bound model-to-reference questions, without residue mapping.

Only a verified whole-reference model may prepare this v1 question. Fragments,
isoforms and historical gaps stay inspectable without a guessed correspondence.
"""

import hashlib
from copy import deepcopy

from ._card_ligand_site_scope_v1 import _conflict, reference
from ._card_model_scope_v1 import bound_context
from .card_exploration_history import _HistoricalInput
from .snapshot import canonical_json

RULE = "model_structure_request@1"
NAVIGATION_RULE = "retained_context_links@4"


def model_path(explorer, location):
    s = location.get("segments", [])
    if not (
        location.get("kind") == "card"
        and len(s) == 2
        and s[0] == {"type": "Key", "value": "relationship_store"}
        and s[1].get("type") == "Record"
    ):
        return False
    row, _ = explorer.access._resolve(location)
    return isinstance(row, dict) and row.get("predicate") == "has_predicted_structure"


def context(explorer, location):
    if not model_path(explorer, location):
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

    if canonical["status"] != "comparable":
        return stop("A consistent source-supported canonical reference is required.")
    if _conflict(card, {"sequence.checksums"}):
        return stop("The captured reference checksum has unresolved source conflicts.")
    if row.get("subject_ref") != canonical["sequence_ref"]:
        return stop("The model declaration refers to another protein.", "unsupported")
    if row.get("qualifier_conflicts"):
        return stop(
            "Alternative model qualifiers require explicit review; no context is selected."
        )
    if original is None or original["input_binding"] != "source_assertions":
        return stop(
            "The original source-bound model context is not retained or cannot be verified."
        )
    if original["identity_state"] != "focal_entry":
        return stop(
            "This model does not declare the captured canonical entry; no isoform mapping is inferred.",
            "unsupported",
        )
    if original["sequence_matches"] is not True or original["model_range"] != [
        1,
        canonical["length"],
    ]:
        return stop(
            "A confirmed whole-reference checksum and range are required. Fragment correspondence is not established by this question.",
            "unsupported",
        )
    # Retain the original reference selection, rather than accepting a new field
    # or revision just because its label or value looks equivalent.
    for field, refs in (
        ("sequence.length", original["focal_length"]["source_assertion_ids"]),
        ("sequence.checksums", original["checksum_comparison"]["source_assertion_ids"]),
    ):
        node = card.get(field)
        if not (
            isinstance(node, dict)
            and isinstance(node.get("source_assertion_ids"), list)
            and all(isinstance(ref, str) for ref in node["source_assertion_ids"])
            and refs
            and set(node["source_assertion_ids"]) == set(refs)
            and all(
                canonical_json(node.get("value"))
                == canonical_json(
                    card.source_assertion_store.get(ref)["asserted_value"]
                )
                for ref in refs
            )
        ):
            return stop(
                "The captured reference no longer selects the model's original checksum/length inputs."
            )
    sequence = card.get("sequence.primary")["value"]
    checksum = hashlib.md5(sequence.encode("utf-8"), usedforsecurity=False).hexdigest()
    model_checksum = original["checksum_comparison"]["model_value"]
    if not isinstance(model_checksum, str) or checksum != model_checksum.lower():
        return stop(
            "The captured canonical sequence differs from the original model checksum."
        )
    result.update(
        state="ready",
        reason="Uses the original source-supported whole-reference interval and confirmed checksum. This does not establish observed atoms, experimental equivalence or biological assembly relevance.",
        position_scope="original_whole_reference_interval",
        request={
            "question": "region_coverage",
            "options": {
                "sequence_ref": canonical["sequence_ref"],
                "region": [[1, canonical["length"]]],
                "include_fragments": False,
            },
        },
    )
    return result


def link(explorer, location):
    basis = context(explorer, location)
    if basis is None:
        return None
    support = deepcopy(explorer._support(location))
    refs = set(basis["canonical_reference"].get("inputs", []))
    original = basis["original_model_context"]
    if original is not None:
        refs.update(original["source_assertion_ids"])
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
        "label": "Experimental structures on this model's original reference",
        "target_ref": "region_coverage",
        "rule": NAVIGATION_RULE,
        "support": support,
        "candidates": [],
        "paths": [],
        "blocked_paths": [],
        "availability": "available" if basis["state"] == "ready" else basis["state"],
        "model_context": basis,
    }
