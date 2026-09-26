"""NCBI Gene record → the UniProt entries NCBI lists as the gene's products (#69).

NCBI Gene links each gene to the UniProtKB entries of its products, Swiss-Prot and
TrEMBL alike. Two UniProt entries that state their gene in different databases (NCBI
Gene for one, an organism database for the other) can then be related through a
source statement: NCBI lists both as products of one gene.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, List

_UNIPROT = {"UniProtKB/Swiss-Prot": "swiss_prot", "UniProtKB/TrEMBL": "trembl"}


def _text(node: Any, path: str) -> str | None:
    found = node.find(path)
    return found.text.strip() if found is not None and found.text else None


def parse_gene(xml: str) -> Dict[str, Any] | None:
    """``{gene_id, status, symbol, locus_tag, tax_id, updated, uniprot}`` from an Entrez
    Gene XML record, or None when the record holds no gene (an ``<Error>``).

    ``uniprot`` is ``{"swiss_prot": [...], "trembl": [...]}``: every UniProtKB accession
    the record links to, sorted.
    """
    root = ET.fromstring(xml)
    gene = root.find("Entrezgene")
    if gene is None:
        return None
    uniprot: Dict[str, List[str]] = {"swiss_prot": [], "trembl": []}
    for tag in gene.iter("Dbtag"):
        kind = _UNIPROT.get(_text(tag, "Dbtag_db") or "")
        accession = _text(tag, "Dbtag_tag/Object-id/Object-id_str")
        if kind and accession and accession not in uniprot[kind]:
            uniprot[kind].append(accession)
    status = gene.find("Entrezgene_track-info/Gene-track/Gene-track_status")
    updated = [
        _text(
            gene,
            f"Entrezgene_track-info/Gene-track/Gene-track_update-date/Date/Date_std/Date-std/Date-std_{part}",
        )
        for part in ("year", "month", "day")
    ]
    tax_id = None
    for tag in gene.findall(
        "Entrezgene_source/BioSource/BioSource_org/Org-ref/Org-ref_db/Dbtag"
    ):
        if _text(tag, "Dbtag_db") == "taxon":
            tax_id = _text(tag, "Dbtag_tag/Object-id/Object-id_id")
    return {
        "gene_id": _text(gene, "Entrezgene_track-info/Gene-track/Gene-track_geneid"),
        "status": status.get("value") if status is not None else None,
        "symbol": _text(gene, "Entrezgene_gene/Gene-ref/Gene-ref_locus"),
        "locus_tag": _text(gene, "Entrezgene_gene/Gene-ref/Gene-ref_locus-tag"),
        "tax_id": int(tax_id) if tax_id else None,
        "updated": "-".join(p.zfill(2) for p in updated) if all(updated) else None,
        "uniprot": {k: sorted(v) for k, v in uniprot.items()},
    }


def products(record: Dict[str, Any] | None) -> List[str]:
    """Every UniProtKB accession a parsed gene record lists as a product."""
    if not record:
        return []
    return sorted({a for accessions in record["uniprot"].values() for a in accessions})
