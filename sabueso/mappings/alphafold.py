"""AlphaFold DB models → ``has_predicted_structure`` relationships (uibcdf/sabueso#57).

One relationship per model (``alphafold:<entryId>``, e.g. ``alphafold:AF-P52270-F1``),
supported by a SourceAssertion that keeps the record as AlphaFold DB states it. The
qualifiers are what a reader needs to judge a model:

- the model version, the tool, and the creation date;
- the mean pLDDT (a confidence score from 0 to 100, not a physical quantity), and the
  fractions of residues in each confidence band;
- the UniProt range the model covers;
- whole-sequence MD5 comparison against the original input, with named rule,
  scope and source references. A different checksum establishes neither cause
  nor age; partial model checksums are not compared to the whole reference;
- ``isoform`` only where original UniProt statements name it. A different model
  accession alone never establishes an isoform relationship. No focal-entry
  coverage is computed for another accession or an unbound historical context.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.relationship_store import make_derivation, make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

from .alphafold_context_v1 import QUALIFIER_PATHS, RULE, interpret, original_inputs

SOURCE = "AlphaFold DB"


def map_predictions(
    response: Dict[str, Any],
    accession: str,
    retrieved_at: str,
    sequence_md5: str | None = None,
    *,
    input_assertions: List[Dict[str, Any]] | None = None,
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
        context = interpret(model, accession, sequence_md5, input_assertions)
        inputs = original_inputs(input_assertions, accession)
        isoform = (
            context["model_accession"]
            if context["identity_state"] == "source_stated_isoform"
            else None
        )
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
                    "sequence_matches": context["sequence_matches"],
                    "sequence_context": context,
                },
                source_assertion_ids=[assertion["id"]],
                derivation=make_derivation(
                    RULE,
                    inputs=[assertion["id"], *sorted({r["id"] for r in inputs})],
                    parameters={
                        "qualifier_paths": QUALIFIER_PATHS,
                        "model_input_path": ["asserted_value", "model"],
                        "focal_accession": accession,
                        "sequence_md5_argument": sequence_md5,
                        "focal_input_assertion_ids": sorted({r["id"] for r in inputs}),
                        "input_binding": context["input_binding"],
                    },
                ),
            )
        )
    return {
        "fields": {},
        "source_assertions": source_assertions,
        "field_source_assertions": {},
        "relationships": relationships,
    }
