"""STRING interaction partners -> ``functionally_associated_with`` relationships.

Each STRING row becomes a relationship of the protein entity to the partner's STRING
protein (``string:<taxon>.<id>``). It is backed by a STRING SourceAssertion that keeps the
row verbatim together with the query parameters and records the STRING version in
``source.version``. The combined score and its evidence channels are qualifiers, so a
consumer can tell curated-pathway or text-mining associations from experimental ones.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

# STRING channel score keys -> Sabueso qualifier names.
CHANNELS = {
    "nscore": "neighborhood",
    "fscore": "fusion",
    "pscore": "cooccurrence",
    "ascore": "coexpression",
    "escore": "experiments",
    "dscore": "databases",
    "tscore": "textmining",
}


def map_string_partners(
    response: Dict[str, Any], subject_accession: str, retrieved_at: str
) -> Dict[str, Any]:
    """Map a STRING ``interaction_partners`` response for a protein entity."""
    query = response.get("query", {})
    version = response.get("version")
    source_assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    for row in response.get("results", []) or []:
        partner = f"string:{row['stringId_B']}"
        assertion = make_source_assertion(
            "relationships.functionally_associated_with",
            {"object_ref": partner, "row": row, "query": query},
            "STRING",
            row["stringId_A"],
            retrieved_at,
        )
        if version:
            assertion["source"]["version"] = version
        source_assertions.append(assertion)
        relationships.append(
            make_relationship(
                f"uniprot:{subject_accession}",
                "functionally_associated_with",
                partner,
                qualifiers={
                    "partner_name": row.get("preferredName_B"),
                    "combined_score": row.get("score"),
                    "channels": {
                        name: row.get(key)
                        for key, name in CHANNELS.items()
                        if key in row
                    },
                    "string_id": row.get("stringId_A"),
                    "species": row.get("ncbiTaxonId"),
                    "required_score": query.get("required_score"),
                },
                source_assertion_ids=[assertion["id"]],
            )
        )
    return {
        "fields": {},
        "source_assertions": source_assertions,
        "field_source_assertions": {},
        "relationships": relationships,
    }
