"""Explain an inventory item through its pinned relationship and source statements.

The inventory and its classifications keep their published rules. This view reads their
output and exposes the stored inputs, without fetching, choosing a structure, or
creating a SourceAssertion (uibcdf/sabueso#91).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Sequence

from .errors import ArgumentError
from .relationship_store import make_derivation
from .structures import coverage_derivation, state_derivation, structures_view

EXPLANATION_RULE = "structure_inventory_explanation@1"


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
    regions: Any = None,
    include_fragments: bool = False,
    residue_maps: Any = None,
    reference: str | None = None,
) -> Dict[str, Any]:
    """Explain one item and the support of every member of its group.

    The complete options and every protein card's pin identify what was read, including
    cards lacking a member of the group. A missing relationship means ``not_on_card``,
    never that the structure does not exist. Unknown or excluded states keep the
    inventory's reasons. Returned records are detached from the cards.
    """
    proteins = [c for c in cards if c.meta.get("entity_type") == "protein"]
    by_id = {c.id: c for c in proteins}
    if len(by_id) != len(proteins):
        raise ArgumentError(
            argument="card_id",
            value=card_id,
            caller="Deck.explain",
            reason="an inventory explanation requires distinct protein card ids",
        )
    pins = {c.id: c.pinned_ref() for c in proteins}
    out = {
        "rule": make_derivation(
            EXPLANATION_RULE,
            inputs=list(pins.values()),
            parameters={
                "card_id": card_id,
                "structure_ref": structure_ref,
                "regions": regions,
                "include_fragments": include_fragments,
                "group_by": inventory["rule"]["parameters"]["state"],
                "residue_maps": residue_maps,
                "reference": reference,
            },
        ),
        "card_id": card_id,
        "card_ref": pins.get(card_id),
        "structure_ref": structure_ref,
        "status": "not_on_card",
        "reason": "no_has_structure_relationship",
        "item": None,
        "group": None,
        "rules": [coverage_derivation(), state_derivation(), inventory["rule"]],
        "members": [],
    }
    card = by_id.get(card_id)
    if card is None:
        out["status"] = "not_inventoried"
        out["reason"] = (
            "not_protein" if any(c.id == card_id for c in cards) else "card_not_in_deck"
        )
        return deepcopy(out)
    relationships = card.relationships("has_structure", object_ref=structure_ref)
    if not relationships:
        return deepcopy(out)
    (relationship,) = relationships
    out["members"] = [_support(card, relationship, pins[card_id])]
    out["item"] = next(
        (
            row
            for row in inventory["items"]
            if row["card_id"] == card_id and row["structure_ref"] == structure_ref
        ),
        None,
    )
    if structure_ref in inventory["excluded"].get(card_id, []):
        out["status"], out["reason"] = "excluded", "fragment_or_peptide"
        region = regions.get(card_id) if isinstance(regions, dict) else regions
        out["item"] = next(
            item
            for item in structures_view(card, include_fragments=True, region=region)[
                "items"
            ]
            if item["structure_ref"] == structure_ref
        )
    else:
        group = next(
            (
                group
                for group in inventory["states"]
                if structure_ref in group["structures"].get(card_id, [])
            ),
            None,
        )
        if group is None:
            out["status"] = "not_inventoried"
            out["reason"] = next(
                row["reason"]
                for row in inventory["not_inventoried"].get(card_id, [])
                if row["structure_ref"] == structure_ref
            )
        else:
            out["status"], out["reason"], out["group"] = "grouped", None, group
            out["members"] = [
                _support(by_id[member_id], rel, pins[member_id])
                for member_id, refs in group["structures"].items()
                for ref in refs
                for rel in by_id[member_id].relationships(
                    "has_structure", object_ref=ref
                )
            ]
    return deepcopy(out)
