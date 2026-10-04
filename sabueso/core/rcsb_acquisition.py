"""RCSB client results retain entry revisions and distinct per-entry outcomes."""

from copy import deepcopy

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal


def summarize(result, query, fixture, requests):
    """A logical lookup owns all transport attempts, including batch fallbacks.

    Child lookups are aggregated by the acquisition decorator. Failed or missing
    entries never acquire a successful entry identity or a primary publication.
    """
    single = "pdb_id" in query
    results = (
        {query["pdb_id"].upper(): result}
        if single
        else dict.fromkeys(query["pdb_ids"], result)
        if isinstance(result, Exception)
        else result
    )
    entries, payload, versions = [], {}, {}
    for pdb_id, response in results.items():
        item = {"pdb_id": pdb_id}
        if isinstance(response, Exception):
            outcome = _terminal(response, fixture, requests)
            # GraphQL reports entry absence in a decoded answer, not an HTTP 404.
            if isinstance(response, RecordNotFoundError) and not fixture:
                outcome = "empty" if requests else "unobserved"
            item.update(
                outcome=outcome,
                error={"type": type(response).__name__, "message": str(response)},
            )
            payload[pdb_id] = {"error": item["error"]}
        else:
            entry, retrieved = response
            info = entry.get("rcsb_accession_info") or {}
            revision = {
                key: deepcopy(info[key])
                for key in ("major_revision", "minor_revision", "revision_date")
                if info.get(key) is not None
            }
            version = (
                {"value": revision, "basis": "entry_revision"}
                if "major_revision" in revision and "minor_revision" in revision
                else {"value": None, "basis": "not_stated"}
            )
            item.update(
                outcome="partial" if entry.get("_partial") else "received",
                retrieved_at=retrieved,
                source_version=version,
                revision_metadata=revision,
                primary_citation=deepcopy(entry.get("rcsb_primary_citation")),
                response_identity={
                    "basis": "decoded_entry",
                    "hash": digest(canonical_json(entry)),
                },
            )
            if entry.get("_partial"):
                item["partial"] = deepcopy(entry["_partial"])
            if version["value"] is not None:
                versions[pdb_id] = version["value"]
            payload[pdb_id] = entry
        entries.append(item)
    outcomes = {item["outcome"] for item in entries}
    outcome = (
        next(iter(outcomes))
        if len(outcomes) == 1
        else "partial"
        if outcomes
        else "not_queried"
    )
    completed = [
        item["pdb_id"]
        for item in entries
        if item["outcome"] in {"received", "partial", "empty"}
    ]
    version = (
        entries[0].get("source_version", {"value": None, "basis": "not_stated"})
        if single
        else {"value": versions, "basis": "per_entry_revision"}
        if versions
        else {"value": None, "basis": "not_stated"}
    )
    from sabueso.tools.db import _http

    fallback_retrieved = _http._STAMP.get().value if requests and not fixture else None
    return {
        "outcome": outcome,
        "count": sum(item["outcome"] in {"received", "partial"} for item in entries),
        "entries": entries,
        "completed_ids": completed,
        "source_version": version,
        "retrieved_at": next(
            (item["retrieved_at"] for item in entries if "retrieved_at" in item),
            next(
                (r.get("retrieved_at") for r in requests if r.get("retrieved_at")),
                fallback_retrieved,
            ),
        ),
        "response_identity": {
            "basis": "decoded_client_result",
            "hash": digest(
                canonical_json(next(iter(payload.values())) if single else payload)
            ),
        },
    }
