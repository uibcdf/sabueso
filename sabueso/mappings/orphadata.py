"""Orphadata rows → ``associated_with`` relationships (protein → rare disorder; #82).

One relationship per disorder–gene association Orphanet states for the card's UniProt
accession (Orphanet's own Swiss-Prot reference, basis ``orphanet_swissprot_xref``). The
disorder is ``orphanet:ORPHA:<code>``. Qualifiers keep Orphanet's wording:
``association_type`` (e.g. "Disease-causing germline mutation(s) in"),
``association_status`` ("Assessed"…), the disorder's type and group, and the
publications that validate it (``validation``, as ``pubmed:`` references).
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "Orphanet"


def map_associations(
    rows: List[Dict[str, Any]], accession: str, retrieved_at: str, version: str | None
) -> Dict[str, Any]:
    assertions, relationships = [], []
    for row in sorted(rows, key=lambda r: int(r.get("orpha_code") or 0)):
        code = row.get("orpha_code")
        if not code:
            continue
        assertion = make_source_assertion(
            "relationships.associated_with",
            row,
            SOURCE,
            f"ORPHA:{code}:{row.get('gene_symbol')}",
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        if version is not None:
            assertion["source"]["version"] = str(version)
        assertions.append(assertion)
        qualifiers = {
            "source": SOURCE,
            "disease_name": row.get("disorder_name"),
            "association_type": row.get("association_type"),
            "association_status": row.get("association_status"),
            "disorder_type": row.get("disorder_type"),
            "disorder_group": row.get("disorder_group"),
            "validation": [f"pubmed:{p}" for p in row.get("validation") or []],
            "via_gene": f"ensembl:{row['ensembl_gene']}"
            if row.get("ensembl_gene")
            else None,
            "basis": "orphanet_swissprot_xref",
        }
        relationships.append(
            make_relationship(
                f"uniprot:{accession}",
                "associated_with",
                f"orphanet:ORPHA:{code}",
                qualifiers={k: v for k, v in qualifiers.items() if v not in (None, [])},
                source_assertion_ids=[assertion["id"]],
            )
        )
    return {"source_assertions": assertions, "relationships": relationships}
