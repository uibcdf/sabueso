"""Explain source-stated ligand crossings and stored site classifications (#91).

Whole-card fields/relationships remain context for the actual view. Protein and
molecule inputs retain distinct pins; deck snapshot locators are not invented
KnowledgeStore references. These readers fetch nothing and add no credit.
"""

from copy import deepcopy

from .bioactivities import CLASS_ORDER
from .bioactivity_explanation import _Support
from .ligand_sites import ANNOTATED_SITES, ligand_sites_view
from .ligands import ligands_view
from .relationship_store import make_derivation


def explain_ligand_site(card, ligand_site_ref):
    support = _Support(card)
    view = ligand_sites_view(card)
    item = next(
        (i for i in view["items"] if i["relationship_id"] == ligand_site_ref), None
    )
    fields = [support.field(path) for path in ANNOTATED_SITES.values()]
    for annotation in view["annotated_sites"]:
        if not annotation["source_assertion_id"]:
            support.gaps.append(
                {
                    "reason": "no_matching_annotation_assertion",
                    "annotation": annotation,
                    "card_ref": support.pin,
                }
            )
    return deepcopy(
        {
            "rule": make_derivation(
                "ligand_site_explanation@1",
                inputs=[support.pin],
                parameters={"ligand_site_ref": ligand_site_ref},
            ),
            "card_ref": support.pin,
            "ligand_site_ref": ligand_site_ref,
            "status": "not_on_card"
            if item is None
            else "partial"
            if support.gaps
            else "on_card",
            "item": item,
            "classification": view["classification"],
            "classification_inputs": {
                "numbering": (
                    (support.links.get(ligand_site_ref) or {}).get("relationship") or {}
                )
                .get("qualifiers", {})
                .get("numbering"),
                "annotated_site_count": len(view["annotated_sites"]),
                "annotated_sites": view["annotated_sites"],
                "fields": fields,
                "absence_basis": "stored annotated positions only; never external source absence",
            },
            "site": support.links.get(ligand_site_ref) if item else None,
            "context": {
                "scope": "whole_card_stored_inputs",
                "relationships": [
                    link
                    for rid, link in support.links.items()
                    if rid != ligand_site_ref
                ],
                "curated_engagements": view["curated_engagements"],
                "reports": [
                    {
                        "locator": {
                            "card_ref": support.pin,
                            "field_path": "quality.enrichments",
                            "index": i,
                        },
                        "record": record,
                    }
                    for i, record in enumerate(card.quality.get("enrichments") or [])
                ],
                "instance_basis": "stored has_structure ligand instances; aggregate residue chains never imply spanning",
            },
            "gaps": support.gaps,
        }
    )


def explain_ligand(card, molecule_ref, deck, include_indirect=False, thresholds=None):
    support = _Support(card)
    trace = {}
    view = ligands_view(card, deck, include_indirect, thresholds, _support=trace)
    members = [c for c in deck.cards if c.id == molecule_ref]
    gaps = list(support.gaps)
    if len(members) > 1:
        gaps.append(
            {
                "reason": "multiple_deck_members",
                "molecule_ref": molecule_ref,
                "card_refs": [c.pinned_ref() for c in members],
            }
        )
    explanations = []
    for decision in trace["decisions"]:
        if decision["item"]["molecule_ref"] != molecule_ref:
            continue
        molecule = deck.cards[decision["deck_index"]]
        molecular = _Support(molecule)
        name = molecular.field("names.canonical_name")
        bioactivities = [
            card.explain_bioactivity(
                ref, include_indirect=include_indirect, thresholds=thresholds
            )
            for ref in decision["measured_refs"]
        ]
        sites = [
            explain_ligand_site(card, ref) for ref in decision["site_relationship_ids"]
        ]
        for child in bioactivities + sites:
            gaps.extend(child["gaps"])
        gaps.extend(molecular.gaps)
        explanations.append(
            {
                "item": decision["item"],
                "molecule_card_ref": molecular.pin,
                "crossing_inputs": decision,
                "identity": {
                    "basis": "same_as relationships targeting this molecule card's anchor",
                    "links": [
                        link
                        for link in molecular.links.values()
                        if link["relationship"]["predicate"] == "same_as"
                    ],
                    "used_relationship_ids": [
                        rel["id"]
                        for rel in molecule.relationships("same_as")
                        if rel["subject_ref"] in decision["records"]
                        and rel["object_ref"] == molecule.id.split(":", 2)[-1]
                    ],
                },
                "name": name,
                "bioactivities": bioactivities,
                "sites": sites,
            }
        )
    snapshot = deck.snapshot_id()
    return deepcopy(
        {
            "rule": make_derivation(
                "ligand_deck_explanation@1",
                inputs=[support.pin, *[c.pinned_ref() for c in members]],
                parameters={
                    "molecule_ref": molecule_ref,
                    "deck_snapshot_id": snapshot,
                    "include_indirect": include_indirect,
                    "thresholds": {
                        name: view["classification"]["parameters"][name]
                        for name in ("active_max", "weak_max", "single_point_min")
                    },
                    "class_order": list(CLASS_ORDER),
                    "bioactivity_class": "strongest matched measured-molecule class",
                    "bioactivity_measurements": "included source records, as counted by the existing ligand view",
                },
            ),
            "card_ref": support.pin,
            "molecule_ref": molecule_ref,
            "status": "not_on_card"
            if not explanations
            else "partial"
            if gaps
            else "on_card",
            "reason": "not_in_deck"
            if not members
            else "no_stored_relation_to_protein"
            if not explanations
            else None,
            "items": explanations,
            "classification": view["classification"],
            "scope": view["scope"],
            "deck": {
                "snapshot_id": snapshot,
                "card_refs": [c.pinned_ref() for c in deck.cards],
                "membership": deck.explain(molecule_ref, skip_digestion=True),
                "meta": deck.meta,
                "locator_basis": "load the supplied or saved deck; snapshot id is not a KnowledgeStore deck reference",
            },
            "context": {**support.context(set()), "unmatched": view["unmatched"]},
            "gaps": gaps,
        }
    )
