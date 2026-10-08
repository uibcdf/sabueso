"""Original HPO gene/disease phenotype occurrences, without ontology expansion."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from datetime import date
from io import StringIO

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

RELEASE = "v2026-09-01"
COLUMNS = (
    "ncbi_gene_id",
    "gene_symbol",
    "hpo_id",
    "hpo_name",
    "frequency",
    "disease_id",
)
HEADER = "\t".join(COLUMNS)
GENE = re.compile(r"[1-9][0-9]{0,15}\Z")
HP = re.compile(r"HP:[0-9]{7}\Z")
DISEASE = re.compile(r"(?:OMIM|ORPHA):[1-9][0-9]*\Z")


def response_query(identifier, release=RELEASE):
    if not isinstance(identifier, str) or not GENE.fullmatch(identifier):
        raise ConnectorError("HPO requires one literal positive NCBI Gene ID.")
    if not isinstance(release, str) or not re.fullmatch(
        r"v[0-9]{4}-[0-9]{2}-[0-9]{2}", release
    ):
        raise ConnectorError("HPO requires an exact dated vYYYY-MM-DD release.")
    try:
        date.fromisoformat(release[1:])
    except ValueError as error:
        raise ConnectorError("HPO release date is invalid.") from error
    return {
        "ncbi_gene_id": identifier,
        "release": release,
        "export": "genes_to_phenotype",
    }


def export_url(release):
    response_query("1", release)
    return f"https://github.com/obophenotype/human-phenotype-ontology/releases/download/{release}/genes_to_phenotype.txt"


def parse_annotations(text, identifier):
    """Validate every received row before returning exact-ID occurrences.

    Keep frequency strings opaque: fractions, percentages, terms and future text
    are source representations, not computed gene penetrance or patient estimates.
    A symbol or term name is never used to select or merge identity.
    """
    response_query(identifier)
    if not isinstance(text, str) or not text:
        raise ConnectorError("HPO requires nonempty original six-column TSV text.")
    stream = StringIO(text)
    if stream.readline().rstrip("\r\n") != HEADER:
        raise ConnectorError("HPO native gene-phenotype header is unsupported.")
    selected, count = [], 0
    for number, line in enumerate(stream, 2):
        raw_line = line.rstrip("\r\n")
        fields = raw_line.split("\t")
        if (
            len(fields) != 6
            or any(
                not x or any(ord(c) < 32 or ord(c) == 127 for c in x) for x in fields
            )
            or not GENE.fullmatch(fields[0])
            or not HP.fullmatch(fields[2])
            or not DISEASE.fullmatch(fields[5])
        ):
            raise ConnectorError(f"Unsupported HPO native row at line {number}.")
        count += 1
        if fields[0] == identifier:
            selected.append({"line": number, "fields": fields, "raw_line": raw_line})
    return selected, count


def map_gene_annotations(envelope):
    """Keep independent disease-associated annotations on their native gene axis."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "HPO"
        or envelope.get("kind") != "gene_phenotypes"
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("HPO requires a full native gene-phenotype envelope.")
    query = envelope["query"]
    expected = response_query(query.get("ncbi_gene_id"), query.get("release"))
    if query != expected or envelope.get("version") != expected["release"]:
        raise ConnectorError("HPO query/release differs from the declared artifact.")
    rows, count = parse_annotations(envelope.get("record"), query["ncbi_gene_id"])
    export_hash = "sha256:" + hashlib.sha256(envelope["record"].encode()).hexdigest()
    assertions = []
    for row in rows:
        assertion = make_source_assertion(
            "annotations.gene_phenotype_associations",
            dict(zip(COLUMNS, row["fields"], strict=True)),
            "HPO",
            f"{expected['release']}:{export_hash}:line:{row['line']}",
            envelope.get("retrieved_at"),
            subject_ref=f"ncbigene:{query['ncbi_gene_id']}",
        )
        assertion["source"]["version"] = expected["release"]
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "export_hash": export_hash,
            "export_url": export_url(expected["release"]),
            "query": deepcopy(query),
            "received_export_count": count,
            "mapping_scope": {
                "identity": "native_NCBI_Gene_column; no_symbol_alias_or_protein_merge",
                "phenotype": "native_gene_disease_annotation; no_ancestor_expansion_or_new_logical_relationship",
                "frequency": "unchanged_disease_annotation_literal; not_gene_penetrance_or_patient_prediction",
                "support": "six_column_summary; per_occurrence_contributor_publication_evidence_modifiers_not_stated",
                "revision": "dated_release_route; individual_gene_ontology_annotation_input_revisions_not_stated",
                "coverage": "all_received_rows_validated; no_native_total_or_current_database_completeness_claim",
                "terms": "HPO_Consortium_attribution_version_and_unchanged_content; contributor_rights_separate; local_unreleased",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
