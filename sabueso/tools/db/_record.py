"""The provenance envelope every public source function returns (uibcdf/sabueso#49).

``{"source", "kind", "query", "retrieved_at", "version", "record"}``: the record as the
source gave it, what was asked, when, and from which release (None when the source does
not state one). Records are raw: turning them into knowledge is the mappings' job.
A source that cut its answer adds ``"truncated": True`` (and states it ``False`` when it
checked and did not cut).
"""

from __future__ import annotations

from typing import Any, Dict


def source_record(
    source: str,
    kind: str,
    query: Dict[str, Any],
    retrieved_at: str | None,
    version: Any,
    record: Any,
    truncated: bool | None = None,
) -> Dict[str, Any]:
    envelope = {
        "source": source,
        "kind": kind,
        "query": query,
        "retrieved_at": retrieved_at,
        "version": None if version is None else str(version),
        "record": record,
    }
    if truncated is not None:
        # The source holds more than the record: a cut never passes for the whole.
        envelope["truncated"] = truncated
    return envelope


def online(client: Any, factory: Any) -> Any:
    """The given client, or the source's online client."""
    return client if client is not None else factory()
