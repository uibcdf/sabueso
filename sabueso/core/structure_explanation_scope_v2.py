"""Frozen relationship-scoped explanation policy; no source queries or identity joins.

The callback family supplies either ordinary native readers or frozen verifier
predicates. Keep this named policy stable for original saved reading.
"""

from copy import deepcopy

RULE = "structure_inventory_explanation@2"
_LIGANDS = {
    "ligand_of_interest": "ligand_of_interest",
    "no_ligand_of_interest": "none_of_interest",
    "no_ligands": "none_of_interest",
    "unstated": "unstated",
}


def group_state(row, inventory):
    """Original inventory @1 group key, bound to one exact retained row."""
    if row["state"]["sequence"] is None:
        return None
    parameters = inventory["rule"]["parameters"]
    state = dict(row["state"])
    state["ligands:interest"] = _LIGANDS.get(state["ligands"])
    in_frame = row["card_id"] == parameters.get("reference") or row[
        "card_id"
    ] in parameters.get("mapped", [])
    substitutions = sorted(
        (m["reference_position"], m["residue"])
        if in_frame and m["reference_position"] is not None
        else (row["card_id"], m["label"])
        for m in row.get("substitutions_in_reference") or []
    )
    state["substitutions"] = [
        f"{pos}{res}" if isinstance(pos, int) else f"{res} ({pos})"
        for pos, res in substitutions
    ]
    return {key: state[key] for key in parameters["state"]}


def evaluate(
    cards,
    card_id,
    structure_ref,
    inventory,
    *,
    relationship_id=None,
    regions=None,
    include_fragments=False,
    residue_maps=None,
    reference=None,
    rule,
    support,
    structures_view,
    coverage_derivation,
    state_derivation,
):
    from .errors import ArgumentError

    if relationship_id is not None and (
        not isinstance(relationship_id, str) or not relationship_id.strip()
    ):
        raise ArgumentError(
            "relationship_id requires None or a nonempty exact record id."
        )
    proteins = [c for c in cards if c.meta.get("entity_type") == "protein"]
    by_id = {c.id: c for c in proteins}
    if len(by_id) != len(proteins):
        raise ArgumentError(
            "An inventory explanation requires distinct protein card ids."
        )
    pins = {c.id: c.pinned_ref() for c in proteins}
    out = {
        "rule": rule(
            RULE,
            inputs=list(pins.values()),
            parameters={
                "card_id": card_id,
                "structure_ref": structure_ref,
                "relationship_id": relationship_id,
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
        "relationship_id": relationship_id,
        "status": "not_on_card",
        "reason": "no_has_structure_relationship",
        "item": None,
        "group": None,
        "candidates": [],
        "rules": [coverage_derivation(), state_derivation(), inventory["rule"]],
        "members": [],
    }
    card = by_id.get(card_id)
    if card is None:
        out.update(
            status="not_inventoried",
            reason="not_protein"
            if any(c.id == card_id for c in cards)
            else "card_not_in_deck",
        )
        return deepcopy(out)
    relationships = card.relationships("has_structure", object_ref=structure_ref)
    if relationship_id is not None:
        relationships = [r for r in relationships if r["id"] == relationship_id]
        if not relationships:
            out["reason"] = "relationship_not_on_card_for_structure"
    if not relationships:
        return deepcopy(out)
    if len(relationships) != 1:
        out.update(status="ambiguous", reason="multiple_has_structure_relationships")
        out["members"] = [support(card, rel, pins[card_id]) for rel in relationships]
        out["candidates"] = [
            {
                "relationship_id": rel["id"],
                "relationship_ref": f"{pins[card_id]}#{rel['id']}",
            }
            for rel in relationships
        ]
        return deepcopy(out)
    relationship = relationships[0]
    selected = relationship["id"]
    out["relationship_id"] = selected
    out["rule"]["parameters"]["relationship_id"] = selected
    out["members"] = [support(card, relationship, pins[card_id])]
    rows = [
        r
        for r in inventory["items"]
        if r["card_id"] == card_id and r["relationship_id"] == selected
    ]
    if not rows:
        region = regions.get(card_id) if isinstance(regions, dict) else regions
        excluded = [
            r
            for r in structures_view(card, include_fragments=True, region=region)[
                "items"
            ]
            if r["relationship_id"] == selected
        ]
        if (
            not include_fragments
            and len(excluded) == 1
            and excluded[0]["coverage_class"] == "fragment_or_peptide"
        ):
            out.update(
                status="excluded", reason="fragment_or_peptide", item=excluded[0]
            )
        else:
            out.update(status="not_inventoried", reason="relationship_not_in_inventory")
        return deepcopy(out)
    if len(rows) != 1:
        out.update(
            status="ambiguous", reason="multiple_inventory_rows_for_relationship"
        )
        return deepcopy(out)
    row = rows[0]
    out["item"] = row
    state = group_state(row, inventory)
    if state is None:
        reasons = {
            r["reason"]
            for r in inventory["not_inventoried"].get(card_id, [])
            if r["structure_ref"] == structure_ref
        }
        out.update(
            status="not_inventoried",
            reason=next(iter(reasons))
            if len(reasons) == 1
            else "unknown_original_inventory_reason",
        )
        return deepcopy(out)
    groups = [
        g
        for g in inventory["states"]
        if g["state"] == state and structure_ref in g["structures"].get(card_id, [])
    ]
    if len(groups) != 1:
        out.update(status="not_inventoried", reason="no_unique_original_group")
        return deepcopy(out)
    group = groups[0]
    out.update(status="grouped", reason=None, group=group)
    out["members"] = [
        support(
            by_id[member_id],
            by_id[member_id].relationship_store.get(member["relationship_id"]),
            pins[member_id],
        )
        for member_id in group["structures"]
        for member in inventory["items"]
        if member["card_id"] == member_id
        and member["structure_ref"] in group["structures"][member_id]
        and group_state(member, inventory) == state
    ]
    return deepcopy(out)
