"""Explain an inventory item through its pinned relationship and source statements.

The inventory and its classifications keep their published rules. This view reads their
output and exposes the stored inputs, without fetching, choosing a structure, or
creating a SourceAssertion (uibcdf/sabueso#91).
"""

from __future__ import annotations

from typing import Any, Dict, Sequence

from .relationship_store import make_derivation
from .structures import coverage_derivation, state_derivation, structures_view

EXPLANATION_RULE = "structure_inventory_explanation@3"


def _support(card: Any, relationship: Dict[str, Any], pin: str) -> Dict[str, Any]:
    """Relationship-level support, never invented attribution per qualifier.

    Reference fields describe the pinned card's context. They do not claim to recover
    the exact inputs of a mapping performed when the card was built.
    """

    def assertions(ids):
        return [
            {**record, "source_assertion_ref": f"{pin}#{record['id']}"}
            for record in card.explain(ids, skip_digestion=True)
        ]

    context = []
    for path in ("sequence.length", "sequence.primary"):
        node = card.get(path)
        if node is not None:
            context.append(
                {
                    "field_path": path,
                    "node": node,
                    "source_assertions": assertions(
                        node.get("source_assertion_ids", [])
                    ),
                    "conflicts": [
                        record
                        for record in card.quality.get("conflicts") or []
                        if record.get("field") == path
                    ],
                }
            )
    return {
        "card_ref": pin,
        "structure_ref": relationship["object_ref"],
        "relationship_ref": f"{pin}#{relationship['id']}",
        "relationship": relationship,
        "support_basis": "relationship",
        "source_assertions": assertions(relationship.get("source_assertion_ids", [])),
        "reference_context": {"basis": "stored_card_fields", "fields": context},
        "enrichments": [
            record
            for record in card.quality.get("enrichments") or []
            if record.get("source") == "RCSB PDB"
            and f"pdb:{record.get('structure')}" == relationship["object_ref"]
        ],
    }


def explain_structure_inventory(
    cards: Sequence[Any],
    card_id: str,
    structure_ref: str,
    inventory: Dict[str, Any],
    *,
    relationship_id: str | None = None,
    regions: Any = None,
    include_fragments: bool = False,
    residue_maps: Any = None,
    reference: str | None = None,
) -> Dict[str, Any]:
    """Explain an exact retained declaration; report ambiguous PDB-only requests.

    Group support follows original inventory row identifiers and state keys.
    Equal PDB labels never select or multiply another declaration's support.
    """
    from .structure_explanation_scope_v3 import evaluate

    return evaluate(
        cards,
        card_id,
        structure_ref,
        inventory,
        relationship_id=relationship_id,
        regions=regions,
        include_fragments=include_fragments,
        residue_maps=residue_maps,
        reference=reference,
        rule=make_derivation,
        support=_support,
        structures_view=structures_view,
        coverage_derivation=coverage_derivation,
        state_derivation=state_derivation,
    )
