"""UniRef clusters → a protein card's sequence clusters and related entries (#103).

UniProt places every entry in a UniRef100, a UniRef90 and a UniRef50 cluster. They are
UniProt's statements of sequence similarity, never identity: Sabueso does not merge an
entry with the members of its clusters, which may be other strains or species.

It states:

- ``identifiers.uniref``: ``{uniref100, uniref90, uniref50}``, the clusters' ids;
- ``clustered_with``: one relationship to each other member of the entry's UniRef90
  cluster, ``uniprot:<accession>`` for a UniProtKB entry, ``uniparc:<UPI>`` for a
  sequence without one. Qualifiers: ``cluster`` and ``identity_level`` (0.9), the
  member's ``member_id`` (entry name or UPI), ``organism``, ``taxon_id``,
  ``sequence_length``, its ``uniref100`` cluster, and ``same_uniref100``, whether it is
  the card's UniRef100 cluster (an identical sequence, or a fragment of it).

A genome-strain entry and the reference entry of the same protein meet here: TcTIM's
P52270 and *T. cruzi* CL Brener's Q4DV43 are in UniRef90_P52270, in different UniRef100
clusters.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "UniProt"
FIELD = "identifiers.uniref"
PREDICATE = "clustered_with"
LEVELS = {"UniRef100": "uniref100", "UniRef90": "uniref90", "UniRef50": "uniref50"}


def cluster_ids(clusters: List[Dict[str, Any]]) -> Dict[str, str]:
    """``{uniref100, uniref90, uniref50}`` from UniProt's answer."""
    out = {}
    for cluster in clusters:
        key = LEVELS.get(str(cluster.get("level")))
        if key and cluster.get("id"):
            out[key] = cluster["id"]
    return out


def member_ref(member: Dict[str, Any]) -> str | None:
    accessions = member.get("accessions") or []
    if accessions:
        return f"uniprot:{accessions[0]}"
    if member.get("memberIdType") == "UniParc" and member.get("memberId"):
        return f"uniparc:{member['memberId']}"
    return None


def map_uniref(
    clusters: List[Dict[str, Any]],
    members: List[Dict[str, Any]],
    accession: str,
    retrieved_at: str,
    version: str | None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    ids = cluster_ids(clusters)
    assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    fields: Dict[str, Any] = {}

    def stated(path: str, value: Any, reference: str) -> Dict[str, Any]:
        made = make_source_assertion(
            path,
            value,
            SOURCE,
            reference,
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        if version:
            made["source"]["version"] = str(version)
        assertions.append(made)
        return made

    if ids:
        fields[FIELD] = ids
        stated(FIELD, ids, f"uniref:{accession}")
    anchor = f"uniprot:{accession}"
    for member in members:
        target = member_ref(member)
        if target is None or target == anchor:
            continue
        if accession in (member.get("accessions") or []):
            continue
        qualifiers = {
            "cluster": ids.get("uniref90"),
            "identity_level": 0.9,
            "member_id": member.get("memberId"),
            "organism": member.get("organismName"),
            "taxon_id": member.get("organismTaxId"),
            "sequence_length": member.get("sequenceLength"),
            "uniref100": member.get("uniref100Id"),
            "same_uniref100": member.get("uniref100Id") == ids.get("uniref100")
            if member.get("uniref100Id")
            else None,
        }
        qualifiers = {k: v for k, v in qualifiers.items() if v is not None}
        made = stated(
            f"relationships.{PREDICATE}",
            {"object_ref": target, **qualifiers},
            f"{ids.get('uniref90')}:{member.get('memberId')}",
        )
        relationships.append(
            make_relationship(
                anchor,
                PREDICATE,
                target,
                qualifiers=qualifiers,
                source_assertion_ids=[made["id"]],
            )
        )
    mapping = {
        "fields": fields,
        "field_source_assertions": {FIELD: [assertions[0]["id"]]} if ids else {},
        "source_assertions": assertions,
        "relationships": relationships,
    }
    return mapping, {
        "clusters": ids,
        "count": len(relationships),
        "uniprot_members": sum(
            1 for r in relationships if r["object_ref"].startswith("uniprot:")
        ),
        "uniparc_members": sum(
            1 for r in relationships if r["object_ref"].startswith("uniparc:")
        ),
    }
