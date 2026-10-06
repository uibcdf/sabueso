"""Observe DISEASES channel files, retaining each cached index's original receipt."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from hashlib import sha256

from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_channels = ContextVar("sabueso_diseases_channels", default=None)


class ObservedIndex(dict):
    def __init__(self, index, origin):
        super().__init__(index)
        self.origin = deepcopy(origin)


def origin(payload, retrieved_at, requests=(), *, fixture=False):
    return {
        "response_identity": {
            "basis": "tsv_file_bytes",
            "hash": sha256(payload).hexdigest(),
        },
        "retrieved_at": retrieved_at,
        "requests": deepcopy(list(requests)),
        "scope": "fixture_subset" if fixture else "downloaded_filtered_channel_file",
        "published_checksum": "not_stated",
    }


def note_channel(channel, version, index, *, access):
    state = _channels.get()
    if state is not None:
        state.append(
            {
                "channel": channel,
                "version": version,
                "index": index,
                "origin": deepcopy(getattr(index, "origin", None)),
                "access": access,
            }
        )


def observe(*, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            args = list(args)
            for position, name in ((1, "proteins"), (2, "channels")):
                if len(args) > position:
                    args[position] = list(args[position])
                elif name in kwargs:
                    kwargs[name] = list(kwargs[name])
            state = []
            token = _channels.set(state)
            try:
                return acquisition(
                    "DISEASES",
                    "associations",
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: summarize(
                        result, query, local, requests, state
                    ),
                )(function)(*args, **kwargs)
            finally:
                _channels.reset(token)

        return observed

    return decorate


def summarize(result, query, fixture, requests, state):
    failed = isinstance(result, Exception)
    ids = sorted({p.split(".")[0] for p in query["proteins"] if p})
    receipts, rows = [], []
    for channel in state:
        selected = [row for protein in ids for row in channel["index"].get(protein, [])]
        rows.extend(selected)
        receipts.append(
            {
                "channel": channel["channel"],
                "count": len(selected),
                "source_version": {
                    "value": channel["version"],
                    "basis": "fixture_declared_channel_date"
                    if fixture and channel["version"] is not None
                    else "HTTP_Last_Modified_date"
                    if channel["version"] is not None
                    else "not_stated",
                },
                "outcome": "received" if selected else "empty",
                "access": channel["access"],
                "index_origin": channel["origin"],
                "row_order": [
                    {
                        "protein": row["protein"],
                        "disease": row["disease"],
                        "source_database": row.get("source_database"),
                    }
                    for row in selected
                ],
                "response_identity": {
                    "basis": "decoded_selected_channel_rows",
                    "hash": digest(canonical_json(selected)),
                },
            }
        )
    dates = [(channel["origin"] or {}).get("retrieved_at") for channel in state]
    outcome = (
        ("partial" if receipts else _terminal(result, fixture, requests))
        if failed
        else "not_queried"
        if not query["channels"]
        else "received"
        if rows
        else "empty"
    )
    metadata = {
        "outcome": outcome,
        "count": len(rows) if receipts else 0 if not failed else None,
        "count_basis": "selected_native_channel_rows; channels_not_merged",
        "pages": receipts,
        "completed_pages": deepcopy(receipts),
        "normalized_query": {"proteins": ids, "channels": list(query["channels"])},
        "source_version": {
            "value": {channel["channel"]: channel["version"] for channel in state},
            "basis": "per_channel_publication_dates",
        },
        "incomplete": failed,
        "retrieved_at": min(dates) if dates and all(dates) else None,
        "retrieved_at_basis": "original_channel_responses"
        if dates and all(dates)
        else "original_channel_time_not_observed",
        "response_identity": {
            "basis": "completed_channel_receipts",
            "hash": digest(canonical_json(receipts)),
        },
        "association_context": {
            "scope": "fixture_subset"
            if fixture
            else "queried_filtered_channel_indexes",
            "identity_basis": "native_Ensembl_protein_ids; identifier_version_suffix_removed; names_not_matched",
            "absence_basis": "selected_filtered_channels_only; fixture_subset_not_global_absence",
            "score_basis": "native_channel_scores; knowledge_experiments_textmining_kept_separate",
            "reference_basis": "native_source_database_and_textmining_URL_pointers; publication_metadata_not_fetched",
            "reference_pointers": [
                {key: row[key] for key in ("source_database", "url") if key in row}
                for row in rows
            ],
            "client_retrieved_at": None if failed else result["retrieved_at"],
            "client_time_basis": "original_channel_responses"
            if dates and all(dates)
            else "query_clock_fallback_for_unobserved_cache_origin",
        },
    }
    if any(channel["access"] in ("memory", "disk") for channel in state):
        metadata["access"] = (
            "mixed"
            if requests
            else "fixture"
            if fixture
            else "memory"
            if all(channel["access"] == "memory" for channel in state)
            else "disk"
        )
    if failed:
        metadata["terminal_outcome"] = _terminal(result, fixture, requests)
    else:
        metadata["missing"] = result["missing"]
    return metadata
