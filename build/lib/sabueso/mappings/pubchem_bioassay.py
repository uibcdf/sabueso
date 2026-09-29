"""PubChem BioAssay results → ``has_bioactivity`` relationships (uibcdf/sabueso#68).

One relationship per result row, from the protein to ``pubchem:<CID>``, with the
ChEMBL qualifier layout, so views read every source alike:

- ``activity_id`` is ``pubchem:<AID>:<SID>``, and ``source`` is ``"PubChem BioAssay"``;
- ``copy_of`` names the depositor and its own assay id when the assay was deposited by
  ChEMBL or BindingDB (``{"source": "ChEMBL", "assay": "CHEMBL816360"}``). Such rows are
  copies with a declared origin;
- the value is in µM as PubChem states it. Its relation is not in the table, so
  ``relation`` is None: a copy never imposes a relation it does not state;
- ``molecule_ref`` is the InChIKey PubChem states for the CID;
- ``outcome`` keeps PubChem's activity outcome (Active, Inactive, Unspecified…).
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.quantities import normalized_measurement
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "PubChem BioAssay"
#: Depositors whose assays are copies of their own records.
COPIED_FROM = {"ChEMBL": "ChEMBL", "BindingDB": "BindingDB"}


def _number(text: Any) -> float | None:
    try:
        return float(text) if str(text).strip() else None
    except ValueError:
        return None


def map_assays(
    response: Dict[str, Any], accession: str, retrieved_at: str
) -> Dict[str, Any]:
    record = response.get("record") or {}
    summaries = {str(s["AID"]): s for s in record.get("summaries") or []}
    inchikeys = record.get("inchikeys") or {}
    source_assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    for aid, table in sorted(
        (record.get("concise") or {}).items(), key=lambda kv: int(kv[0])
    ):
        columns = (table.get("Columns") or {}).get("Column") or []
        summary = summaries.get(str(aid)) or {}
        depositor = summary.get("SourceName")
        copy_of = (
            {"source": COPIED_FROM[depositor], "assay": summary.get("SourceID")}
            if depositor in COPIED_FROM
            else None
        )
        for row in table.get("Row") or []:
            cell = dict(zip(columns, row.get("Cell") or []))
            cid, sid = cell.get("CID"), cell.get("SID")
            if not cid:
                continue
            target = cell.get("Target Accession")
            if target and target != accession:
                continue  # a row of this assay about another protein
            object_ref = f"pubchem:{cid}"
            assertion = make_source_assertion(
                "relationships.has_bioactivity",
                {
                    "object_ref": object_ref,
                    "aid": int(aid),
                    "row": cell,
                    "assay": summary.get("Name"),
                },
                SOURCE,
                f"AID{aid}",
                retrieved_at,
                subject_ref=f"uniprot:{accession}",
            )
            source_assertions.append(assertion)
            value = _number(cell.get("Activity Value [uM]"))
            key = inchikeys.get(str(cid))
            pmid = cell.get("PubMed ID")
            relationships.append(
                make_relationship(
                    f"uniprot:{accession}",
                    "has_bioactivity",
                    object_ref,
                    qualifiers={
                        "activity_id": f"pubchem:{aid}:{sid}",
                        "source": SOURCE,
                        "copy_of": copy_of,
                        "molecule_ref": f"inchikey:{key}" if key else None,
                        "measurement": {
                            "type": cell.get("Activity Name") or None,
                            "relation": None,
                            "value": value,
                            "units": "uM" if value is not None else None,
                            "stated_value": cell.get("Activity Value [uM]") or None,
                            "normalized": normalized_measurement(value, "uM"),
                            "pchembl": None,
                            "outcome": cell.get("Activity Outcome"),
                        },
                        "assay": {
                            "id": f"AID{aid}",
                            "description": summary.get("Name"),
                            "relationship_type": "D",
                            "organism": None,
                            "source": SOURCE,
                            "depositor": depositor,
                            "depositor_id": summary.get("SourceID"),
                        },
                        "document": {
                            "id": None,
                            "year": None,
                            "journal": None,
                            "pubmed": str(pmid) if pmid else None,
                            "doi": None,
                            "title": None,
                        },
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
