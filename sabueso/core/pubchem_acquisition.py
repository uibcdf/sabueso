"""Observe PubChem lookups and BioAssay batches without changing their results."""

import csv
import io
from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_responses = ContextVar("sabueso_pubchem_responses", default=None)


def note_response(path, payload):
    responses = _responses.get()
    if responses is not None:
        responses.append((path, deepcopy(payload)))


def observe(operation, *, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            responses = []
            token = _responses.set(responses)

            def summary(result, query, is_fixture, requests):
                return summarize(
                    result, query, is_fixture, requests, operation, responses
                )

            try:
                return acquisition(
                    "PubChem BioAssay" if operation == "assays" else "PubChem",
                    operation,
                    fixture=fixture,
                    summarize=summary,
                )(function)(*args, **kwargs)
            finally:
                _responses.reset(token)

        return observed

    return decorate


def _rows(table, accession):
    columns = (table.get("Columns") or {}).get("Column") or []
    rows = [dict(zip(columns, row.get("Cell") or [])) for row in table.get("Row") or []]
    return [r for r in rows if r.get("Target Accession") in (accession, "", None)]


def _publications(rows):
    return sorted(
        {
            str(r["PubMed ID"])
            for r in rows
            if str(r.get("PubMed ID") or "").isdigit() and int(r["PubMed ID"]) > 0
        }
    )


def _assay_versions(summaries):
    entries, versions = [], {}
    for summary in summaries:
        aid = str(summary["AID"])
        revision = {
            k: deepcopy(summary[k])
            for k in ("Version", "Revision", "LastDataChange")
            if summary.get(k) is not None
        }
        if "Version" in revision and "Revision" in revision:
            versions[aid] = revision
        entries.append(
            {
                "aid": aid,
                "source_version": {
                    "value": revision if aid in versions else None,
                    "basis": "assay_revision" if aid in versions else "not_stated",
                },
                "revision_metadata": revision,
                "depositor": {
                    k: deepcopy(summary[k])
                    for k in ("SourceName", "SourceID")
                    if summary.get(k) is not None
                },
                "response_identity": {
                    "basis": "decoded_assay_summary",
                    "hash": digest(canonical_json(summary)),
                },
            }
        )
    return entries, {
        "value": versions or None,
        "basis": "per_assay_revision" if versions else "not_stated",
    }


def summarize(result, query, fixture, requests, operation, responses):
    failed = isinstance(result, Exception)
    pages, summaries, received_rows = [], [], []
    for path, payload in responses:
        page = {
            "path": path,
            "response_identity": {
                "basis": "decoded_api_response",
                "hash": digest(canonical_json(payload)),
            },
        }
        if path.endswith("concise/CSV"):
            reader = csv.reader(io.StringIO(payload))
            columns = next(reader, [])
            all_rows = [
                dict(zip(columns, cells)) for cells in reader if cells and cells[0]
            ]
            rows = [
                r
                for r in all_rows
                if r.get("Target Accession") in (query["accession"], "", None)
            ]
            received_rows.extend(rows)
            page.update(
                kind="target_rows",
                count=len(rows),
                returned_rows=len(all_rows),
                columns=columns,
                publication_ids=_publications(rows),
            )
        elif "/summary/" in path:
            items = payload["AssaySummaries"]["AssaySummary"]
            summaries.extend(items)
            page.update(
                kind="assay_summaries", count=len(items), summaries=deepcopy(items)
            )
        elif "/property/" in path:
            items = (payload.get("PropertyTable") or {}).get("Properties") or []
            page.update(
                kind="compound_properties",
                count=len(items),
                cids=[str(p["CID"]) for p in items if "CID" in p],
            )
        else:
            page["kind"] = "structure_match"
        pages.append(page)

    terminal = _terminal(result, fixture, requests) if failed else None
    if failed:
        outcome = terminal
        # A missing/empty result keeps its native absence semantics. Otherwise a
        # later failing batch must not erase received source content.
        if pages and (
            not isinstance(result, RecordNotFoundError)
            or (requests and requests[-1]["outcome"] == "failed")
        ):
            outcome = "partial"
        if operation == "compound" and any(r.get("status") == 400 for r in requests):
            outcome = "rejected"
        count = len(received_rows) if operation == "assays" else 0
        payload = {"completed_pages": pages, "error": type(result).__name__}
    else:
        payload = result
        if operation == "compound":
            compound = result.get("record") or {}
            count = len(
                (compound.get("PropertyTable") or {}).get("Properties")
                or compound.get("PC_Compounds")
                or []
            )
        elif operation == "structure_match":
            count = len(result.get("cids") or [])
        else:
            record = result.get("record") or {}
            count = record.get("rows", 0)
            summaries = deepcopy(record.get("summaries") or [])
            received_rows = [
                row
                for table in (record.get("concise") or {}).values()
                for row in _rows(table, query["accession"])
            ]
        outcome = "received" if count else "empty"
        if operation == "compound" and compound.get("Fault"):
            outcome = "rejected"
        if operation == "structure_match":
            if result.get("fault"):
                outcome = "rejected"
            elif any(r.get("status") == 404 for r in requests):
                outcome = "not_found"

    metadata = {
        "outcome": outcome,
        "count": count,
        "source_version": {"value": None, "basis": "not_stated"},
        "pages": pages,
        "completed_pages": deepcopy(pages),
        "response_identity": {
            "basis": "decoded_completed_pages" if failed else "decoded_client_result",
            "hash": digest(canonical_json(payload)),
        },
    }
    if not failed:
        metadata["retrieved_at"] = result.get("retrieved_at")
        if operation == "structure_match":
            metadata.update(
                cids=deepcopy(result.get("cids") or []), fault=result.get("fault")
            )
    else:
        metadata.update(terminal_outcome=terminal, incomplete=outcome == "partial")
    if operation == "assays":
        entries, version = _assay_versions(summaries)
        metadata.update(
            assays=entries,
            source_version=version,
            publication_ids=_publications(received_rows),
        )
        if not failed:
            record = result.get("record") or {}
            metadata.update(
                total_count=record.get("total_rows"),
                truncated=record.get("total_rows", 0) > count,
                row_order=record.get("row_order"),
                aids=deepcopy(record.get("aids") or []),
            )
        else:
            metadata["count_basis"] = "received_target_rows_before_completion"
    return metadata
