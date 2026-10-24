"""Conservative model scope from original stored AlphaFold derivation inputs."""

from copy import deepcopy

from sabueso.mappings.alphafold_context_v1 import (
    QUALIFIER_PATHS,
    interpret,
    original_inputs,
)
from sabueso.mappings.alphafold_context_v1 import RULE as CONTEXT_RULE

from .snapshot import canonical_json

RULE = "predicted_structure_scope@1"


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


def predicted_structures_view(card):
    items = []
    for rel in card.relationships(predicate="has_predicted_structure"):
        q = rel.get("qualifiers") if isinstance(rel.get("qualifiers"), dict) else {}
        context = bound_context(card, rel)
        supported = context is not None
        alternatives = rel.get("qualifier_conflicts") or {}
        multiple = isinstance(alternatives, dict) and any(
            key in alternatives for key in QUALIFIER_PATHS
        )
        item = {
            "model_ref": rel["object_ref"],
            **{
                key: deepcopy(q.get(key))
                for key in (
                    "model_version",
                    "tool",
                    "mean_plddt",
                    "plddt_fractions",
                    "range",
                )
            },
            "isoform": context["model_accession"]
            if supported and context["identity_state"] == "source_stated_isoform"
            else None,
            "coverage": context["coverage"] if supported else None,
            "coverage_scope": "original_whole_sequence_input"
            if supported and context["coverage"] is not None
            else None,
            "sequence_matches": context["sequence_matches"] if supported else None,
            "recorded_isoform": deepcopy(q.get("isoform")),
            "recorded_sequence_matches": deepcopy(q.get("sequence_matches")),
            "context_state": (
                "original_source_inputs_bound"
                if context["input_binding"] == "source_assertions"
                else "supplied_argument_bound"
            )
            if supported
            else "multiple_original_contexts"
            if multiple
            else "original_basis_not_established",
            "qualifier_conflicts": deepcopy(alternatives),
            "sequence_context": context,
            "rule": RULE,
            "relationship_id": rel["id"],
            "source_assertion_ids": list(rel.get("source_assertion_ids") or []),
        }
        items.append(item)
    return {"items": sorted(items, key=lambda item: item["model_ref"])}
