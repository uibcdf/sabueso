"""What sources state about a protein's quaternary structure (uibcdf/sabueso#40).

``oligomer_view`` puts side by side, each with its source:

- UniProt's ``SUBUNIT`` statements (``annotations.subunit``), with their evidence;
- the biological assemblies of each experimental structure the card has fetched from
  RCSB: oligomeric state and stoichiometry, and who defined the assembly (author,
  software such as PISA, or both);
- the interface residues PDBe-KB reports per partner chain (``has_interface_with``), in
  UniProt numbering;
- the interface sites a family model places on the sequence
  (``features_positional.family_site``, e.g. CDD's dimer interface).

Two derived judgements, never stored:

- ``interface_partner_class@1`` says what kind of partner each PDBe-KB interface is:

  - ``homomeric``: another copy of the protein itself;
  - ``heteromeric``: observed in at least one structure where the protein is not a
    fragment and its chains are not a chimera with that partner;
  - ``chimera``: observed only in entries whose polymer entity maps to both proteins, so
    the "partner" is the protein itself. 3Q37, a TcTIM/TbTIM chimera, makes TbTIM look
    like a partner of TcTIM;
  - ``fragment_complex``: observed only where the protein is a fragment or peptide, for
    example a TIM peptide presented by HLA-DR;
  - ``chimera_or_fragment``: both of the above, and nothing else;
  - ``undetermined``: some of its structures are not on the card with the data needed.

  The basis is given per structure.
- ``interface_site_agreement@2`` compares exact positions only with confirmed
  UniProt numbering, matching family sequence identity and 1-based indexing.
  Unknown/incompatible context is reported without computed residue sets.
  Explicit ``@1`` reproduces the historical integer-only comparison (#120).

Interfaces are not computed from coordinates here; that is modelling (uibcdf/sabueso#30).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .ligand_sites import _positions as site_positions
from .ligand_sites import annotated_sites
from .structures import coverage_class

PARTNER_RULE = "interface_partner_class@1"
LEGACY_AGREEMENT_RULE = "interface_site_agreement@1"
AGREEMENT_RULE = "interface_site_agreement@2"
INTERFACE_SITE = re.compile(r"\binterface\b", re.IGNORECASE)


def _positions(residues: List[Dict[str, Any]]) -> List[int]:
    return sorted(
        {
            p
            for r in residues
            if r.get("start") is not None
            for p in range(r["start"], (r.get("end") or r["start"]) + 1)
        }
    )


def _source_names(card: Any, rel: Dict[str, Any]) -> List[str]:
    return sorted(
        {
            card.source_assertion_store.get(sa)["source"]["name"]
            for sa in rel.get("source_assertion_ids", [])
            if card.source_assertion_store.get(sa)
        }
    )


def _subunit(card: Any) -> List[Dict[str, Any]]:
    node = card.get("annotations.subunit") or {}
    assertions = [
        card.source_assertion_store.get(i)
        for i in node.get("source_assertion_ids") or []
    ]
    out = []
    for text in node.get("value") or []:
        assertion = next(
            (a for a in assertions if a and a.get("asserted_value") == text), {}
        )
        out.append(
            {
                "text": text,
                "source": (assertion.get("source") or {}).get("name"),
                "evidence": (assertion.get("source_metadata") or {}).get("eco") or [],
                "source_assertion_id": assertion.get("id"),
            }
        )
    return out


def _structure_basis(structure: Dict[str, Any] | None, partner: str) -> str:
    """Why one structure does or does not show a complex with ``partner``."""
    if structure is None:
        return "structure_not_on_card"
    q = structure.get("qualifiers", {})
    if partner in (q.get("chimeric_with") or []):
        return "chimera_with_partner"
    if coverage_class(q.get("coverage")) == "fragment_or_peptide":
        return "protein_as_fragment"
    if "chimeric_with" not in q:
        return "entity_mapping_not_retrieved"  # RCSB data not fetched for it
    return "complex_with_partner"


def _partner_class(subject: str, partner_ref: str, basis: Dict[str, str]) -> str:
    if partner_ref == subject:
        return "homomeric"
    reasons = set(basis.values())
    if "complex_with_partner" in reasons:
        return "heteromeric"
    if reasons & {"structure_not_on_card", "entity_mapping_not_retrieved"} or not (
        reasons
    ):
        return "undetermined"
    if reasons == {"chimera_with_partner"}:
        return "chimera"
    if reasons == {"protein_as_fragment"}:
        return "fragment_complex"
    return "chimera_or_fragment"


def _family_positions(value):
    sequence = (value.get("location") or {}).get("sequence") or {}
    spans = sequence.get("fragments") or (
        [{"start": sequence["start"], "end": sequence.get("end")}]
        if sequence.get("start") is not None
        else []
    )
    return site_positions(spans)


def _family_inputs(card):
    """Original field/index members in the native family-interface view order."""
    members = []
    for index, value in enumerate(
        (card.get("features_positional.family_site") or {}).get("value") or []
    ):
        positions = _family_positions(value)
        if positions and INTERFACE_SITE.search(value.get("description") or ""):
            members.append((positions[0], value.get("description") or "", index, value))
    return sorted(members, key=lambda member: member[:2])


def agreement_context(subject, interface, family_value):
    """Read native numbering declarations; never infer a residue correspondence."""
    q = interface.get("qualifiers") or {}
    sequence = (family_value.get("location") or {}).get("sequence") or {}
    missing, incompatible = [], []
    numbering = q.get("numbering")
    if not numbering:
        missing.append("interface_numbering_not_stated")
    elif numbering != "uniprot":
        incompatible.append("interface_numbering_not_uniprot")
    if not interface.get("subject_ref"):
        missing.append("interface_subject_not_stated")
    elif interface["subject_ref"] != subject:
        incompatible.append("interface_subject_not_card_subject")
    if not subject.startswith("uniprot:"):
        missing.append("card_subject_not_uniprot")
    if not sequence.get("sequence_id"):
        missing.append("family_sequence_id_not_stated")
    elif subject.startswith("uniprot:") and sequence["sequence_id"] != (
        f"UniProt:{subject.split(':', 1)[1]}"
    ):
        incompatible.append("family_sequence_not_card_subject")
    if not sequence.get("indexing"):
        missing.append("family_indexing_not_stated")
    elif sequence["indexing"] != "1-based":
        incompatible.append("family_indexing_not_1_based")
    if q.get("residues") is None:
        missing.append("interface_residues_not_stated")
    elif any(row.get("start") is None for row in q["residues"]):
        missing.append("interface_residue_positions_not_stated")
    if any(position < 1 for position in _positions(q.get("residues") or [])):
        incompatible.append("interface_positions_not_1_based")
    if any(position < 1 for position in _family_positions(family_value)):
        incompatible.append("family_positions_not_1_based")
    for key in ("numbering", "residues"):
        if (interface.get("qualifier_conflicts") or {}).get(key):
            missing.append(f"interface_{key}_conflicted")
    return {
        "status": "not_comparable"
        if incompatible
        else "undetermined"
        if missing
        else "comparable",
        "reasons": incompatible + missing,
        "interface_numbering": numbering,
        "interface_subject_ref": interface.get("subject_ref"),
        "family_sequence": sequence,
    }


def oligomer_derivations(agreement_rule=AGREEMENT_RULE) -> List[Dict[str, Any]]:
    from .relationship_store import make_derivation

    return [
        make_derivation(
            PARTNER_RULE,
            inputs=[
                "has_interface_with.structures",
                "has_structure.chimeric_with",
                "has_structure.coverage",
            ],
            parameters={
                "classes": [
                    "homomeric",
                    "heteromeric",
                    "chimera",
                    "fragment_complex",
                    "chimera_or_fragment",
                    "undetermined",
                ],
                "fragment": "structure_coverage_class@1 fragment_or_peptide",
            },
        ),
        make_derivation(
            agreement_rule,
            inputs=["has_interface_with.residues", "features_positional.family_site"]
            + (
                [
                    "has_interface_with.numbering",
                    "has_interface_with.subject_ref",
                    "meta.card_id",
                    "has_interface_with.qualifier_conflicts",
                ]
                if agreement_rule == AGREEMENT_RULE
                else []
            ),
            parameters={"match": "exact residue position", "numbering": "uniprot"}
            | (
                {
                    "family_sequence": "exact card UniProt reference",
                    "indexing": "1-based",
                    "unconfirmed": "no computed residue sets",
                }
                if agreement_rule == AGREEMENT_RULE
                else {}
            ),
        ),
    ]


def oligomer_view(card: Any, agreement_rule=AGREEMENT_RULE) -> Dict[str, Any]:
    """``{"subunit", "assemblies", "without_assembly_data", "interfaces",
    "family_interface_sites", "agreement", "rules"}`` for a protein card."""
    subject = card.meta.get("card_id", "").replace("sabueso:protein:", "", 1)
    structures = {r["object_ref"]: r for r in card.relationships("has_structure")}

    assemblies, without = [], []
    for ref, rel in sorted(structures.items()):
        stated = rel.get("qualifiers", {}).get("assemblies")
        if stated is None:
            without.append(ref)
        else:
            assemblies.append({"structure_ref": ref, "assemblies": stated})

    interfaces = []
    for rel in card.relationships("has_interface_with"):
        q = rel.get("qualifiers", {})
        partner = rel["object_ref"]
        partner_accession = partner.split(":", 1)[1]
        basis = {
            s: _structure_basis(structures.get(s), partner_accession)
            for s in q.get("structures") or []
        }
        interfaces.append(
            {
                "partner_ref": partner,
                "partner_name": q.get("partner_name"),
                "partner_type": q.get("partner_type"),
                "class": _partner_class(subject, partner, basis),
                "basis": dict(sorted(basis.items())),
                "positions": _positions(q.get("residues") or []),
                "structures": q.get("structures") or [],
                "sources": _source_names(card, rel),
                "relationship_id": rel["id"],
            }
        )
    order = ["homomeric", "heteromeric", "undetermined"]
    interfaces.sort(
        key=lambda i: (
            order.index(i["class"]) if i["class"] in order else len(order),
            -len(i["positions"]),
            i["partner_ref"],
        )
    )

    family = [
        s
        for s in annotated_sites(card)
        if s["kind"] == "family_site" and INTERFACE_SITE.search(s["description"] or "")
    ]
    homomeric = next((i for i in interfaces if i["class"] == "homomeric"), None)
    agreement = []
    members = _family_inputs(card) if agreement_rule == AGREEMENT_RULE else []
    if homomeric:
        observed = set(homomeric["positions"])
        for index, site in enumerate(family):
            annotated = set(site["positions"])
            context = (
                agreement_context(
                    subject,
                    card.relationship_store.get(homomeric["relationship_id"]),
                    members[index][3],
                )
                if agreement_rule == AGREEMENT_RULE
                else None
            )
            comparable = context is None or context["status"] == "comparable"
            agreement.append(
                {
                    "family_site": site["description"],
                    "signature": site["signature"],
                    "source": site["source"],
                    "both": sorted(annotated & observed) if comparable else None,
                    "family_only": sorted(annotated - observed) if comparable else None,
                    "observed_only": sorted(observed - annotated)
                    if comparable
                    else None,
                    **({"comparison": context} if context is not None else {}),
                }
            )

    return {
        "subunit": _subunit(card),
        "assemblies": assemblies,
        "without_assembly_data": without,
        "interfaces": interfaces,
        "family_interface_sites": family,
        "agreement": agreement,
        "rules": oligomer_derivations(agreement_rule),
        **(
            {
                "agreement_state": {
                    "status": "not_computed"
                    if not agreement
                    else "computed"
                    if all(
                        row["comparison"]["status"] == "comparable" for row in agreement
                    )
                    else "partial"
                    if any(
                        row["comparison"]["status"] == "comparable" for row in agreement
                    )
                    else "not_computed",
                    "reasons": (
                        ["no_homomeric_interface_on_card"] if homomeric is None else []
                    )
                    + (["no_family_interface_site_on_card"] if not family else [])
                    + (
                        ["no_comparable_interface_sites_on_card"]
                        if agreement
                        and not any(
                            row["comparison"]["status"] == "comparable"
                            for row in agreement
                        )
                        else []
                    ),
                }
            }
            if agreement_rule == AGREEMENT_RULE
            else {}
        ),
    }
