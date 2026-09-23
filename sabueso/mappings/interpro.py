"""InterPro site residues -> ``features_positional.family_site`` (uibcdf/sabueso#28).

Each site a member database annotates inside a signature (e.g. CDD ``cd00311``: catalytic
triad, substrate binding site, dimer interface) becomes one item, positioned on the
protein's own sequence as InterPro states it. The item keeps the site description
verbatim and names its signature. Sites are family-level annotations: they are placed
by the source's model of the family, not observed on this protein, which is why they stay
apart from UniProt's ``active_site``/``binding_site`` instead of being merged into them.

Each item is backed by an InterPro SourceAssertion whose subject is the UniProt protein
(InterPro keys protein records by UniProt accession), with the InterPro release in
``source.version`` and the member database and signature in ``source_metadata``.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion

FIELD_PATH = "features_positional.family_site"


def map_family_sites(response: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map an InterPro ``site_residues`` response (``tools.db.interpro``)."""
    accession = response["accession"]
    version = response.get("version")
    items: List[Dict[str, Any]] = []
    source_assertions: List[Dict[str, Any]] = []
    for signature_id, signature in sorted((response.get("residues") or {}).items()):
        database = signature.get("source_database")
        for location in signature.get("locations") or []:
            fragments = sorted(
                (
                    {
                        "start": f.get("start"),
                        "end": f.get("end")
                        if f.get("end") is not None
                        else f.get("start"),
                        "residues": f.get("residues"),
                    }
                    for f in location.get("fragments") or []
                    if f.get("start") is not None
                ),
                key=lambda f: f["start"],
            )
            if not fragments:
                continue
            item = {
                "location": {
                    "kind": "sequence",
                    "sequence": {
                        "sequence_id": f"UniProt:{accession}",
                        "fragments": fragments,
                        "indexing": "1-based",
                    },
                },
                "description": location.get("description") or "",
                "signature": {
                    "accession": signature.get("accession") or signature_id,
                    "source_database": database,
                    "name": signature.get("name"),
                },
            }
            assertion = make_source_assertion(
                FIELD_PATH,
                item,
                "InterPro",
                accession,
                retrieved_at,
                subject_ref=f"uniprot:{accession}",
            )
            assertion["source_metadata"] = {
                "member_database": database,
                "signature": signature.get("accession") or signature_id,
            }
            if version:
                assertion["source"]["version"] = version
            items.append(item)
            source_assertions.append(assertion)
    return {
        "fields": {},
        "features": {FIELD_PATH: items} if items else {},
        "source_assertions": source_assertions,
        "field_source_assertions": {FIELD_PATH: [a["id"] for a in source_assertions]}
        if source_assertions
        else {},
        "relationships": [],
    }
