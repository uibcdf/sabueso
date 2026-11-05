"""Original source-sequence fragment questions; whole-model @1 stays frozen.

These predicates bind original inputs for both live navigation and inert history.
They establish sequence/reference correspondence, never identity by similarity or
atomic coordinate correspondence. Future interpretation changes need a new rule.
"""

import hashlib
from copy import deepcopy

from ._card_model_scope_v1 import bound_context, md5
from .card_exploration_history import _HistoricalInput
from .card_model_regions_v1 import link as whole_model_link
from .snapshot import canonical_json

RULE = "model_fragment_structure_request@1"
NAVIGATION_RULE = "retained_context_links@5"
FORMAT = "sabueso.card_exploration@9"
VERIFIER = "model_fragment_navigation_binding@1"
SCOPE = (
    "The original source fragment sequence and MD5 match its declared canonical "
    "interval exactly. Retained experimental fragments are included. This is "
    "sequence correspondence, not observed atoms, experimental equivalence or "
    "biological assembly relevance."
)


def _same_inputs(card, path, refs):
    node = card.get(path)
    return (
        isinstance(node, dict)
        and isinstance(node.get("source_assertion_ids"), list)
        and all(isinstance(ref, str) for ref in node["source_assertion_ids"])
        and bool(refs)
        and set(node["source_assertion_ids"]) == set(refs)
        and all(
            canonical_json(node.get("value"))
            == canonical_json(card.source_assertion_store.get(ref)["asserted_value"])
            for ref in refs
        )
    )


def _original_model(card, relationship, original):
    """Require one actual model/application; alternatives are never selected."""
    candidates = []
    for ref in relationship.get("source_assertion_ids", []):
        source = card.source_assertion_store.get(ref) or {}
        value = source.get("asserted_value")
        model = value.get("model") if isinstance(value, dict) else None
        if not isinstance(model, dict):
            continue
        entry = model.get("entryId") or model.get("modelEntityId")
        if not (
            isinstance(entry, str)
            and isinstance(source.get("source"), dict)
            and source.get("source", {}).get("record_id") == entry
            and relationship["object_ref"] == f"alphafold:{entry}"
        ):
            continue
        for application in relationship.get("derivation_applications", []):
            single = {
                **relationship,
                "source_assertion_ids": [ref],
                "derivation_applications": [application],
            }
            if canonical_json(bound_context(card, single)) == canonical_json(original):
                candidates.append((ref, model))
    return candidates[0] if len(candidates) == 1 else None


def _fragment_context(explorer, location, basis):
    canonical, original = (
        basis["canonical_reference"],
        basis["original_model_context"],
    )
    if not (
        basis["state"] == "unsupported"
        and canonical["status"] == "comparable"
        and isinstance(original, dict)
        and original["input_binding"] == "source_assertions"
        and original["identity_state"] == "focal_entry"
    ):
        return None
    begin, end = original["model_range"]
    length = canonical["length"]
    if not (
        type(begin) is int
        and type(end) is int
        and 1 <= begin <= end <= length
        and [begin, end] != [1, length]
    ):
        return None
    card = _HistoricalInput(explorer.access._focal)
    relationship, _ = explorer.access._resolve(location)
    if relationship["subject_ref"] != canonical["sequence_ref"]:
        return None
    for path, refs in (
        ("sequence.length", original["focal_length"]["source_assertion_ids"]),
        ("sequence.checksums", original["checksum_comparison"]["source_assertion_ids"]),
    ):
        if not _same_inputs(card, path, refs):
            return None
    sequence = card.get("sequence.primary")["value"]
    original_checks = [
        md5(value) for value in original["checksum_comparison"]["focal_values"]
    ]
    if not (
        original_checks
        and all(original_checks)
        and len(set(original_checks)) == 1
        and hashlib.md5(sequence.encode("utf-8"), usedforsecurity=False).hexdigest()
        == original_checks[0]
    ):
        return None
    selected = _original_model(card, relationship, original)
    if selected is None:
        return None
    source_ref, model = selected
    fragment = model.get("sequence")
    checksum = md5(model.get("sequenceChecksum"))
    if not (
        isinstance(fragment, str)
        and len(fragment) == end - begin + 1
        and fragment == sequence[begin - 1 : end]
        and checksum is not None
        and hashlib.md5(fragment.encode("utf-8"), usedforsecurity=False).hexdigest()
        == checksum
    ):
        return None
    return {
        **deepcopy(basis),
        "rule": RULE,
        "state": "ready",
        "reason": f"Original canonical interval {begin}–{end}. {SCOPE}",
        "position_scope": "original_exact_fragment_interval",
        "fragment_match": {
            "basis": "exact_original_sequence_and_md5",
            "source_assertion_id": source_ref,
            "sequence_field": "sequence",
            "range_fields": ["uniprotStart", "uniprotEnd"],
            "length": len(fragment),
            "md5": checksum,
            "reference_interval": [begin, end],
            "coordinate_correspondence": "not_established",
        },
        "request": {
            "question": "region_coverage",
            "options": {
                "sequence_ref": canonical["sequence_ref"],
                "region": [[begin, end]],
                "include_fragments": True,
            },
        },
    }


def link(explorer, location):
    original = whole_model_link(explorer, location)
    if original is None:
        return None
    fragment = _fragment_context(explorer, location, original["model_context"])
    if fragment is None:
        return original
    return {
        **original,
        "rule": NAVIGATION_RULE,
        "label": "Experimental structures on this model fragment's reference region",
        "availability": "available",
        "model_context": fragment,
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
