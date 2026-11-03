"""Refuse malformed original inputs before current native ligand interpretation.

This is an input contract, not a new scientific classification or an alternative
historical reader. Valid inputs reach the unchanged original computations.
"""

from .errors import SchemaError, _diagnostic_details_allowed
from .experimental_structure_admission_v1 import decision


def _problem(relationship):
    qualifiers = relationship.get("qualifiers", {})
    root = [{"type": "Key", "value": "qualifiers"}]
    if not isinstance(qualifiers, dict):
        return root, "qualifiers_not_mapping"
    ligands = qualifiers.get("ligands")
    root = [*root, {"type": "Key", "value": "ligands"}]
    if ligands is None:
        return None
    if not isinstance(ligands, list):
        return root, "ligands_not_list"
    for index, ligand in enumerate(ligands):
        location = [*root, {"type": "Index", "value": index}]
        if not isinstance(ligand, dict):
            return location, "ligand_not_mapping"
        for field, shape, reason in (
            ("comp_id", str, "component_id_not_string"),
            ("subject_of_investigation", bool, "investigation_flag_not_boolean"),
        ):
            value = ligand.get(field)
            if value is not None and not isinstance(value, shape):
                return [*location, {"type": "Key", "value": field}], reason
    return None


def validate(cards):
    """Preflight every admitted declaration without editing or copying its data.

    Missing/null and empty lists remain valid and distinct. Foreign/unplaced
    declarations do not enter this interpretation. Nested instance/contact data
    do not authorize the component/flag classification and remain opaque here.
    """
    for card in cards:
        for row in card.relationships("has_structure"):
            if decision(card, row)["status"] != "admitted":
                continue
            problem = _problem(row)
            if problem is None:
                continue
            segments, reason = problem
            parent = reason == "qualifiers_not_mapping"
            extra = {
                "reason": "malformed_structure_qualifier_inputs"
                if parent
                else "malformed_structure_ligand_inputs",
                "problem": reason,
                "field": "has_structure.qualifiers"
                if parent
                else "has_structure.qualifiers.ligands",
            }
            if _diagnostic_details_allowed():
                pin = card.pinned_ref()
                location = {
                    "format": "card_access_location@1",
                    "kind": "card",
                    "card_ref": pin,
                    "snapshot_id": pin.rsplit("@", 1)[1],
                    "segments": [
                        {"type": "Key", "value": "relationship_store"},
                        {"type": "Record", "value": row["id"]},
                    ],
                }
                extra.update(
                    relationship_location=location,
                    location={
                        **location,
                        "segments": [*location["segments"], *segments],
                    },
                )
            raise SchemaError(
                f"Malformed retained structure {'qualifier' if parent else 'ligand'} inputs prevent scientific "
                "interpretation. Inspect the original declaration and its source "
                "support through literal Card exploration; detailed diagnostics "
                "include the exact location. Missing or malformed input does not "
                "establish ligand absence. No partial scientific result is returned.",
                extra=extra,
            )
