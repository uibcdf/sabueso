# Frozen original quaternary predicates from0830de5/SDK109 (#148).
# Independent saved verification only; preserve these semantics.
"""Complete original inputs of versioned quaternary interpretation (#165)."""

from copy import deepcopy

from ._card_quaternary_native_v1 import (
    AGREEMENT_RULE,
    FAMILY,
    LEGACY_AGREEMENT_RULE,
    PREVIOUS_AGREEMENT_RULE,
    REFERENCE_FIELDS,
    oligomer_view,
)
from .card_exploration_history import _rule as make_derivation

GLOSSARY_PREDICATES = {
    "same_as",
    "has_ligand_site",
    "engages",
    "has_bioactivity",
    "has_structure",
}


class _Support:
    def __init__(self, card, *, predicates=GLOSSARY_PREDICATES):
        self.card = card
        self.pin = card.pinned_ref()
        self.gaps = []
        self.links = {
            rel["id"]: self.relationship(rel)
            for rel in card.relationships()
            if rel["predicate"] in predicates
        }

    def relationship(self, rel):
        ref = f"{self.pin}#{rel['id']}"
        ids = rel.get("source_assertion_ids") or []
        if not ids and not rel.get("derivation"):
            self.gaps.append(
                {"reason": "no_relationship_support", "relationship_ref": ref}
            )
        assertions = self.assertions(ids)
        return {
            "relationship_ref": ref,
            "relationship": rel,
            "source_assertions": assertions,
        }

    def assertions(self, ids):
        assertions = [
            {**row, "source_assertion_ref": f"{self.pin}#{row['id']}"}
            for row in self.card.explain(sorted(set(ids)), skip_digestion=True)
        ]
        self.gaps.extend(
            {
                "reason": "missing_source_assertion",
                "source_assertion_ref": row["source_assertion_ref"],
            }
            for row in assertions
            if not row["found"]
        )
        return assertions

    def field(self, path):
        node = self.card.get(path)
        if node is None:
            return {"field_path": path, "stored": False}
        ids = node.get("source_assertion_ids") or []
        if not ids:
            self.gaps.append(
                {
                    "reason": "no_selected_source_assertion",
                    "field_path": path,
                    "card_ref": self.pin,
                }
            )
        conflicts = [
            c
            for c in self.card.quality.get("conflicts") or []
            if c.get("field") == path
        ]

        def flatten(ids):
            for value in ids:
                if isinstance(value, str):
                    yield value
                else:
                    yield from flatten(value)

        return {
            "field_path": path,
            "stored": True,
            "node": node,
            "source_assertions": self.assertions(ids),
            "alternatives": self.assertions(
                [
                    a["id"]
                    for a in self.card.source_assertion_store.to_list()
                    if a.get("field_path") == path and a["id"] not in ids
                ]
            ),
            "conflicts": conflicts,
            "conflict_source_assertions": self.assertions(
                list(flatten([c.get("source_assertion_ids") or [] for c in conflicts]))
            ),
            "selection_rules": self.card.selection_rules,
        }

    def context(self, selected):
        entities = self.card.entities()
        return {
            "scope": "whole_card_grouping_and_glossary_inputs",
            "relationships": [
                link for rid, link in self.links.items() if rid not in selected
            ],
            "entities": entities,
            "stored_identities": [
                {
                    "locator": {
                        "card_ref": self.pin,
                        "field_path": "entities",
                        "key": key,
                    },
                    "record": entities[key],
                    "basis": "stored_identity_record",
                    "source_assertion_membership": "not_recorded",
                }
                for key in sorted(self.card.entity_identities)
            ],
        }


RULE = "oligomer_explanation@3"
LEGACY_RULE = "oligomer_explanation@1"
SUBUNIT = "annotations.subunit"


def explain_oligomer(card, agreement_rule=AGREEMENT_RULE):
    if agreement_rule in (LEGACY_AGREEMENT_RULE, PREVIOUS_AGREEMENT_RULE):
        raise ValueError("This original quaternary verifier requires @3.")
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
