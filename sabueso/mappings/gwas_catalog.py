"""Native GWAS association occurrences on an explicit standard mapped-gene page."""

from __future__ import annotations

import re
from copy import deepcopy
from urllib.parse import parse_qs, urlsplit

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

URL = "https://www.ebi.ac.uk/gwas/rest/api/v2/associations"
GENE = re.compile(r"[A-Z][A-Za-z0-9_-]{0,63}\Z")
STUDY = re.compile(r"GCST[0-9]+\Z")


def response_query(identifier, limit, page):
    if not isinstance(identifier, str) or not GENE.fullmatch(identifier):
        raise ConnectorError("GWAS requires one exact standard mapped-gene symbol.")
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ConnectorError("GWAS reader limit must be an integer from 1 to 500.")
    if type(page) is not int or page < 0:
        raise ConnectorError("GWAS page must be a nonnegative integer.")
    return {
        "mapped_gene": identifier,
        "extended_geneset": "false",
        "page": page,
        "size": limit,
    }


def page_rows(payload):
    return payload.get("_embedded", {}).get("associations", [])


def page_is_partial(payload):
    return len(page_rows(payload)) < payload["page"]["totalElements"]


def _links(links):
    if not isinstance(links, dict):
        raise ConnectorError("GWAS native HAL links are malformed.")
    for link in links.values():
        if not isinstance(link, dict) or not isinstance(link.get("href"), str):
            raise ConnectorError("GWAS native HAL link is malformed.")
    return links


def _page_link(link, query, number):
    try:
        parts = urlsplit(link["href"])
        scope = parse_qs(parts.query, keep_blank_values=True, strict_parsing=True)
    except (KeyError, TypeError, ValueError) as error:
        raise ConnectorError("GWAS page link is missing or malformed.") from error
    expected = {k: [str(v)] for k, v in {**query, "page": number}.items()}
    if (
        parts.scheme != "https"
        or parts.netloc != "www.ebi.ac.uk"
        or parts.path != "/gwas/rest/api/v2/associations"
        or parts.fragment
        or scope != expected
    ):
        raise ConnectorError("GWAS native page link changes the exact query scope.")


def validate_page(payload, identifier, limit, page):
    """Validate native HAL shape, page/link/query binding and every association."""
    query = response_query(identifier, limit, page)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("GWAS response is not finite JSON.") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("page"), dict):
        raise ConnectorError("GWAS response must be its native HAL page.")
    metadata = payload["page"]
    for k in ("size", "number", "totalElements", "totalPages"):
        if type(metadata.get(k)) is not int or metadata[k] < 0:
            raise ConnectorError("GWAS page counts are missing or malformed.")
    total = metadata["totalElements"]
    pages = (total + limit - 1) // limit
    if (
        metadata["size"] != limit
        or metadata["number"] != page
        or metadata["totalPages"] != pages
    ):
        raise ConnectorError("GWAS native page scope/counts differ from the request.")
    if "_embedded" in payload and (
        not isinstance(payload["_embedded"], dict)
        or not isinstance(payload["_embedded"].get("associations"), list)
    ):
        raise ConnectorError("GWAS embedded association array is malformed.")
    rows = page_rows(payload)
    expected_count = max(0, min(limit, total - page * limit))
    if len(rows) != expected_count:
        raise ConnectorError("GWAS page counts contradict received occurrences.")
    links = _links(payload.get("_links"))
    _page_link(links.get("self", {}), query, page)
    targets = {"first": 0, "last": max(0, pages - 1)}
    if page + 1 < pages:
        targets["next"] = page + 1
        if "next" not in links:
            raise ConnectorError("GWAS partial page omits its native next link.")
    if page > 0:
        targets["prev"] = page - 1
    for relation in ("first", "last", "next", "prev"):
        if relation in links:
            if relation not in targets:
                raise ConnectorError("GWAS page link contradicts native coverage.")
            _page_link(links[relation], query, targets[relation])
    for row in rows:
        if not isinstance(row, dict):
            raise ConnectorError("GWAS native association is malformed.")
        if type(row.get("association_id")) is not int or row["association_id"] <= 0:
            raise ConnectorError("GWAS association identity is missing or malformed.")
        if not isinstance(row.get("accession_id"), str) or not STUDY.fullmatch(
            row["accession_id"]
        ):
            raise ConnectorError("GWAS study identity is missing or malformed.")
        for k in ("mapped_genes", "reported_trait", "locations", "snp_effect_allele"):
            if k not in row or (
                not isinstance(row[k], list)
                or any(not isinstance(v, str) or not v for v in row[k])
            ):
                raise ConnectorError(
                    "GWAS native gene/trait/variant list is malformed."
                )
        if identifier not in row["mapped_genes"]:
            raise ConnectorError("GWAS row does not state the exact mapped-gene query.")
        for k in (
            "risk_frequency",
            "pvalue_description",
            "range",
            "beta",
            "snp_type",
            "description",
            "or_value",
            "beta_unit",
            "beta_direction",
            "pubmed_id",
            "first_author",
            "last_mapping_date",
            "last_update_date",
        ):
            if k in row and row[k] is not None and not isinstance(row[k], str):
                raise ConnectorError(
                    "GWAS native text/statistical context is malformed."
                )
        for k in ("pvalue_mantissa", "pvalue_exponent"):
            if k in row and row[k] is not None and type(row[k]) is not int:
                raise ConnectorError("GWAS original p-value components are malformed.")
        for k in (
            "p_value",
            "standard_error",
            "or_per_copy_num",
            "beta_num",
            "ci_lower",
            "ci_upper",
        ):
            if k in row and row[k] is not None and type(row[k]) not in (int, float):
                raise ConnectorError("GWAS native numeric context is malformed.")
        for k in ("multi_snp_haplotype", "snp_interaction"):
            if k in row and row[k] is not None and type(row[k]) is not bool:
                raise ConnectorError(
                    "GWAS native haplotype/interaction flag is malformed."
                )
        for k, fields in (
            ("efo_traits", ("efo_id", "efo_trait")),
            ("bg_efo_traits", ("efo_id", "efo_trait")),
            ("snp_allele", ("rs_id", "effect_allele")),
        ):
            if k in row and row[k] is not None:
                if not isinstance(row[k], list):
                    raise ConnectorError("GWAS native trait/allele array is malformed.")
                for item in row[k]:
                    if not isinstance(item, dict) or any(
                        not isinstance(item.get(f), str) or not item[f] for f in fields
                    ):
                        raise ConnectorError(
                            "GWAS native trait/allele object is malformed."
                        )
        native_links = _links(row.get("_links"))
        if native_links.get("self", {}).get("href") != f"{URL}/{row['association_id']}":
            raise ConnectorError(
                "GWAS native association self link changes its identity."
            )
    return payload


def map_associations(envelope):
    """Retain occurrences without causal-gene, protein or statistical interpretation."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "GWAS Catalog"
        or envelope.get("kind") != "mapped_gene_associations"
        or envelope.get("version") is not None
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError(
            "GWAS mapping requires a native mapped-gene page envelope."
        )
    query = envelope["query"]
    expected = response_query(
        query.get("mapped_gene"), query.get("size"), query.get("page")
    )
    if query != expected:
        raise ConnectorError("GWAS query scope is unsupported.")
    record = validate_page(
        envelope.get("record"), query["mapped_gene"], query["size"], query["page"]
    )
    if envelope.get("truncated") is not page_is_partial(record):
        raise ConnectorError("GWAS envelope cut differs from native page coverage.")
    response_hash, query_hash = (
        digest(canonical_json(record)),
        digest(canonical_json(query)),
    )
    assertions = []
    for index, row in enumerate(page_rows(record)):
        assertion = make_source_assertion(
            "genetics.gwas_associations",
            deepcopy(row),
            "GWAS Catalog",
            f"{query_hash}:{response_hash}:row:{index}:{row['association_id']}",
            envelope.get("retrieved_at"),
            subject_ref=f"gwas:association:{row['association_id']}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_association": deepcopy(row),
            "native_row_index": index,
            "response_hash": response_hash,
            "query": deepcopy(query),
            "page": {
                **deepcopy(record["page"]),
                "returned": len(page_rows(record)),
                "partial": page_is_partial(record),
            },
            "native_page_links": deepcopy(record["_links"]),
            "mapping_scope": {
                "gene": "literal_standard_mapped_gene_filter; no_causal_gene_or_protein_identity_claim",
                "statistics": "original_mantissa_exponent_numeric_and_text_fields; no_ranking_recalculation_or_unit_guess",
                "variant": "native_study_trait_allele_location_and_haplotype_scope; assembly_and_sequence_revisions_not_stated",
                "revision": "API_v2_and_native_mapping_dates_are_not_dataset_or_association_revisions",
                "coverage": "one_received_page; no_implicit_continuation_or_absence_claim",
                "terms": "EBI_services_terms_and_original_owner_rights; summary_statistics_CC0_is_separate",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
