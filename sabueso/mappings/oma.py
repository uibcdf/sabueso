"""OMA orthologs → ``ortholog_of`` relationships of a protein card (#83).

**The query joins only through an exact match OMA states.** OMA maps a UniProt
accession to one of its proteins, sometimes of another strain or assembly, and says
whether its sequence is the accession's (``seq_match``: ``exact`` or ``modified``). The
card's protein takes OMA's orthologs only when OMA states the accession with
``seq_match`` ``exact`` (``joined``); otherwise nothing is joined, and the record says
which OMA protein the accession was mapped to (TcTIM P52270 maps to T. cruzi CL
Brener's Q4DV43, whose sequence differs).

**Each ortholog is named by the identifier its source states:**

- ``uniprot:<accession>`` when OMA's canonical id is a UniProt accession;
- ``uniprot:<accession>`` when it is a Swiss-Prot entry name UniProt states the
  accession of (``TPIS_HUMAN`` → P60174), with the name kept;
- ``oma:<OMA id>`` otherwise (a GenBank protein, or a name UniProt no longer has).

Each ``ortholog_of`` relationship keeps OMA's relation type (``1:1``, ``1:n``, ``m:1``,
``m:n``), the ortholog's species and taxon, its OMA id, OMA group and hierarchical
orthologous group, its canonical id, and OMA's evolutionary distance and alignment
score, as stated. Orthology is OMA's inference; it is recorded as OMA's statement.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "OMA"
FIELD = "relationships.ortholog_of"
ACCESSION = re.compile(
    r"^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})$"
)
ENTRY_NAME = re.compile(r"^[A-Z0-9]{1,10}_[A-Z0-9]{1,5}$")


def joined(xrefs: List[Dict[str, Any]], accession: str) -> Dict[str, Any] | None:
    """OMA's UniProt cross-reference of ``accession`` with an exact sequence match, or
    None."""
    for xref in xrefs:
        if (
            xref.get("xref") == accession
            and str(xref.get("source", "")).startswith("UniProtKB")
            and xref.get("seq_match") == "exact"
        ):
            return xref
    return None


def mapped_to(xrefs: List[Dict[str, Any]], accession: str) -> Dict[str, Any]:
    """Which OMA protein the accession was mapped to, and how its sequence matched."""
    for xref in xrefs:
        if xref.get("xref") == accession:
            return {
                "oma_id": xref.get("omaid"),
                "seq_match": xref.get("seq_match"),
                "source": xref.get("source"),
            }
    return {}


def names_of(orthologs: List[Dict[str, Any]]) -> List[str]:
    """The Swiss-Prot entry names among the orthologs' canonical ids."""
    return sorted(
        {
            o["canonicalid"]
            for o in orthologs
            if o.get("canonicalid")
            and not ACCESSION.match(o["canonicalid"])
            and ENTRY_NAME.match(o["canonicalid"])
        }
    )


def ortholog_ref(ortholog: Dict[str, Any], accessions: Dict[str, str]) -> str:
    canonical = ortholog.get("canonicalid") or ""
    if ACCESSION.match(canonical):
        return f"uniprot:{canonical}"
    if canonical in accessions:
        return f"uniprot:{accessions[canonical]}"
    return f"oma:{ortholog.get('omaid')}"


def map_orthologs(
    orthologs: List[Dict[str, Any]],
    accessions: Dict[str, str],
    accession: str,
    retrieved_at: str,
    limit: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """``orthologs`` as OMA states them, already filtered by the options."""
    wanted = orthologs
    kept = wanted[:limit]
    assertions, relationships = [], []
    for ortholog in kept:
        species = ortholog.get("species") or {}
        qualifiers = {
            "rel_type": ortholog.get("rel_type"),
            "species": species.get("species"),
            "taxon_id": species.get("taxon_id"),
            "oma_id": ortholog.get("omaid"),
            "oma_group": ortholog.get("oma_group") or None,
            "oma_hog_id": ortholog.get("oma_hog_id"),
            "canonical_id": ortholog.get("canonicalid"),
            "distance": ortholog.get("distance"),
            "score": ortholog.get("score"),
        }
        qualifiers = {k: v for k, v in qualifiers.items() if v not in (None, "")}
        target = ortholog_ref(ortholog, accessions)
        stated = make_source_assertion(
            FIELD,
            {"object_ref": target, **qualifiers},
            SOURCE,
            f"{accession}:{ortholog.get('omaid')}",
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        assertions.append(stated)
        relationships.append(
            make_relationship(
                f"uniprot:{accession}",
                "ortholog_of",
                target,
                qualifiers=qualifiers,
                source_assertion_ids=[stated["id"]],
            )
        )
    mapping = {
        "fields": {},
        "field_source_assertions": {},
        "source_assertions": assertions,
        "relationships": relationships,
    }
    by_ref = [r["object_ref"] for r in relationships]
    return mapping, {
        "count": len(kept),
        "total_count": len(wanted),
        "truncated": len(wanted) > len(kept),
        "uniprot_orthologs": sum(1 for r in by_ref if r.startswith("uniprot:")),
        "oma_orthologs": sum(1 for r in by_ref if r.startswith("oma:")),
    }
