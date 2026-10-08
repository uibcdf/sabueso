"""Native HPA categorical expression summaries on an explicit human gene."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "Human Protein Atlas"
GENE = re.compile(r"ENSG[0-9]{11}\Z")
SCOPES = (
    "RNA tissue",
    "RNA single cell type",
    "RNA single cell type group",
    "RNA single nuclei brain",
    "RNA cancer",
    "RNA brain regional",
    "RNA blood cell",
    "RNA blood lineage",
    "RNA cell line",
    "Protein cell type",
    "Protein tissue",
)
CATEGORIES = tuple(
    f"{scope} {category}"
    for scope in SCOPES
    for category in ("specificity", "distribution")
)


def gene_id(identifier):
    if not isinstance(identifier, str) or not GENE.fullmatch(identifier):
        raise ConnectorError(
            "HPA requires one exact unversioned human ENSG identifier."
        )
    return identifier


def validate_profile(payload, identifier):
    """Require one native gene object; quantitative fields remain in that object."""
    identifier = gene_id(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("HPA response is not finite JSON.") from error
    if (
        not isinstance(payload, dict)
        or payload.get("Ensembl") != identifier
        or not isinstance(payload.get("Gene"), str)
        or not payload["Gene"]
        or not any(key in payload for key in CATEGORIES)
    ):
        raise ConnectorError("HPA native gene identity/summary object is malformed.")
    if "Uniprot" in payload and (
        not isinstance(payload["Uniprot"], list)
        or any(not isinstance(v, str) or not v for v in payload["Uniprot"])
    ):
        raise ConnectorError("HPA native UniProt reference list is malformed.")
    for key in CATEGORIES:
        if (
            key in payload
            and payload[key] is not None
            and (not isinstance(payload[key], str) or not payload[key])
        ):
            raise ConnectorError("HPA categorical summary must be native text or null.")
    return payload


def map_gene_summary(envelope):
    """Keep independent categorical declarations, including explicitly stated nulls.

    RNA and protein contexts retain their native labels. Neither categories nor
    gene cross-references establish a measured protein form, an isoform, an assay,
    experimental support or a sequence correspondence. Quantitative fields stay
    available in the original envelope; this mapping does not project them.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != SOURCE
        or envelope.get("kind") != "gene_profile"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"gene_id", "format"}
        or envelope["query"]["format"] != "single_gene_json_subset"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError("HPA mapping requires a qualified single-gene envelope.")
    identifier = gene_id(envelope["query"]["gene_id"])
    record = validate_profile(envelope.get("record"), identifier)
    response_hash = digest(canonical_json(record))
    out = []
    for key in CATEGORIES:
        if key not in record:
            continue
        assertion = make_source_assertion(
            "expression.gene_summary.hpa",
            {"native_field": key, "native_value": record[key]},
            SOURCE,
            f"{identifier}:{key}:{response_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"hpa:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "response_hash": response_hash,
            "native_record_url": f"https://www.proteinatlas.org/{identifier}.json",
            "native_gene_label": record["Gene"],
            "native_uniprot_references": deepcopy(record.get("Uniprot")),
            "mapping_scope": {
                "coverage": "single_gene_json_subset; not_full_expression_or_assay_data",
                "identity": "native_gene_subject; no_protein_or_isoform_identity_merge",
                "interpretation": "literal_source_category_or_null; no_experimental_class",
                "quantities": "not_projected; original_native_envelope_retained",
                "revisions": "dataset_record_and_sequence_revisions_not_stated",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        out.append(assertion)
    return out
