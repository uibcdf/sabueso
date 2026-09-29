"""ClinVar summaries → ``annotations.clinical_variants`` (#83).

One item per ClinVar variation record of the gene:

- what ClinVar states, verbatim: ``accession`` (VCV), ``title`` (HGVS), ``variant_type``,
  ``classification`` (a germline classification; "Conflicting classifications of
  pathogenicity" is kept as ClinVar states it, never resolved), ``review_status``,
  ``last_evaluated``, the ``conditions`` with their cross-references, and the
  ``consequences``;
- ``transcript``, ``hgvs_c`` and ``hgvs_p``, read from the title
  (``NM_000365.6(TPI1):c.315G>C (p.Glu105Asp)``).

**Numbering.** ClinVar's ``protein_change`` lists the change in each isoform's numbering
("E142D, E105D, E23D"), so it never places a variant. A variant gets a ``location`` in
the card's UniProt numbering only when both hold:

- its transcript is one UniProt states for the canonical isoform (RefSeq
  cross-references, with their versions);
- the residue ClinVar names is the residue of the UniProt sequence at that position.

Otherwise ``numbering`` names ClinVar's transcript and ``not_placed`` says why
(``no_protein_change``, ``transcript_not_canonical``, ``residue_mismatch``). A variant is
never placed by similarity.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from sabueso.core.source_assertion_store import make_source_assertion

from ._hgvs import place

SOURCE = "ClinVar"
FIELD = "annotations.clinical_variants"
TITLE = re.compile(r"(N[MR]_\d+\.\d+)\([^)]*\):(\S+)(?: \((p\.[^)]+)\))?")


def _parse_title(title: str) -> Dict[str, str]:
    match = TITLE.match(title or "")
    if not match:
        return {}
    out = {"transcript": match.group(1), "hgvs_c": match.group(2)}
    if match.group(3):
        out["hgvs_p"] = match.group(3)
    return out


def map_variants(
    records: List[Dict[str, Any]],
    accession: str,
    canonical: Iterable[str],
    sequence: str | None,
    retrieved_at: str,
    version: str | None,
) -> Dict[str, Any]:
    canonical = sorted(set(canonical))
    items, assertions = [], []
    for record in sorted(records, key=lambda r: r.get("accession") or ""):
        classification = record.get("germline_classification") or {}
        parsed = _parse_title(record.get("title"))
        item = {
            "accession": record.get("accession"),
            "title": record.get("title"),
            "variant_type": record.get("obj_type"),
            **parsed,
            "classification": classification.get("description") or None,
            "review_status": classification.get("review_status") or None,
            "last_evaluated": (classification.get("last_evaluated") or "")[:10].replace(
                "/", "-"
            )
            or None,
            "conditions": [
                {
                    "name": t.get("trait_name"),
                    "xrefs": [
                        f"{x['db_source']}:{x['db_id']}"
                        for x in t.get("trait_xrefs") or []
                        if x.get("db_source") and x.get("db_id")
                    ],
                }
                for t in classification.get("trait_set") or []
            ],
            "consequences": record.get("molecular_consequence_list") or [],
        }
        placed = place(
            parsed.get("hgvs_p"), parsed.get("transcript"), canonical, sequence
        )
        item.update(placed)
        item["numbering"] = (
            "uniprot" if "location" in placed else parsed.get("transcript")
        )
        item = {k: v for k, v in item.items() if v not in (None, "", [])}
        assertion = make_source_assertion(
            FIELD,
            item,
            SOURCE,
            record.get("accession") or str(record.get("uid")),
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        if version is not None:
            assertion["source"]["version"] = str(version)
        items.append(item)
        assertions.append(assertion)
    return {
        "fields": {FIELD: items} if items else {},
        "source_assertions": assertions,
        "field_source_assertions": {FIELD: [a["id"] for a in assertions]}
        if assertions
        else {},
        "relationships": [],
    }
