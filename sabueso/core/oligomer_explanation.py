"""Complete original inputs of versioned quaternary interpretation (#165)."""

from copy import deepcopy

from .bioactivity_explanation import _Support
from .oligomer import (
    AGREEMENT_RULE,
    FAMILY,
    LEGACY_AGREEMENT_RULE,
    PREVIOUS_AGREEMENT_RULE,
    REFERENCE_FIELDS,
    oligomer_view,
)
from .relationship_store import make_derivation

RULE = "oligomer_explanation@3"
LEGACY_RULE = "oligomer_explanation@1"
SUBUNIT = "annotations.subunit"


def explain_oligomer(card, agreement_rule=AGREEMENT_RULE):
    if agreement_rule in (LEGACY_AGREEMENT_RULE, PREVIOUS_AGREEMENT_RULE):
        from ._oligomer_explanation_legacy_v2 import explain_oligomer as legacy

        return legacy(card, agreement_rule)
    return _explain_oligomer(card, oligomer_view(card, agreement_rule))


def _explain_oligomer(card, view):
    """Explain one already evaluated result without calculating another view."""
    support = _Support(card, predicates={"has_structure", "has_interface_with"})
    fields = [support.field(path) for path in (SUBUNIT, FAMILY, *REFERENCE_FIELDS)]
    for entry in fields:
        alternatives = [
            row
            for row in card.quality.get("alternatives", [])
            if isinstance(row, dict) and row.get("field") == entry["field_path"]
        ]
        entry["selection_alternatives"] = deepcopy(alternatives)

        def identifiers(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, list):
                for item in value:
                    yield from identifiers(item)

        entry["alternative_source_assertions"] = support.assertions(
            list(
                identifiers(
                    [row.get("source_assertion_ids", []) for row in alternatives]
                )
            )
        )
    subunit = [
        {
            "item": row,
            "locator": {
                "card_ref": support.pin,
                "field_path": SUBUNIT,
                "index": row["index"],
            },
            "source_assertions": support.assertions(row["source_assertion_ids"]),
        }
        for row in view["subunit"]
    ]
    structures = []
    for row in view["assemblies"]:
        structures.append(
            {
                "item": row,
                "structure": support.links[row["relationship_id"]],
                "support_basis": "relationship",
                "qualifier_lineage": "unrecorded_mapping_lineage_is_not_reconstructed",
            }
        )
    interfaces = []
    for row in view["interfaces"]:
        inputs = [
            {
                "structure_ref": ref,
                "declaration": basis,
                "structure": support.links.get(basis["relationship_id"]),
            }
            for ref, bases in row["basis"].items()
            for basis in bases
        ]
        interfaces.append(
            {
                "item": row,
                "interface": support.links[row["relationship_id"]],
                "classification_inputs": {
                    "classification": row["classification"],
                    "structures": inputs,
                    "coordinate_scope": row["coordinate_scope"],
                    "canonical_reference": view["canonical_reference"],
                    "residue_scope": "source_aggregate_across_structures_not_assembly_occurrences",
                },
            }
        )
    family = [
        {
            "item": row,
            "locator": {
                "card_ref": support.pin,
                "field_path": FAMILY,
                "index": row["index"],
            },
            "value": row["value"],
            "source_assertions": support.assertions(row["source_assertion_ids"]),
        }
        for row in view["family_interface_sites"]
    ]
    agreement = [
        {
            "item": row,
            "rule": AGREEMENT_RULE,
            "observed_interface_ref": support.links[row["interface_relationship_id"]][
                "relationship_ref"
            ],
            "family_site_locator": {
                "card_ref": support.pin,
                "field_path": FAMILY,
                "index": row["family_site_index"],
            },
            "selection_basis": "every_focal_self_interface_family_pair",
            "source_assertions": support.assertions(row["source_assertion_ids"]),
            "comparison": row["comparison"],
        }
        for row in view["agreement"]
    ]
    return deepcopy(
        {
            "rule": make_derivation(
                RULE,
                inputs=[support.pin],
                parameters={"agreement_rule": AGREEMENT_RULE},
            ),
            "card_ref": support.pin,
            "status": "not_on_card"
            if not (structures or interfaces or family or view["subunit"])
            else "partial"
            if support.gaps
            or view["canonical_reference"]["status"] != "comparable"
            or any(
                row["classification"]["status"] != "computed"
                or row["coordinate_scope"]["status"] != "comparable"
                for row in view["interfaces"]
            )
            or any(
                row["comparison"]["status"] != "comparable" for row in view["agreement"]
            )
            else "on_card"
            if structures or interfaces or family or view["subunit"]
            else "not_on_card",
            "view": view,
            "fields": fields,
            "subunit": subunit,
            "structures": structures,
            "interfaces": interfaces,
            "family_interface_sites": family,
            "agreement": agreement,
            "context": {
                "scope": "all_original_card_inputs",
                "canonical_reference": view["canonical_reference"],
                "excluded_structure_relationships": view[
                    "excluded_structure_relationships"
                ],
                "stored_quality": deepcopy(card.quality),
                "source_coverage": "read knowledge_state separately; input absence is not external source absence",
                "scope_limits": view["scope"],
            },
            "gaps": support.gaps,
        }
    )
