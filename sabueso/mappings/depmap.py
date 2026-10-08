"""Native DepMap model metadata from one fixed public release, without gene effects."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

RELEASE = "24Q4"
ARTIFACT = "24Q4__Model.csv"
URL = "https://ndownloader.figshare.com/files/51065297"
SHA256 = "b7a0c1385e6cef30132b56aff61f1261d11e3f490490b355c430d32ee0dbdcfa"
DATASET = {
    "release": RELEASE,
    "article_id": 27993248,
    "article_version": 1,
    "file_id": 51065297,
    "doi": "10.25452/figshare.plus.27993248.v1",
    "metadata_url": "https://api.figshare.com/v2/articles/27993248/versions/1",
    "licence": "CC-BY-4.0",
}
COLUMNS = (
    "ModelID",
    "PatientID",
    "CellLineName",
    "StrippedCellLineName",
    "DepmapModelType",
    "OncotreeLineage",
    "OncotreePrimaryDisease",
    "OncotreeSubtype",
    "OncotreeCode",
    "PatientSubtypeFeatures",
    "RRID",
    "Age",
    "AgeCategory",
    "Sex",
    "PatientRace",
    "PrimaryOrMetastasis",
    "SampleCollectionSite",
    "SourceType",
    "SourceDetail",
    "CatalogNumber",
    "ModelType",
    "TissueOrigin",
    "ModelDerivationMaterial",
    "ModelTreatment",
    "PatientTreatmentStatus",
    "PatientTreatmentType",
    "PatientTreatmentDetails",
    "Stage",
    "StagingSystem",
    "PatientTumorGrade",
    "PatientTreatmentResponse",
    "GrowthPattern",
    "OnboardedMedia",
    "FormulationID",
    "SerumFreeMedia",
    "PlateCoating",
    "EngineeredModel",
    "EngineeredModelDetails",
    "CulturedResistanceDrug",
    "PublicComments",
    "CCLEName",
    "HCMIID",
    "ModelAvailableInDbgap",
    "ModelSubtypeFeatures",
    "WTSIMasterCellID",
    "SangerModelID",
    "COSMICID",
)
MAPPED = (
    "ModelID",
    "CellLineName",
    "StrippedCellLineName",
    "DepmapModelType",
    "OncotreeLineage",
    "OncotreePrimaryDisease",
    "OncotreeSubtype",
    "OncotreeCode",
    "RRID",
    "SourceType",
    "SourceDetail",
    "CatalogNumber",
    "ModelType",
    "TissueOrigin",
    "ModelDerivationMaterial",
    "CCLEName",
)


def response_query(identifier, release=RELEASE):
    if not isinstance(identifier, str) or not re.fullmatch(r"ACH-[0-9]{6}", identifier):
        raise ConnectorError("DepMap requires one exact native ACH model identifier.")
    if release != RELEASE:
        raise ConnectorError(
            "Only the qualified DepMap 24Q4 v1 Model.csv is supported."
        )
    return {
        "model_id": identifier,
        "release": release,
        "article_version": 1,
        "export": "Model.csv",
    }


def parse_models(text):
    """Validate all quoted CSV rows before selection, preserving blanks and repeats."""
    if not isinstance(text, str) or not text:
        raise ConnectorError("DepMap requires nonempty native Model.csv text.")
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        if tuple(next(reader)) != COLUMNS:
            raise ConnectorError("Unsupported DepMap native model header.")
        rows = []
        for fields in reader:
            if len(fields) != len(COLUMNS) or any(
                any(ord(c) < 32 and c not in "\r\n\t" or ord(c) == 127 for c in value)
                for value in fields
            ):
                raise ConnectorError("Malformed DepMap native model row.")
            response_query(fields[0])
            rows.append({"csv_end_line": reader.line_num, "fields": fields})
        return rows
    except (csv.Error, StopIteration) as error:
        raise ConnectorError("Unreadable DepMap native model CSV.") from error


def selected_rows(rows, identifier):
    response_query(identifier)
    return [row for row in rows if row["fields"][0] == identifier]


def map_model(envelope):
    """Keep model identity and descriptive context without interpreting measurements."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "DepMap"
        or envelope.get("kind") != "model"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("DepMap requires a full native model envelope.")
    query = envelope["query"]
    if query != response_query(query.get("model_id"), query.get("release")):
        raise ConnectorError("Unsupported DepMap release/model/export scope.")
    rows = parse_models(envelope.get("record"))
    response_hash = "sha256:" + hashlib.sha256(envelope["record"].encode()).hexdigest()
    assertions = []
    for row in selected_rows(rows, query["model_id"]):
        native = dict(zip(COLUMNS, row["fields"], strict=True))
        assertion = make_source_assertion(
            "annotations.cell_model_context",
            {k: native[k] for k in MAPPED},
            "DepMap",
            f"{RELEASE}:v1:{response_hash}:line:{row['csv_end_line']}",
            envelope.get("retrieved_at"),
            subject_ref=f"depmap:model:{native['ModelID']}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "response_hash": response_hash,
            "received_export_count": len(rows),
            "query": deepcopy(query),
            "selected_dataset": deepcopy(DATASET),
            "mapping_scope": {
                "identity": "exact_native_ModelID; names_RRID_and_other_IDs_not_merged",
                "revision": "fixed_release_article_version_separate_from_unknown_model_or_disease_ontology_revision",
                "measurements": "age_media_composition_and_unqualified_quantities_kept_only_in_raw_support",
                "coverage": "full_received_model_metadata; gene_effect_dependency_screens_and_conditions_unqueried",
                "biology": "source_model_descriptions_not_gene_essentiality_or_protein_target_claims",
                "terms": "selected_DepMap_24Q4_v1_CC_BY_4_0; other_datasets_have_independent_terms",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
