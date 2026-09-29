"""DISEASES rows → ``associated_with`` relationships (protein → disease; #82, #83).

One relationship per disease and channel: a curated association and a text-mined
co-mention of the same disease are two statements, never merged. Each keeps DISEASES's
scores as stated: ``confidence`` in every channel, and ``source_database``,
``statement_type`` (knowledge), ``source_score`` (experiments) or ``z_score`` (text
mining). None of them is recomputed or ranked.

A row reaches the card through an Ensembl protein that the UniProt entry cross-
references (``via_protein``, basis ``uniprot_ensembl_xref``), never through the gene
name DISEASES prints. ``uniprot_isoform`` names the isoform UniProt maps that protein
to.
"""

from __future__ import annotations

from typing import Any, Dict

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "DISEASES"
BASIS = "uniprot_ensembl_xref"
NUMERIC = ("confidence", "z_score")


def disease_ref(term: str) -> str:
    """``doid:DOID:10718`` for ``DOID:10718``."""
    return f"{term.split(':', 1)[0].lower()}:{term}"


def _number(value: Any) -> Any:
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def map_associations(
    record: Dict[str, list],
    accession: str,
    isoform_of: Dict[str, str | None],
    retrieved_at: str,
    versions: Dict[str, str | None],
) -> Dict[str, Any]:
    """``record`` is ``{channel: [row, ...]}``; ``isoform_of`` maps each Ensembl protein
    UniProt cross-references to the isoform it names (or None)."""
    assertions, relationships = [], []
    for channel in sorted(record):
        for row in sorted(record[channel], key=lambda r: (r["disease"], r["protein"])):
            if row["protein"] not in isoform_of:
                continue
            assertion = make_source_assertion(
                "relationships.associated_with",
                row,
                SOURCE,
                f"{channel}:{row['protein']}:{row['disease']}",
                retrieved_at,
                subject_ref=f"uniprot:{accession}",
                # DISEASES states that this channel's records are mined from text.
                acquisition={"method": "database", "origin": "text_mining"}
                if channel == "textmining"
                else None,
            )
            if versions.get(channel):
                assertion["source"]["version"] = f"{channel} {versions[channel]}"
            assertions.append(assertion)
            qualifiers = {
                "source": SOURCE,
                "channel": channel,
                "disease_name": row.get("disease_name"),
                "via_protein": f"ensembl:{row['protein']}",
                "uniprot_isoform": isoform_of[row["protein"]],
                "basis": BASIS,
                **{
                    k: _number(row[k]) if k in NUMERIC else row[k]
                    for k in (
                        "source_database",
                        "statement_type",
                        "source_score",
                        "z_score",
                        "confidence",
                    )
                    if row.get(k) not in (None, "")
                },
            }
            relationships.append(
                make_relationship(
                    f"uniprot:{accession}",
                    "associated_with",
                    disease_ref(row["disease"]),
                    qualifiers={k: v for k, v in qualifiers.items() if v is not None},
                    source_assertion_ids=[assertion["id"]],
                )
            )
    return {"source_assertions": assertions, "relationships": relationships}
