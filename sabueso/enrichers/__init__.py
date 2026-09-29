"""Declared enrichers: one source's contribution to a card, and one runner (#86).

An enricher declares what the card-building code used to repeat per source: its option,
its source's name, its registry entry, the knowledge areas it answers, the organisms it
covers, and three steps:

- ``requests(context, options)``: what to ask (one request per gene, or one for the
  entry), each with the fields its enrichment record starts with. ``NothingToAsk`` when
  the entry states nothing to ask with (e.g. no Ensembl gene): ``not_found``, with the
  reason;
- ``fetch(client, request, options)``: the source client's call;
- ``map(context, request, response, options)``: the mapping, and the record's outcome
  (status, version, count, truncation).

The runner (``run``) does the rest, the same way for every source:
- organism coverage: ``not_applicable``, with the reason;
- ``RecordNotFoundError`` → ``not_found``, and ``ConnectorError`` → ``error``, per
  request, so one failing source or gene never hides another's knowledge;
- mappings and records in the declared order, so a card stays deterministic.

The knowledge-state rows and the migration map of enrichment records to options are
derived from ``ENRICHERS`` (``knowledge_areas``, ``options_by_source``), not kept by
hand. See ``devguide/SOURCE_ARCHITECTURE.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, Tuple

from sabueso.core.errors import ConnectorError, RecordNotFoundError


class NothingToAsk(Exception):
    """The entry states nothing this source can be asked with; the message says why."""


@dataclass
class Context:
    """What the card already states, computed once for every enricher."""

    anchor: str
    entry: Dict[str, Any]

    @property
    def taxon(self) -> int | None:
        return (self.entry.get("organism") or {}).get("taxonId")

    @property
    def sequence(self) -> str | None:
        return (self.entry.get("sequence") or {}).get("value")

    def xrefs(self, database: str) -> List[Dict[str, Any]]:
        return [
            x
            for x in self.entry.get("uniProtKBCrossReferences") or []
            if x.get("database") == database
        ]

    def xref_properties(self, database: str, key: str) -> List[Tuple[str, Any]]:
        """``(value, isoform)`` of a cross-reference property, e.g. Ensembl GeneId."""
        return [
            (p["value"], x.get("isoformId"))
            for x in self.xrefs(database)
            for p in x.get("properties") or []
            if p.get("key") == key and p.get("value")
        ]

    @cached_property
    def transcripts(self) -> Dict[str, Any]:
        """Transcripts, isoforms and their position maps (``mappings._hgvs``)."""
        from sabueso.mappings._hgvs import transcript_context

        return transcript_context(self.entry)


@dataclass
class Request:
    identifier: str
    record: Dict[str, Any] = field(default_factory=dict)
    args: Dict[str, Any] = field(default_factory=dict)


class Enricher:
    option: str
    source: str
    registry_id: str
    entity_type: str = "protein"
    areas: Tuple[str, ...] = ()
    #: Taxa the source covers; None for every organism.
    organisms: Tuple[int, ...] | None = None
    coverage_detail: str | None = None
    #: "flag" (``option=True``) or "options" (``option={}`` or ``{"limit": …}``).
    option_kind: str = "flag"

    def requested(self, options: Any) -> bool:
        return bool(options) if self.option_kind == "flag" else options is not None

    def client(self) -> Any:
        raise NotImplementedError

    def record(self, context: Context, options: Any) -> Dict[str, Any]:
        """Fields every record of this source starts with."""
        return {"source": self.source, "identifier": context.anchor}

    def requests(self, context: Context, options: Any) -> List[Request]:
        return [Request(context.anchor, self.record(context, options))]

    def fetch(self, client: Any, request: Request, options: Any) -> Any:
        raise NotImplementedError

    def map(
        self, context: Context, request: Request, response: Any, options: Any
    ) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
        raise NotImplementedError


def _complete(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "fields": {},
        "field_source_assertions": {},
        "source_assertions": [],
        "relationships": [],
        **mapping,
    }


def run(
    enricher: Enricher,
    context: Context,
    options: Any,
    client: Any,
    mappings: List[Dict[str, Any]],
    enrichments: List[Dict[str, Any]],
) -> None:
    """Run one enricher and append its mappings and records; see the module docstring."""
    if enricher.organisms is not None and context.taxon not in enricher.organisms:
        enrichments.append(
            {
                **enricher.record(context, options),
                "status": "not_applicable",
                "detail": enricher.coverage_detail
                or f"{enricher.source} does not cover this organism",
            }
        )
        return
    try:
        requests = enricher.requests(context, options)
    except NothingToAsk as exc:
        enrichments.append(
            {
                **enricher.record(context, options),
                "status": "not_found",
                "detail": str(exc),
            }
        )
        return
    client = client or enricher.client()
    for request in requests:
        try:
            response = enricher.fetch(client, request, options)
        except RecordNotFoundError as exc:
            enrichments.append(
                {**request.record, "status": "not_found", "detail": str(exc)}
            )
            continue
        except ConnectorError as exc:
            enrichments.append(
                {**request.record, "status": "error", "detail": str(exc)}
            )
            continue
        mapping, outcome = enricher.map(context, request, response, options)
        if mapping is not None:
            mappings.append(_complete(mapping))
        enrichments.append({**request.record, **outcome})


def _registered() -> List[Enricher]:
    from . import (
        clinvar,
        diseases,
        gnomad,
        open_targets,
        orphadata,
        phi_base,
        reactome,
    )

    return [
        phi_base.ENRICHER,
        diseases.ENRICHER,
        open_targets.ENRICHER,
        orphadata.ENRICHER,
        reactome.ENRICHER,
        gnomad.ENRICHER,
        clinvar.ENRICHER,
    ]


#: Every declared enricher, in the order they run.
ENRICHERS: List[Enricher] = _registered()


def knowledge_areas(
    entity_type: str = "protein",
) -> List[Tuple[str, str, Dict[str, str]]]:
    """``(area, source, match)`` rows for the knowledge state, from the declarations."""
    return [
        (area, e.source, {"source": e.source})
        for e in ENRICHERS
        if e.entity_type == entity_type
        for area in e.areas
    ]


def options_by_source() -> Dict[Tuple[str, None], set]:
    """Which resolve option produced an enrichment record, by its source."""
    return {(e.source, None): {e.option} for e in ENRICHERS}
