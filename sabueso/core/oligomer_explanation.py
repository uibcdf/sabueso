"""Pinned inputs of the existing oligomer and interface rules (#91).

Relationship support is retained at its recorded granularity. Assembly methods
and family signatures are source declarations, never local executions. A reader
cannot recover original runtime credit or per-qualifier mapping lineage.
"""

from copy import deepcopy

from .bioactivity_explanation import _Support
from .oligomer import (
    AGREEMENT_RULE,
    PARTNER_RULE,
    _family_inputs,
    oligomer_view,
)
from .relationship_store import make_derivation
from .structures import coverage_derivation

LEGACY_RULE = "oligomer_explanation@1"
RULE = "oligomer_explanation@2"
SUBUNIT = "annotations.subunit"
FAMILY = "features_positional.family_site"


def explain_oligomer(card, agreement_rule=AGREEMENT_RULE):
    support = _Support(card, predicates={"has_structure", "has_interface_with"})
    pin = support.pin
    view = oligomer_view(card, agreement_rule)
    fields = {path: support.field(path) for path in (SUBUNIT, FAMILY)}
    subject = card.id.replace("sabueso:protein:", "", 1)

    def matched(path, value):
        selected = fields[path].get("source_assertions") or []
        rows = [
            row
            for row in selected
            if row["found"] and row.get("asserted_value") == value
        ]
        if not rows:
            support.gaps.append(
                {
                    "reason": "no_matching_annotation_assertion",
                    "field_path": path,
                    "card_ref": pin,
                    "value": value,
                }
            )
        return rows

    # Selection alternatives remain context, rather than support for the winner.
    for path, field in fields.items():
        alternatives = [
            row
            for row in card.quality.get("alternatives") or []
            if row.get("field") == path
        ]
        field["selection_alternatives"] = alternatives

        def ids(groups):
            for group in groups:
                if isinstance(group, str):
                    yield group
                else:
                    yield from ids(group)

        field["alternative_source_assertions"] = support.assertions(
            list(ids([r.get("source_assertion_ids") or [] for r in alternatives]))
        )

    subunit = [
        {
            "item": item,
            "locator": {"card_ref": pin, "field_path": SUBUNIT, "index": i},
            "source_assertions": matched(SUBUNIT, item["text"]),
        }
        for i, item in enumerate(view["subunit"])
    ]
    structures = {}
    for rel in card.relationships("has_structure"):
        link = support.links[rel["id"]]
        q = rel.get("qualifiers") or {}
        structures[rel["object_ref"]] = {
            **link,
            "support_basis": "relationship",
            "qualifier_lineage": "not_recorded",
            "assembly_state": "not_stated_on_card"
            if q.get("assemblies") is None
            else "stated_empty"
            if not q["assemblies"]
            else "stated",
            "coverage_rule": coverage_derivation(),
        }

    interfaces = []
    for item in view["interfaces"]:
        link = support.links[item["relationship_id"]]
        q = link["relationship"].get("qualifiers") or {}
        inputs = []
        for ref, basis in item["basis"].items():
            structure = structures.get(ref)
            if structure is None:
                support.gaps.append(
                    {
                        "reason": "structure_not_on_card",
                        "card_ref": pin,
                        "structure_ref": ref,
                    }
                )
            inputs.append(
                {
                    "structure_ref": ref,
                    "basis": basis,
                    "relationship_ref": structure["relationship_ref"]
                    if structure
                    else None,
                }
            )
        interfaces.append(
            {
                "item": item,
                "interface": {
                    **link,
                    "support_basis": "relationship",
                    "qualifier_lineage": "not_recorded",
                },
                "classification_inputs": {
                    "rule": PARTNER_RULE,
                    "subject_ref": subject,
                    "subject_locator": {"card_ref": pin, "field_path": "meta.card_id"},
                    "identity_basis": "exact_native_reference_equality"
                    if item["partner_ref"] == subject
                    else "distinct_native_references",
                    "structures": inputs,
                    "numbering": q.get("numbering"),
                    "residue_scope": "source_aggregate_across_structures",
                },
            }
        )

    # Keep the exact original member, including sequence indexing/signature data.
    members = _family_inputs(card)
    family = [
        {
            "item": item,
            "locator": {"card_ref": pin, "field_path": FAMILY, "index": member[2]},
            "value": member[3],
            "source_assertions": matched(FAMILY, member[3]),
        }
        for item, member in zip(view["family_interface_sites"], members)
    ]
    homomeric = next(
        (row for row in interfaces if row["item"]["class"] == "homomeric"), None
    )
    agreement = []
    for item, site in zip(view["agreement"], family):
        sequence = (site["value"].get("location") or {}).get("sequence") or {}
        numbering = homomeric["classification_inputs"]["numbering"]
        comparable = (
            numbering == "uniprot"
            and subject.startswith("uniprot:")
            and sequence.get("sequence_id") == f"UniProt:{subject.split(':', 1)[1]}"
            and sequence.get("indexing") == "1-based"
        )
        if agreement_rule == AGREEMENT_RULE:
            comparable = item["comparison"]["status"] == "comparable"
        if not comparable:
            support.gaps.append(
                {
                    "reason": "agreement_numbering_not_confirmed",
                    "interface_ref": homomeric["interface"]["relationship_ref"],
                    "family_site_locator": site["locator"],
                }
            )
        agreement.append(
            {
                "item": item,
                "rule": agreement_rule,
                "observed_interface_ref": homomeric["interface"]["relationship_ref"],
                "family_site_locator": site["locator"],
                "selection_basis": "first_homomeric_interface_in_native_view",
                "numbering": numbering,
                "family_sequence": sequence,
                "numbering_confirmed": comparable,
                "comparison_basis": f"exact_integer_positions_as_used_by_{agreement_rule}",
                **(
                    {"comparison": item["comparison"]}
                    if agreement_rule == AGREEMENT_RULE
                    else {}
                ),
            }
        )
    reports = [
        {
            "locator": {
                "card_ref": pin,
                "field_path": "quality.enrichments",
                "index": i,
            },
            "record": record,
        }
        for i, record in enumerate(card.quality.get("enrichments") or [])
        if record.get("source") in {"UniProt", "RCSB PDB", "PDBe-KB", "InterPro"}
    ]
    stored = bool(support.links or any(field["stored"] for field in fields.values()))
    return deepcopy(
        {
            "rule": make_derivation(
                RULE if agreement_rule == AGREEMENT_RULE else LEGACY_RULE,
                inputs=[pin],
                parameters={"agreement_rule": agreement_rule}
                if agreement_rule == AGREEMENT_RULE
                else None,
            ),
            "card_ref": pin,
            "status": "partial"
            if support.gaps
            else "on_card"
            if stored
            else "not_on_card",
            "view": view,
            "fields": list(fields.values()),
            "subunit": subunit,
            "structures": [structures[ref] for ref in sorted(structures)],
            "interfaces": interfaces,
            "family_interface_sites": family,
            "agreement": agreement,
            "context": {
                "reports": reports,
                "report_membership": "source_context_not_per_assertion_membership",
                "absence_basis": "stored_inputs_only_never_external_absence",
                "runtime_attribution": "not_reconstructed_from_scientific_payload",
                "method_basis": "source_declarations_never_local_execution",
            },
            "gaps": support.gaps,
        }
    )
