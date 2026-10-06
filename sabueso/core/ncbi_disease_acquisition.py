"""Observe NCBI disease queries without treating search hits as identity evidence."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .errors import ConnectorError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_pages = ContextVar("sabueso_ncbi_disease_pages", default=None)


def note_page(path, query, payload, *, fixture=False, valid=False):
    receipt = {
        "endpoint": path,
        "query": deepcopy(query),
        "response_identity": {
            "basis": "decoded_fixture_envelope"
            if fixture
            else "decoded_eutilities_page",
            "hash": digest(canonical_json(payload)),
        },
        "outcome": "received" if valid else "unobserved",
    }
    pages = _pages.get()
    if pages is not None:
        pages.append(receipt)
    return receipt


def validate(source, path, params, payload):
    """Require a declared native answer; missing protocol fields are not absence."""
    receipt = note_page(path, params, payload)
    root = {
        "einfo.fcgi": "einforesult",
        "esearch.fcgi": "esearchresult",
        "esummary.fcgi": "result",
    }[path]
    native = payload.get(root) if isinstance(payload, dict) else None
    if (
        not isinstance(native, dict)
        or payload.get("error")
        or native.get("error")
        or native.get("ERROR")
    ):
        raise ConnectorError(f"{source} {path} has no valid {root} answer")
    if path == "einfo.fcgi":
        info = native.get("dbinfo")
        if (
            not isinstance(info, list)
            or len(info) != 1
            or not isinstance(info[0], dict)
        ):
            raise ConnectorError(f"{source} einfo has no database metadata")
        field = "dbbuild" if source == "ClinVar" else "lastupdate"
        version = info[0].get(field)
        if version is not None and not isinstance(version, str):
            raise ConnectorError(f"{source} einfo has an invalid {field}")
        receipt["source_version"] = {
            "value": version,
            "basis": field if version is not None else "not_stated",
        }
    elif path == "esearch.fcgi":
        ids, count = native.get("idlist"), native.get("count")
        if (
            not isinstance(ids, list)
            or not all(isinstance(uid, str) and uid.isdigit() for uid in ids)
            or len(set(ids)) != len(ids)
        ):
            raise ConnectorError(f"{source} esearch has an invalid id list")
        if (
            not isinstance(count, (str, int))
            or isinstance(count, bool)
            or not str(count).isdigit()
            or int(count) < len(ids)
        ):
            raise ConnectorError(f"{source} esearch has an invalid result count")
        if len(ids) != min(int(count), int(params["retmax"])):
            raise ConnectorError(f"{source} esearch omitted requested result ids")
        receipt.update(
            total_count=int(count),
            count=len(ids),
            row_order=list(ids),
            truncated=int(count) > len(ids),
        )
    else:
        ids = native.get("uids")
        requested = params["id"].split(",")
        if (
            not isinstance(ids, list)
            or not all(isinstance(uid, str) for uid in ids)
            or len(ids) != len(set(ids))
            or set(ids) != set(requested)
        ):
            raise ConnectorError(
                f"{source} esummary did not return exactly the requested UIDs"
            )
        if any(
            not isinstance(native.get(uid), dict) or native[uid].get("error")
            for uid in ids
        ):
            raise ConnectorError(f"{source} esummary has an invalid UID record")
        receipt.update(count=len(ids), row_order=list(ids))
        if source == "MedGen":
            if any(
                not isinstance(native[uid].get("conceptid"), str)
                or not native[uid]["conceptid"]
                for uid in ids
            ):
                raise ConnectorError("MedGen summary has no stated concept identity")
            receipt["identity_pairs"] = [
                {"concept_id": native[uid]["conceptid"], "uid": uid} for uid in ids
            ]
        else:
            for uid in ids:
                row = native[uid]
                if str(row.get("uid")) != uid:
                    raise ConnectorError(
                        "ClinVar summary UID contradicts its native record key"
                    )
                classification = row.get("germline_classification")
                if classification is not None and not isinstance(classification, dict):
                    raise ConnectorError(
                        "ClinVar summary has an invalid classification"
                    )
                for owner, field in (
                    (row, "variation_set"),
                    (classification or {}, "trait_set"),
                ):
                    value = owner.get(field)
                    if value is not None and (
                        not isinstance(value, list)
                        or not all(isinstance(item, dict) for item in value)
                    ):
                        raise ConnectorError(f"ClinVar summary has an invalid {field}")
            receipt["variant_versions"] = [
                {
                    "uid": uid,
                    "accession": native[uid].get("accession"),
                    "accession_version": native[uid].get("accession_version"),
                }
                for uid in ids
            ]
    receipt["outcome"] = "received"
    return native


def note_fixture(query, payload, source):
    receipt = note_page("fixture", query, payload, fixture=True, valid=True)
    record = payload["record"]
    receipt.update(
        count=len(record),
        source_version={
            "value": payload.get("version"),
            "basis": "fixture_declared_version"
            if payload.get("version") is not None
            else "not_stated",
        },
    )
    if source == "ClinVar":
        record = record[: query["limit"]]
        receipt.update(
            count=len(record),
            total_count=payload["total_count"],
            row_order=[row.get("uid") for row in record],
            variant_versions=[
                {key: row.get(key) for key in ("uid", "accession", "accession_version")}
                for row in record
            ],
        )
    else:
        record = {c: uid for c, uid in record.items() if c in query["concept_ids"]}
        receipt["count"] = len(record)
        receipt["identity_pairs"] = [
            {"concept_id": concept, "uid": uid} for concept, uid in record.items()
        ]


def observe(source, operation, *, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            # Materialize only the iterable arguments once, before provenance copies them.
            args = list(args)
            name = "gene_ids" if source == "ClinVar" else "concept_ids"
            if len(args) > 1:
                args[1] = list(args[1])
            elif name in kwargs:
                kwargs[name] = list(kwargs[name])
            pages = []
            token = _pages.set(pages)
            try:
                return acquisition(
                    source,
                    operation,
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: summarize(
                        source, result, query, local, requests, pages
                    ),
                )(function)(*args, **kwargs)
            finally:
                _pages.reset(token)

        return observed

    return decorate


def summarize(source, result, query, fixture, requests, pages):
    from sabueso.tools.db.medgen import _ids

    failed = isinstance(result, Exception)
    completed = [page for page in pages if page["outcome"] == "received"]
    data_pages = [
        page for page in completed if page["endpoint"] in ("esummary.fcgi", "fixture")
    ]
    searches = [page for page in completed if page["endpoint"] == "esearch.fcgi"]
    versions = [
        page["source_version"]["value"]
        for page in completed
        if "source_version" in page
    ]
    names = "gene_ids" if source == "ClinVar" else "concept_ids"
    normalized = (
        sorted({str(g) for g in query[names] if g})
        if source == "ClinVar"
        else _ids(query[names])
    )
    count = (
        sum(page["count"] for page in data_pages) if failed else len(result["record"])
    )
    terminal = _terminal(result, fixture, requests) if failed else None
    outcome = (
        ("partial" if completed else terminal)
        if failed
        else "not_queried"
        if not normalized
        else "received"
        if count
        else "empty"
    )
    version = versions[-1] if versions and len(set(versions)) == 1 else None
    basis = (
        "fixture_declared_version"
        if fixture
        else "ncbi_database_build"
        if source == "ClinVar"
        else "ncbi_database_lastupdate"
    )
    metadata = {
        "outcome": outcome,
        "count": count,
        "count_basis": "returned_summaries_per_gene; overlapping_UIDs_not_deduplicated"
        if source == "ClinVar"
        else "returned_source_stated_concept_UID_pairs",
        "normalized_query": {
            names: normalized,
            **({"limit": query["limit"]} if source == "ClinVar" else {}),
        },
        "pages": deepcopy(pages),
        "completed_pages": deepcopy(completed),
        "source_version": {
            "value": version,
            "basis": basis if version is not None else "not_stated",
        },
        "total_count": sum(page["total_count"] for page in searches)
        if searches
        else result.get("total_count")
        if not failed
        else None,
        "incomplete": failed
        or (result.get("truncated", False) if not failed else False),
        "truncated": any(page.get("truncated") for page in searches)
        or (result.get("truncated", False) if not failed else False),
        "effective_limit": query["limit"] if source == "ClinVar" else 1000,
        "cutoff_scope": "per_gene_search"
        if source == "ClinVar"
        else "per_concept_batch_search; incomplete_search_refused",
        "response_identity": {
            "basis": "completed_page_receipts" if failed else "decoded_client_record",
            "hash": digest(canonical_json(completed if failed else result["record"])),
        },
        "association_context": {
            "scope": "fixture_subset" if fixture else "queried_eutilities_pages",
            "identity_basis": "native_NCBI_Gene_query_and_ClinVar_UID_accession_versions"
            if source == "ClinVar"
            else "native_MedGen_conceptid_to_UID; names_and_similarity_not_matched",
            "reference_basis": "summary_only; submission_publications_not_fetched"
            if source == "ClinVar"
            else "identity_lookup_only; underlying_terminology_citations_not_fetched",
            "absence_basis": "queried_ids_only; fixture_subset_not_global_absence",
            "versions_consistent": len(set(versions)) <= 1,
            "variant_versions": [
                row for page in data_pages for row in page.get("variant_versions", [])
            ],
            "identity_pairs": [
                row for page in data_pages for row in page.get("identity_pairs", [])
            ],
        },
    }
    if failed:
        metadata["terminal_outcome"] = terminal
    else:
        metadata["retrieved_at"] = result["retrieved_at"]
        metadata["missing"] = result.get("missing", [])
    return metadata
