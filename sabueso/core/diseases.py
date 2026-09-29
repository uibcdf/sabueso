"""A protein's diseases, grouped across sources by stated identity (#90).

Diseases reach a protein card from several sources, each with its own ids:

- ``associated_with`` relationships: DISEASES (``doid:``), Open Targets (``mondo:``,
  ``efo:``) and Orphanet (``orphanet:ORPHA:``);
- UniProt's ``annotations.disease``, through the MIM id it states for each disease;
- ClinVar's ``annotations.clinical_variants``, through the ids each condition states.

``disease_statements`` lists them, each with the id it names. The ``disease_identity``
enrichment then asks MONDO which of those ids it states are the same disease, and
records each answer as a ``same_as`` relationship (id → ``mondo:<term>``), backed by a
MONDO SourceAssertion.

``diseases_view`` (``Card.diseases()``) groups the statements by MONDO term, under the
rule ``disease_grouping@1``:
- two statements are about one disease only when MONDO states that their ids are the
  same disease, or they name the same id;
- a statement whose id MONDO does not state as equivalent to any term stays apart
  (``ungrouped``), with the reason. It is never grouped by name;
- without the ``disease_identity`` enrichment, only statements naming the same MONDO
  id are grouped; every other stays apart with the reason ``identity_not_queried``.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from .relationship_store import make_derivation

RULE = "disease_grouping@1"


def disease_statements(
    get: Callable[[str], Any], relationships: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Every statement naming a disease: ``{ref, curie, source, kind, ...}``.

    ``get(path)`` returns a field's value; ``relationships`` are the card's."""
    from sabueso.tools.db.mondo import normalize

    out: List[Dict[str, Any]] = []
    for rel in relationships:
        if rel.get("predicate") != "associated_with":
            continue
        q = rel.get("qualifiers") or {}
        out.append(
            {
                "ref": rel["object_ref"],
                "curie": normalize(rel["object_ref"]),
                "source": q.get("source"),
                "kind": "association",
                "channel": q.get("channel"),
                "name": q.get("disease_name"),
                "relationship_id": rel.get("id"),
            }
        )
    for item in get("annotations.disease") or []:
        for xref in item.get("cross_references") or []:
            if xref.get("database") == "MIM" and xref.get("id"):
                out.append(
                    {
                        "ref": f"omim:{xref['id']}",
                        "curie": normalize(f"omim:{xref['id']}"),
                        "source": "UniProt",
                        "kind": "uniprot_disease",
                        "name": item.get("name"),
                        "accession": item.get("accession"),
                    }
                )
    for variant in get("annotations.clinical_variants") or []:
        for condition in variant.get("conditions") or []:
            for xref in condition.get("xrefs") or []:
                out.append(
                    {
                        "ref": xref,
                        "curie": normalize(xref),
                        "source": "ClinVar",
                        "kind": "clinvar_condition",
                        "name": condition.get("name"),
                        "variant": variant.get("accession"),
                    }
                )
    return [{k: v for k, v in s.items() if v is not None} for s in out]


def _card_statements(card: Any) -> List[Dict[str, Any]]:
    def get(path: str) -> Any:
        node = card.get(path)
        return node.get("value") if isinstance(node, dict) else None

    return disease_statements(get, card.relationships())


def diseases_view(card: Any) -> Dict[str, Any]:
    """The card's disease statements grouped by MONDO term; see the module docstring."""
    identity = {
        rel["subject_ref"]: rel
        for rel in card.relationships("same_as")
        if str(rel["object_ref"]).startswith("mondo:MONDO:")
    }
    queried = any(
        e.get("source") == "MONDO" for e in card.quality.get("enrichments") or []
    )
    unresolved = {
        u["curie"]: u["reason"]
        for e in card.quality.get("enrichments") or []
        if e.get("source") == "MONDO"
        for u in e.get("ungrouped") or []
    }
    groups: Dict[str, Dict[str, Any]] = {}
    ungrouped: List[Dict[str, Any]] = []
    for statement in _card_statements(card):
        curie = statement.get("curie")
        if curie and curie.startswith("MONDO:") and curie not in unresolved:
            mondo, basis = curie, "named_directly"
        elif curie in identity:
            mondo, basis = identity[curie]["object_ref"].split(":", 1)[1], "same_as"
        else:
            reason = (
                "identity_not_queried"
                if not queried
                else unresolved.get(curie or "", "no_stated_equivalence")
                if curie
                else "namespace_not_mapped"
            )
            ungrouped.append({**statement, "reason": reason})
            continue
        group = groups.setdefault(
            mondo, {"mondo": mondo, "names": set(), "refs": set(), "statements": []}
        )
        name = (identity.get(curie) or {}).get("qualifiers", {}).get("mondo_name")
        if name:
            group["mondo_name"] = name
        if statement.get("name"):
            group["names"].add(statement["name"])
        group["refs"].add(statement["ref"])
        group["statements"].append({**statement, "grouped_by": basis})
    diseases = []
    for mondo in sorted(groups):
        group = groups[mondo]
        diseases.append(
            {
                **group,
                "names": sorted(group["names"]),
                "refs": sorted(group["refs"]),
                "sources": sorted(
                    {s.get("source") for s in group["statements"]} - {None}
                ),
            }
        )
    return {
        "diseases": diseases,
        "ungrouped": ungrouped,
        "rule": make_derivation(
            RULE,
            inputs=[
                "relationships.associated_with",
                "annotations.disease",
                "annotations.clinical_variants",
                "relationships.same_as",
            ],
            parameters={"identity": "mondo_equivalence@1"},
        ),
    }
