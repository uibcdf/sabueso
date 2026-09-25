"""AlphaFold DB models → ``has_predicted_structure`` relationships (uibcdf/sabueso#57).

One relationship per model (``alphafold:<entryId>``, e.g. ``alphafold:AF-P52270-F1``),
supported by a SourceAssertion that keeps the record as AlphaFold DB states it. The
qualifiers are what a reader needs to judge a model:

- the model version, the tool, and the creation date;
- the mean pLDDT (a confidence score from 0 to 100, not a physical quantity), and the
  fractions of residues in each confidence band;
- the UniProt range the model covers;
- whether the modelled sequence is the entry's current sequence (``sequence_matches``,
  by MD5). A model of an older sequence version does not describe the current one;
- ``isoform``: AlphaFold DB also models an entry's isoforms (``P60174-3``). Such a model
  is of another sequence, so ``sequence_matches`` is None and the view gives no
  coverage of the entry for it.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "AlphaFold DB"


def map_predictions(
    response: Dict[str, Any],
    accession: str,
    retrieved_at: str,
    sequence_md5: str | None = None,
) -> Dict[str, Any]:
    source_assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    for model in response.get("record") or []:
        entry = model.get("entryId") or model.get("modelEntityId")
        if not entry:
            continue
        object_ref = f"alphafold:{entry}"
        assertion = make_source_assertion(
            "relationships.has_predicted_structure",
            {"object_ref": object_ref, "model": model},
            SOURCE,
            entry,
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        if model.get("latestVersion") is not None:
            assertion["source"]["version"] = str(model["latestVersion"])
        source_assertions.append(assertion)
        checksum = model.get("sequenceChecksum")
        # AlphaFold DB also models the entry's isoforms (e.g. P60174-3). Such a model is
        # of another sequence: its coverage and sequence check do not apply to the entry.
        modelled = model.get("uniprotAccession") or accession
        isoform = modelled if modelled != accession else None
        relationships.append(
            make_relationship(
                f"uniprot:{accession}",
                "has_predicted_structure",
                object_ref,
                qualifiers={
                    "model_version": model.get("latestVersion"),
                    "tool": model.get("toolUsed"),
                    "created": model.get("modelCreatedDate"),
                    "mean_plddt": model.get("globalMetricValue"),
                    "plddt_fractions": {
                        "very_high": model.get("fractionPlddtVeryHigh"),
                        "confident": model.get("fractionPlddtConfident"),
                        "low": model.get("fractionPlddtLow"),
                        "very_low": model.get("fractionPlddtVeryLow"),
                    },
                    "range": [model.get("uniprotStart"), model.get("uniprotEnd")],
                    "isoform": isoform,
                    "sequence_matches": None
                    if isoform or not (checksum and sequence_md5)
                    else checksum.lower() == sequence_md5.lower(),
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
