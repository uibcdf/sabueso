"""Ligand sites of a protein crossed with its annotated sites (uibcdf/sabueso#28).

A ProteinCard can hold independent statements about where things bind:

- the functional sites UniProt annotates (``features_positional.active_site`` and
  ``binding_site``), each with its ECO evidence and, for binding sites, its ligand;
- the sites InterPro member databases place on the sequence from their family models
  (``features_positional.family_site``, e.g. CDD's catalytic triad, substrate binding site
  and dimer interface);
- the residues each ligand contacts in experimental structures, from PDBe-KB
  (``has_ligand_site`` relationships), in UniProt numbering.

``ligand_sites_view`` puts them side by side. Whether a ligand site overlaps an annotated
site is derived knowledge, computed here with rule ``annotated_site_overlap@3``: an exact
match of residue positions in UniProt numbering, against every annotated site. It is
never stored. Each overlap names the annotation and its source, because overlapping a
catalytic triad and overlapping a dimer interface mean different things.

Absence states stay distinct. "No annotated overlap" is not "binds elsewhere": UniProt
annotations are sparse (four residues for TIM), and a ligand can bind next to an annotated
residue without contacting it. When the card has no annotated site at all, the class says
so instead. Proximity over coordinates is not computed here; see uibcdf/sabueso#30.

Whether one ligand contacts more than one chain can only be read from **instance-level**
contacts. PDBe-KB aggregates all copies of a ligand, and its per-residue chains cannot
tell one ligand touching two chains from two copies in two chains. The card holds
per-instance contacts (from RCSB) only for the structures it has fetched, so
``spans_chains`` is ``None`` when no instance-level data is available, never ``[]``.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

# @1 compared UniProt sites; @2 adds family sites; @3 verifies coordinate scope.
SITE_OVERLAP_RULE = "annotated_site_overlap@3"
INSTANCE_RULE = "ligand_instance_scope@1"
ANNOTATION_SUPPORT_RULE = "annotated_site_source_support@1"
ANNOTATED_SITES = {
    "active_site": "features_positional.active_site",
    "binding_site": "features_positional.binding_site",
    "family_site": "features_positional.family_site",
}


def annotated_sites(card: Any, *, canonical=None) -> List[Dict[str, Any]]:
    """Every retained annotation, with explicit comparable/uncomputed scope."""
    from . import ligand_site_scope as scope

    canonical = scope.reference(card) if canonical is None else canonical
    out = []
    for kind, field_path in ANNOTATED_SITES.items():
        node = card.get(field_path)
        if node is None:
            continue
        values = node.get("value") if isinstance(node, dict) else None
        rows = list(enumerate(values)) if isinstance(values, list) else [(None, values)]
        for index, original in rows:
            value = original if isinstance(original, dict) else {}
            subject = canonical["sequence_ref"]
            if (
                subject is None
                and isinstance(card.id, str)
                and card.id.startswith("sabueso:protein:uniprot:")
            ):
                subject = card.id.removeprefix("sabueso:protein:")
            sources, problems = scope.matching(
                card, node, field_path, original, subject
            )
            context = scope.annotation(
                card, canonical, kind, field_path, index, original, sources, problems
            )
            context["field_source_assertion_ids"] = (
                deepcopy(node.get("source_assertion_ids"))
                if isinstance(node, dict)
                else None
            )
            if index is None:
                context.update(
                    status="not_computed",
                    reason="unrecognized_annotation_collection",
                    positions=None,
                )
            positions = context["positions"]
            for assertion in sources or [{}]:
                metadata = assertion.get("source_metadata")
                codes = metadata.get("eco") if isinstance(metadata, dict) else None
                out.append(
                    {
                        "kind": kind,
                        "start": positions[0] if positions else None,
                        "end": positions[-1] if positions else None,
                        "positions": deepcopy(positions),
                        "description": value.get("description") or None,
                        "ligand": deepcopy(value.get("ligand")),
                        "source": (assertion.get("source") or {}).get("name"),
                        "signature": value["signature"].get("accession")
                        if isinstance(value.get("signature"), dict)
                        else None,
                        "evidence": [
                            e.get("code") for e in codes if isinstance(e, dict)
                        ]
                        if isinstance(codes, list)
                        else [],
                        "source_assertion_id": assertion.get("id"),
                        "source_support_rule": ANNOTATION_SUPPORT_RULE,
                        "recorded_annotation": deepcopy(original),
                        "scope": deepcopy(context),
                    }
                )
    return sorted(
        out,
        key=lambda row: (
            row["start"] is None,
            row["start"] or 0,
            row["kind"],
            str(row["description"] or ""),
        ),
    )


def _positions(residues: List[Dict[str, Any]]) -> List[int]:
    return sorted(
        {p for r in residues for p in range(r["start"], (r["end"] or r["start"]) + 1)}
    )


def _structure_statements(card: Any, code: str) -> tuple:
    """PDB flags and per-instance contacts of this ligand in the card's structures."""
    flags: Dict[str, Any] = {}
    instances: List[Dict[str, Any]] = []
    relationships = set()
    for rel in card.relationships("has_structure"):
        for ligand in rel.get("qualifiers", {}).get("ligands") or []:
            if ligand.get("comp_id") != code:
                continue
            relationships.add(rel["id"])
            flags[rel["object_ref"]] = ligand.get("subject_of_investigation")
            for instance in ligand.get("instances") or []:
                instances.append(
                    {
                        "structure_ref": rel["object_ref"],
                        "relationship_id": rel["id"],
                        "sequence_ref": rel["subject_ref"],
                        "asym_id": instance.get("asym_id"),
                        "chains": deepcopy(instance.get("chains") or []),
                        "chain_scope": "recorded"
                        if instance.get("chains")
                        and all(
                            isinstance(chain, str) and chain
                            for chain in instance["chains"]
                        )
                        else "unknown",
                        "positions": sorted(
                            {
                                c["position"]
                                for c in instance.get("contacts") or []
                                if c.get("position") is not None
                                and f"uniprot:{c.get('uniprot')}" == rel["subject_ref"]
                            }
                        ),
                        "unplaced_contacts": deepcopy(
                            [
                                c
                                for c in instance.get("contacts") or []
                                if c.get("position") is None
                                or f"uniprot:{c.get('uniprot')}" != rel["subject_ref"]
                            ]
                        ),
                    }
                )
    instances.sort(key=lambda i: (i["structure_ref"], str(i["asym_id"])))
    return dict(sorted(flags.items())), instances, sorted(relationships)


def site_overlap_derivation() -> Dict[str, Any]:
    from .ligand_site_scope import RULE as SCOPE_RULE
    from .relationship_store import make_derivation

    return make_derivation(
        SITE_OVERLAP_RULE,
        inputs=[
            "has_ligand_site.residues",
            "has_ligand_site.numbering",
            "has_ligand_site.subject_ref",
            "identifiers.uniprot",
            "sequence.primary",
            "sequence.length",
            "source_assertion_store",
            "quality.conflicts",
            ANNOTATED_SITES["active_site"],
            ANNOTATED_SITES["binding_site"],
            ANNOTATED_SITES["family_site"],
        ],
        parameters={
            "match": "exact declared canonical residue position",
            "numbering": "uniprot",
            "coordinate_scope_rule": SCOPE_RULE,
            "uncomputed": "not a negative overlap; partial positives remain explicit",
            "revision_agreement": "not inferred when unstated",
        },
    )


def _chain_spans(instances):
    """ligand_instance_scope@1: unidentified occurrences cannot prove a span."""
    identified = [
        i
        for i in instances
        if isinstance(i.get("asym_id"), str)
        and i["asym_id"]
        and i.get("chains")
        and i.get("chain_scope", "recorded") == "recorded"
    ]
    spans = sorted({i["structure_ref"] for i in identified if len(i["chains"]) > 1})
    return spans if spans or instances and len(identified) == len(instances) else None


def ligand_sites_view(card: Any) -> Dict[str, Any]:
    """Each ligand site of the card next to the card's annotated sites.

    Returns ``{"items", "curated_engagements", "annotated_sites", "classification"}``. Each item holds the
    ligand, its contacted positions (PDBe-KB, over all structures), the per-instance
    contacts of the structures the card holds (RCSB) and the structures where one
    instance contacts more than one chain, the relevance statements of both sources
    (PDBe-KB ``is_solvent`` and ``significance``; the PDB ``subject_of_investigation``
    flag), and the annotated sites its positions overlap.
    """
    from . import ligand_site_scope as scope

    canonical = scope.reference(card)
    annotated = annotated_sites(card, canonical=canonical)
    uncomputed = [
        index
        for index, site in enumerate(annotated)
        if site["scope"]["status"] != "comparable"
    ]
    items: List[Dict[str, Any]] = []
    for rel in card.relationships("has_ligand_site"):
        original_qualifiers = rel.get("qualifiers")
        q = original_qualifiers if isinstance(original_qualifiers, dict) else {}
        contact_scope = scope.contact(card, canonical, rel)
        positions = contact_scope["positions"]
        code = rel["object_ref"].split(":", 1)[1]
        flags, instances, structure_relationships = _structure_statements(card, code)
        overlap = [
            {**site, "matched": sorted(set(site["positions"]) & set(positions))}
            for site in annotated
            if site["scope"]["status"] == "comparable"
            and positions is not None
            and set(site["positions"]) & set(positions)
        ]
        if q.get("numbering") != "uniprot":
            site_class, status = "numbering_not_comparable", "not_computed"
        elif not annotated:
            site_class, status = "no_annotated_sites", "not_computed"
        elif contact_scope["status"] != "comparable":
            site_class, status = "comparison_not_computed", "not_computed"
        elif overlap:
            site_class, status = (
                "overlaps_annotated_site",
                "partial" if uncomputed else "computed",
            )
        elif uncomputed:
            site_class, status = "comparison_not_computed", "not_computed"
        else:
            site_class, status = "no_annotated_overlap", "computed"
        if status == "not_computed":
            overlap = []
        items.append(
            {
                "ligand_ref": rel["object_ref"],
                "name": q.get("ligand_name"),
                "positions": positions,
                "residues": [
                    {"position": r["start"], "residue": r.get("residue")}
                    for r in q.get("residues") or []
                ]
                if positions is not None
                else None,
                "recorded_residues": deepcopy(q.get("residues")),
                "comparison": {
                    "rule": SITE_OVERLAP_RULE,
                    "status": status,
                    "basis": "source-declared canonical numbering, not atom completeness or revision agreement",
                    "contact_scope": contact_scope,
                    "uncomputed_annotation_indices": uncomputed,
                    "compared_annotation_indices": [
                        index
                        for index, site in enumerate(annotated)
                        if contact_scope["status"] == "comparable"
                        and site["scope"]["status"] == "comparable"
                    ],
                },
                "structures": q.get("structures") or [],
                "instances": instances,
                "spans_chains": _chain_spans(instances),
                "instance_rule": INSTANCE_RULE,
                "is_solvent": q.get("is_solvent"),
                "significance": q.get("significance"),
                "subject_of_investigation": flags,
                "structure_support": {
                    "basis": "relationship_level",
                    "relationship_ids": structure_relationships,
                },
                "annotated_overlap": [
                    {
                        k: site[k]
                        for k in (
                            "kind",
                            "start",
                            "end",
                            "description",
                            "source",
                            "signature",
                            "matched",
                            "source_assertion_id",
                            "scope",
                        )
                    }
                    for site in overlap
                ],
                "site_class": site_class,
                "relationship_id": rel["id"],
            }
        )
    items.sort(key=lambda i: i["ligand_ref"])
    # What papers state about how compounds act on residues (#61), next to what the
    # structures show; each keeps its source.
    curated = [
        {
            "molecule_ref": (rel.get("qualifiers") or {}).get("molecule_ref"),
            "ligand_ref": rel["object_ref"],
            "positions": [
                r["position"] for r in rel["qualifiers"].get("residues") or []
            ],
            "residues": rel["qualifiers"].get("residues"),
            "mechanism": rel["qualifiers"].get("mechanism"),
            "covalent_residue": rel["qualifiers"].get("covalent_residue"),
            "method": rel["qualifiers"].get("method"),
            "publication": rel["qualifiers"].get("publication"),
            "relationship_id": rel["id"],
        }
        for rel in card.relationships("engages")
    ]
    return {
        "items": items,
        "curated_engagements": sorted(
            curated, key=lambda c: (c["ligand_ref"], c["relationship_id"])
        ),
        "annotated_sites": annotated,
        "classification": site_overlap_derivation(),
        "canonical_reference": canonical,
    }
