"""GTEx's tissues → the ontology terms of the tissues a card's pext names (#102).

gnomAD's pext gives, per GTEx tissue, the share of a gene's expression that includes a
coding region. It names each tissue by GTEx's id in lower case, with every run of other
characters as one ``_`` (``brain_spinal_cord_cervical_c_1`` for GTEx's
``Brain_Spinal_cord_cervical_c-1``). Rule ``gtex_tissue_key@1`` joins the two ids that
way; it compares identifiers of one dataset, never names.

It states ``annotations.tissue_terms``: for each GTEx tissue the card's pext names, as
GTEx states it, its id, name, tissue site and ontology term (UBERON, or EFO for a cell
line) with the term's IRI. Two GTEx tissues can share a term (GTEx gives the cerebellum
and the cerebellar hemisphere UBERON:0002037), so a term never replaces the tissue.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "GTEx"
FIELD = "annotations.tissue_terms"
KEY_RULE = "gtex_tissue_key@1"


def tissue_key(gtex_id: str) -> str:
    """The key gnomAD's pext names a GTEx tissue by (``gtex_tissue_key@1``)."""
    return re.sub(r"[^a-z0-9]+", "_", str(gtex_id).lower()).strip("_")


def map_tissue_terms(
    rows: List[Dict[str, Any]],
    tissue_keys: Iterable[str],
    accession: str,
    retrieved_at: str,
    dataset: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    wanted = set(tissue_keys)
    items: List[Dict[str, Any]] = []
    assertions: List[Dict[str, Any]] = []
    matched = set()
    for row in sorted(rows, key=lambda r: str(r.get("tissueSiteDetailId"))):
        key = tissue_key(row.get("tissueSiteDetailId") or "")
        if key not in wanted:
            continue
        matched.add(key)
        item = {
            "gtex_id": row.get("tissueSiteDetailId"),
            "name": row.get("tissueSiteDetail"),
            "tissue_site": row.get("tissueSite"),
            "ontology_id": row.get("ontologyId"),
            "ontology_iri": row.get("ontologyIri"),
        }
        item = {k: v for k, v in item.items() if v is not None}
        made = make_source_assertion(
            FIELD,
            item,
            SOURCE,
            f"gtex:{dataset}:{item['gtex_id']}",
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        made["source"]["version"] = dataset
        items.append(item)
        assertions.append(made)
    mapping = {
        "fields": {FIELD: items} if items else {},
        "source_assertions": assertions,
        "field_source_assertions": {FIELD: [a["id"] for a in assertions]}
        if assertions
        else {},
        "relationships": [],
    }
    return mapping, {
        "count": len(items),
        "join_rule": KEY_RULE,
        "tissues_not_in_gtex": sorted(wanted - matched),
    }
