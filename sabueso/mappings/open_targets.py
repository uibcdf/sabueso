"""Open Targets associations → ``associated_with`` relationships (#82).

One relationship per associated disease, with Open Targets' overall ``score`` and its
``datatype_scores`` as stated, and the data version on the SourceAssertion. The row
reaches the card through the Ensembl gene UniProt cross-references (``via_gene``), and
only when Open Targets also lists the card's accession among the gene's products: both
sources state the link (basis ``uniprot_ensembl_xref``, ``gene_lists_protein``). Disease
terms keep Open Targets' ontology (``mondo:MONDO:0014221``, ``efo:EFO:…``); a term of
another ontology is another disease reference, never merged by name.
"""

from __future__ import annotations

from typing import Any, Dict

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "Open Targets"


def disease_ref(term: str) -> str:
    """``mondo:MONDO:0014221`` for Open Targets' ``MONDO_0014221``."""
    prefix, _, number = term.partition("_")
    return f"{prefix.lower()}:{prefix}:{number}" if number else term


def lists_protein(target: Dict[str, Any], accession: str) -> bool:
    return any(p.get("id") == accession for p in target.get("proteinIds") or [])


def map_associations(
    record: Dict[str, Any], accession: str, retrieved_at: str, version: str | None
) -> Dict[str, Any]:
    target = record.get("target") or {}
    gene = target.get("id")
    assertions, relationships = [], []
    for rank, row in enumerate(record.get("rows") or [], start=1):
        disease = (row.get("disease") or {}).get("id")
        if not disease:
            continue
        assertion = make_source_assertion(
            "relationships.associated_with",
            {"target": gene, **row},
            SOURCE,
            f"{gene}:{disease}",
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        if version is not None:
            assertion["source"]["version"] = str(version)
        assertions.append(assertion)
        relationships.append(
            make_relationship(
                f"uniprot:{accession}",
                "associated_with",
                disease_ref(disease),
                qualifiers={
                    "source": SOURCE,
                    "disease_name": (row.get("disease") or {}).get("name"),
                    "score": row.get("score"),
                    # A list, not a mapping: data types are data, not schema keys.
                    "datatype_scores": [
                        {"datatype": d["id"], "score": d.get("score")}
                        for d in row.get("datatypeScores") or []
                        if d.get("id")
                    ],
                    "rank": rank,
                    "via_gene": f"ensembl:{gene}",
                    "basis": "uniprot_ensembl_xref",
                    "gene_lists_protein": True,
                },
                source_assertion_ids=[assertion["id"]],
            )
        )
    return {"source_assertions": assertions, "relationships": relationships}
