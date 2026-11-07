# Frozen original B4 predicates from 2eb6114 / SDK200.
# Private consistency expectations only; preserve these meanings.
"""Source-bound direct-target selection without rewriting original assignments (#188)."""

from copy import deepcopy

from ..errors import ArgumentError, SchemaError
from .rules import make_derivation

LEGACY_RULE = "bioactivity_target_scope@1"
RULE = "bioactivity_target_scope@2"


def validate_target_scope_rule(value):
    if isinstance(value, str) and value in (LEGACY_RULE, RULE):
        return value
    raise ArgumentError(
        'target_scope_rule requires "bioactivity_target_scope@1" or "bioactivity_target_scope@2".',
        argument="target_scope_rule",
    )


def target_scope(card, copy_identity):
    """Assess retained records; only declared-copy families supply original scope.

    The caller supplies the actual measurement_identity@2 result over the same
    Card. Its numeric/publication candidates never supply a missing original.
    This is a selection interpretation, not independent experimental validation.
    """
    if copy_identity["rule"]["rule"] != "measurement_identity@2":
        raise SchemaError(
            "Target scope requires the declared-copy interpretation of measurement_identity@2."
        )
    relationships = {r["id"]: r for r in card.relationships("has_bioactivity")}
    focal = card.id
    focal = (
        focal[len("sabueso:protein:") :]
        if isinstance(focal, str) and focal.startswith("sabueso:protein:")
        else None
    )
    if not focal or ":" not in focal:
        focal = None
    assignments = {}
    for rid, rel in relationships.items():
        value = (rel["qualifiers"].get("assay") or {}).get("relationship_type")
        if value is not None and not isinstance(value, str):
            raise SchemaError(
                f"Cannot interpret target scope: assay.relationship_type of {rid} must be text or null. "
                "Inspect the original relationship and SourceAssertions."
            )
        assignments[rid] = value
    group_of = copy_identity["group_of"]
    originals = {}
    for rid, rel in relationships.items():
        if not rel["qualifiers"].get("copy_of"):
            originals.setdefault(group_of[rid], []).append(rid)
    unresolved = {row["record"]: row for row in copy_identity["unresolved_copies"]}
    decisions = {}
    for rid, rel in relationships.items():
        q = rel["qualifiers"]
        copy = q.get("copy_of")
        original_ids = sorted(originals.get(group_of[rid], [])) if copy else []
        original_context = [
            {
                "relationship_id": other,
                "subject_ref": relationships[other]["subject_ref"],
                "mapped_assignment": assignments[other],
                "source_assertion_ids": list(
                    relationships[other].get("source_assertion_ids") or []
                ),
            }
            for other in original_ids
        ]
        decision = {
            "relationship_id": rid,
            "subject_ref": rel["subject_ref"],
            "mapped_assignment": assignments[rid],
            "declared_copy": bool(copy),
            "originals": original_context,
            "source_assertion_ids": list(rel.get("source_assertion_ids") or []),
            "direct_supported": False,
        }

        def outcome(state, reason, interpretation, direct=False):
            decision.update(
                state=state,
                reason=reason,
                interpretation=interpretation,
                direct_supported=direct,
            )

        if focal is None:
            outcome(
                "unconfirmed",
                "focal_protein_reference_not_stated",
                "The retained Card does not establish a focal protein reference for this selection.",
            )
        elif rel["subject_ref"] != focal:
            outcome(
                "subject_disagreement",
                "record_subject_differs_from_focal_protein",
                "This record names another subject; it does not establish direct assignment to the focal protein.",
            )
        elif not copy:
            if assignments[rid] == "D":
                outcome(
                    "mapped_direct",
                    "mapped_record_assignment",
                    "This non-copy record is mapped D for the focal protein; this is retained source/mapping context, not independent experimental validation.",
                    True,
                )
            elif assignments[rid] is None:
                outcome(
                    "unconfirmed",
                    "mapped_assignment_not_stated",
                    "No direct-target assignment is recorded in this non-copy record.",
                )
            else:
                outcome(
                    "outside_direct_scope",
                    "mapped_assignment_not_direct",
                    "The retained mapped assignment does not satisfy the direct-only D criterion.",
                )
        elif len(original_ids) != 1:
            outcome(
                "unconfirmed",
                "original_not_resolved" if not original_ids else "original_ambiguous",
                "This declared copy has no uniquely resolved non-copy original at this Card pin; its own mapping does not establish direct-target scope.",
            )
            if rid in unresolved:
                decision["copy_resolution"] = unresolved[rid]
        else:
            original = original_context[0]
            value = original["mapped_assignment"]
            own = assignments[rid]
            if original["subject_ref"] != focal:
                outcome(
                    "subject_disagreement",
                    "original_subject_differs_from_focal_protein",
                    "The resolved original names another subject; direct assignment cannot be transferred to the focal protein.",
                )
            elif value is None:
                outcome(
                    "unconfirmed",
                    "original_assignment_not_stated",
                    "The resolved original has no recorded direct-target assignment; the copy mapping cannot supply that missing original context.",
                )
            elif own is not None and own != value:
                outcome(
                    "assignment_disagreement",
                    "copy_and_original_assignments_differ",
                    "The copy and its resolved original have different mapped target assignments; direct-only scope is not established. Inspect both records.",
                )
            elif value == "D":
                outcome(
                    "resolved_original_direct",
                    "resolved_original_assignment",
                    "A unique declared-copy original is mapped D for this same focal protein. The original supplies scope; the copy's raw fields are unchanged.",
                    True,
                )
            else:
                outcome(
                    "outside_direct_scope",
                    "original_assignment_not_direct",
                    "The resolved original does not satisfy the direct-only D criterion; its declared copy cannot bypass that scope.",
                )
        decisions[rid] = decision
    return deepcopy(
        {
            "rule": make_derivation(
                RULE,
                inputs=["meta.card_id", "has_bioactivity", "entities"],
                parameters={
                    "non_copy": "retained mapped D and exact focal subject required",
                    "declared_copy": "unique resolved non-copy original mapped D for the same focal subject, with no different recorded copy assignment",
                    "copy_resolution": "measurement_identity@2 declared-copy edges only; numeric/publication candidates supply no original scope",
                    "unknown_or_disagreement": "excluded from direct-only selection; original values/support retained",
                    "include_indirect": "explicit True includes retained rows with their original scope diagnostics; no acquisition",
                    "scope_meaning": "selection over retained source/mapping assignments, not independently validated experimental target identity",
                },
            ),
            "focal_ref": focal,
            "records": decisions,
            "record_count": len(decisions),
            "direct_supported_count": sum(
                row["direct_supported"] for row in decisions.values()
            ),
        }
    )
