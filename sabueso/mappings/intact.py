"""Native IntAct MITAB observations, without inferred binary binding relationships."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

LIMIT = 200  # Sabueso's single-page ceiling, not a claimed service limit.
ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-[1-9][0-9]*)?\Z"
)
HEADERS = (
    "X-PSICQUIC-Count",
    "X-PSICQUIC-Impl",
    "X-PSICQUIC-Impl-Version",
    "X-PSICQUIC-Spec-Version",
)
COLUMNS = (
    "id_a",
    "id_b",
    "alt_id_a",
    "alt_id_b",
    "alias_a",
    "alias_b",
    "detection_method",
    "first_author",
    "publication",
    "taxon_a",
    "taxon_b",
    "interaction_type",
    "source_database",
    "interaction_id",
    "confidence",
    "complex_expansion",
    "biological_role_a",
    "biological_role_b",
    "experimental_role_a",
    "experimental_role_b",
    "participant_type_a",
    "participant_type_b",
    "xref_a",
    "xref_b",
    "interaction_xref",
    "annotation_a",
    "annotation_b",
    "interaction_annotation",
    "host_taxon",
    "parameters",
    "creation_date",
    "update_date",
    "checksum_a",
    "checksum_b",
    "interaction_checksum",
    "negative",
    "features_a",
    "features_b",
    "stoichiometry_a",
    "stoichiometry_b",
    "participant_detection_a",
    "participant_detection_b",
)
_ATOM = r'(?:"(?:[^"\\]|\\.)*"|[^:"|()]+)'
_REFERENCE = re.compile(rf"({_ATOM}):({_ATOM})(?:\(.*\))?\Z")


def accession(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier.upper()):
        raise ConnectorError(
            "IntAct requires one UniProt accession, optionally an isoform."
        )
    return identifier.upper()


def page_limit(limit):
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= LIMIT:
        raise ConnectorError(f"IntAct requires a single-page limit from 1 to {LIMIT}.")
    return limit


def response_query(identifier, limit):
    return {
        "miql": f"id:{accession(identifier)}",
        "format": "tab27",
        "first_result": 0,
        "max_results": page_limit(limit),
    }


def _references(cell):
    """Parse identifier cells only; quoted pipes/colons retain their native token.

    Other MITAB cells remain literal, including CV terms, free text and scores.
    Unsupported identifier syntax fails rather than removing database namespaces.
    """
    if cell == "-":
        return []
    tokens, start, quoted, escaped = [], 0, False, False
    for index, char in enumerate(cell):
        if escaped:
            escaped = False
        elif char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == "|" and not quoted:
            tokens.append(cell[start:index])
            start = index + 1
    if quoted or escaped:
        raise ConnectorError("IntAct identifier cell has unbalanced quoting.")
    tokens.append(cell[start:])
    references = []
    for token in tokens:
        match = _REFERENCE.fullmatch(token)
        if match is None:
            raise ConnectorError("IntAct identifier cell has unsupported syntax.")
        try:
            namespace, identifier = (
                json.loads(value) if value.startswith('"') else value
                for value in match.groups()
            )
        except ValueError as error:
            raise ConnectorError("IntAct quoted identifier is unreadable.") from error
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", namespace) or not identifier:
            raise ConnectorError("IntAct identifier namespace/value is invalid.")
        references.append(
            {"namespace": namespace, "identifier": identifier, "native": token}
        )
    return references


def parse_page(document, headers, native_query, identifier, limit):
    """Validate every native row before applying the caller's result cap."""
    identifier, limit = accession(identifier), page_limit(limit)
    if (
        not isinstance(native_query, dict)
        or type(native_query.get("first_result")) is not int
        or native_query != response_query(identifier, native_query.get("max_results"))
    ):
        raise ConnectorError("IntAct native query identity/format/page is unsupported.")
    if native_query["max_results"] < limit:
        raise ConnectorError("IntAct supplied page cannot satisfy the requested scope.")
    if not isinstance(headers, dict) or set(headers) - set(HEADERS):
        raise ConnectorError("IntAct response count/service headers are unsupported.")
    count = headers.get("X-PSICQUIC-Count")
    if not isinstance(count, str) or not re.fullmatch(r"[0-9]+", count):
        raise ConnectorError("IntAct requires its native total-result count header.")
    if any(not isinstance(v, str) or not v for v in headers.values()):
        raise ConnectorError("IntAct service headers are malformed.")
    if not isinstance(document, str):
        raise ConnectorError("IntAct requires unchanged native MITAB text.")
    rows = []
    for index, line in enumerate(document.splitlines()):
        cells = line.split("\t")
        if len(cells) != len(COLUMNS) or any(not cell for cell in cells):
            raise ConnectorError(
                "IntAct MITAB 2.7 row must contain 42 nonempty native cells."
            )
        native = dict(zip(COLUMNS, cells))
        if native["negative"] not in {"true", "false", "-"}:
            raise ConnectorError("IntAct negative flag is malformed.")
        matches = []
        for column in ("id_a", "id_b", "alt_id_a", "alt_id_b"):
            for offset, ref in enumerate(_references(native[column])):
                if ref["namespace"] == "uniprotkb" and ref["identifier"] == identifier:
                    matches.append(
                        {"column": column, "alternative_index": offset, **ref}
                    )
        if not matches:
            raise ConnectorError(
                "IntAct returned a row without the exact requested UniProt reference."
            )
        interaction_ids = _references(native["interaction_id"])
        if not interaction_ids:
            raise ConnectorError("IntAct native interaction identifiers are missing.")
        rows.append(
            {
                "index": index,
                "line": line,
                "native": native,
                "query_matches": matches,
                "interaction_ids": interaction_ids,
            }
        )
    total = int(count)
    if len(rows) != min(total, native_query["max_results"]):
        raise ConnectorError(
            "IntAct native page row count differs from its declared scope."
        )
    selected = rows[:limit]
    scope = {
        "basis": "intact_mitab_page@1",
        "total_results": total,
        "observed_rows": len(rows),
        "returned_rows": len(selected),
        "first_result": 0,
        "max_results": native_query["max_results"],
        "requested_limit": limit,
        "truncated": len(selected) < total,
        "count_semantics": "MIQL_result_rows; not_unique_partners_or_complete_biological_coverage",
    }
    return selected, scope


def _validated(envelope):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "IntAct"
        or envelope.get("kind") != "interactions"
        or envelope.get("version") is not None
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("IntAct mapping requires its native interaction envelope.")
    query = envelope["query"]
    identifier = accession(query.get("accession"))
    rows, scope = parse_page(
        envelope.get("record"),
        envelope.get("response_headers"),
        envelope.get("response_query"),
        identifier,
        query.get("limit"),
    )
    if (
        envelope.get("scope") != scope
        or envelope.get("truncated") is not scope["truncated"]
    ):
        raise ConnectorError(
            "IntAct envelope scope differs from the original response."
        )
    return identifier, rows, scope


def map_interactions(envelope):
    """One source-scoped observation per result occurrence; no partner identity merge.

    All 42 columns stay literal. Negation, association/proximity, complex expansion,
    participant roles and native confidence are not rewritten as direct binding,
    an experimental class or a calibrated probability. Alias/xref columns are never
    used to bind the requested protein. Source sequence/record revisions are unknown.
    """
    identifier, rows, scope = _validated(envelope)
    document_hash = hashlib.sha256(envelope["record"].encode("utf-8")).hexdigest()
    assertions = []
    for row in rows:
        row_hash = hashlib.sha256(row["line"].encode("utf-8")).hexdigest()
        value = {
            "query_ref": f"uniprot:{identifier}",
            "query_matches": deepcopy(row["query_matches"]),
            "native": deepcopy(row["native"]),
        }
        assertion = make_source_assertion(
            "interactions.observations.intact",
            value,
            "IntAct",
            f"{identifier}:row:{row['index']}:{row_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"uniprot:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "record_id_basis": "query_page_row_locator; native_interaction_ids_retained_separately",
            "native_interaction_ids": deepcopy(row["interaction_ids"]),
            "native_row_index": row["index"],
            "native_row": row["line"],
            "native_row_sha256": row_hash,
            "document_sha256": document_hash,
            "response_query": deepcopy(envelope["response_query"]),
            "response_headers": deepcopy(envelope["response_headers"]),
            "scope": deepcopy(scope),
            "mapping_scope": {
                "identity": "exact_uniprotkb_declaration_in_primary_or_alternative_ID_cell; no_alias_or_xref_merge",
                "classification": "native_method_type_negation_and_expansion_only; no_universal_experimental_or_direct_class",
                "revision": "not_stated; service_versions_and_native_dates_are_separate",
                "parameters": "native_literals_only; units_and_canonical_feature_placement_not_inferred",
                "support": "native_publication_pointers; linked_articles_not_acquired",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
