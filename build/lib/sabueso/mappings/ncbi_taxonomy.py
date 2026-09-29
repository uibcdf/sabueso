"""NCBI Taxonomy → ``annotations.taxonomy`` (uibcdf/sabueso#67).

The field states the organism's taxon with its rank, and every ancestor with its name
and rank, from the root down: ``{"tax_id", "name", "rank", "ancestors": [{"tax_id",
"name", "rank"}, ...]}``. Ranks are NCBI's, in lower case (``species``, ``genus``,
``strain``…); a node NCBI gives no rank to has ``None``. An ancestor NCBI does not
return is kept with its id only.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "NCBI Taxonomy"


def _rank(taxon: Dict[str, Any]) -> str | None:
    rank = taxon.get("rank")
    return rank.lower() if isinstance(rank, str) and rank else None


def map_taxonomy(
    organism: Dict[str, Any],
    ancestors: List[Dict[str, Any]],
    accession: str,
    retrieved_at: str,
) -> Dict[str, Any]:
    by_id = {int(a["tax_id"]): a for a in ancestors}
    value = {
        "tax_id": int(organism["tax_id"]),
        "name": organism.get("organism_name"),
        "rank": _rank(organism),
        "ancestors": [
            {
                "tax_id": int(t),
                "name": (by_id.get(int(t)) or {}).get("organism_name"),
                "rank": _rank(by_id.get(int(t)) or {}),
            }
            for t in organism.get("lineage") or []
        ],
    }
    assertion = make_source_assertion(
        "annotations.taxonomy",
        value,
        SOURCE,
        str(organism["tax_id"]),
        retrieved_at,
        subject_ref=f"uniprot:{accession}",
    )
    return {
        "fields": {"annotations.taxonomy": value},
        "source_assertions": [assertion],
        "field_source_assertions": {"annotations.taxonomy": [assertion["id"]]},
        "relationships": [],
    }
