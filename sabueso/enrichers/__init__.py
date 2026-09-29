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
- ``RecordNotFoundError`` → ``not_found`` (with the release consulted, when the source
  states one), and ``ConnectorError`` → ``error``, per request, so one failing source
  or gene never hides another's knowledge;
- ``MissingKeyError`` → ``not_queried``: a source that needs a personal key it was not
  given is not asked (``tools.db._keys``);
- mappings and records in the declared order, so a card stays deterministic.

The knowledge-state rows and the migration map of enrichment records to options are
derived from ``ENRICHERS`` (``knowledge_areas``, ``options_by_source``), not kept by
hand. See ``devguide/SOURCE_ARCHITECTURE.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, Tuple

from sabueso.core.errors import ConnectorError, MissingKeyError, RecordNotFoundError


class NothingToAsk(Exception):
    """The entry states nothing this source can be asked with; the message says why."""


@dataclass
class Context:
    """What the card already states, computed once for every enricher."""

    anchor: str
    entry: Dict[str, Any]
    #: The mappings built so far (the bespoke enrichments' among them), read-only.
    mappings: List[Dict[str, Any]] = field(default_factory=list)

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

    def author_numbering(self) -> Dict[str, Dict[str, List[list]]]:
        """Per PDB entry, the author numbering RCSB states for this protein's chains
        (``has_structure`` qualifier ``author_numbering``, #73), for the structures the
        card holds."""
        out: Dict[str, Dict[str, List[list]]] = {}
        subject = f"uniprot:{self.anchor}"
        for mapping in self.mappings:
            for rel in mapping.get("relationships") or []:
                if (
                    rel.get("predicate") == "has_structure"
                    and rel.get("subject_ref") == subject
                    and (rel.get("qualifiers") or {}).get("author_numbering")
                ):
                    pdb_id = str(rel["object_ref"]).split(":", 1)[1].upper()
                    out[pdb_id] = rel["qualifiers"]["author_numbering"]
        return out

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
    #: The resolve argument that passes this source's client (default
    #: ``<option>_client``); sources of one service share it (PDBe-KB).
    client_option: str | None = None
    #: Where the enricher runs among the bespoke enrichments, so records keep the
    #: order cards have always had: "after_structures", "after_chembl" or
    #: "after_bioactivity".
    stage: str = "after_bioactivity"
    #: Whether a ``not_found`` record carries the source's message as ``detail``.
    not_found_detail: bool = True

    @property
    def client_argument(self) -> str:
        return self.client_option or f"{self.option}_client"

    @property
    def match(self) -> Dict[str, str]:
        """Fields that identify this enricher's records in ``quality.enrichments``."""
        return {"source": self.source}

    @property
    def default_request(self) -> Any:
        """The option's value that asks for everything by default (packets use it)."""
        return True if self.option_kind == "flag" else {}

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
    try:
        client = client or enricher.client()
    except MissingKeyError as exc:
        enrichments.extend(
            {**r.record, "status": "not_queried", "detail": str(exc)} for r in requests
        )
        return
    for request in requests:
        try:
            response = enricher.fetch(client, request, options)
        except MissingKeyError as exc:
            enrichments.append(
                {**request.record, "status": "not_queried", "detail": str(exc)}
            )
            continue
        except RecordNotFoundError as exc:
            detail = {"detail": str(exc)} if enricher.not_found_detail else {}
            # The release consulted, when the source states one (#89).
            version = getattr(exc, "version", None)
            released = {"version": version} if version is not None else {}
            enrichments.append(
                {**request.record, "status": "not_found", **released, **detail}
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
        alphafold,
        clinvar,
        disease_identity,
        diseases,
        gnomad,
        interpro,
        medgen,
        ncbi_taxonomy,
        open_targets,
        orphadata,
        pdbe_kb,
        phi_base,
        reactome,
        skempi,
        stringdb,
    )

    return [
        stringdb.ENRICHER,
        pdbe_kb.LIGAND_SITES,
        pdbe_kb.INTERFACES,
        alphafold.ENRICHER,
        ncbi_taxonomy.ENRICHER,
        interpro.ENRICHER,
        phi_base.ENRICHER,
        diseases.ENRICHER,
        open_targets.ENRICHER,
        orphadata.ENRICHER,
        reactome.ENRICHER,
        gnomad.ENRICHER,
        clinvar.ENRICHER,
        skempi.ENRICHER,
        # Last: they read the diseases the sources above put on the card (#90), and
        # MONDO reads the MedGen records MedGen states.
        medgen.ENRICHER,
        disease_identity.ENRICHER,
    ]


#: Every declared enricher, in the order they run.
ENRICHERS: List[Enricher] = _registered()


def knowledge_areas(
    entity_type: str = "protein",
) -> List[Tuple[str, str, Dict[str, str]]]:
    """``(area, source, match)`` rows for the knowledge state, from the declarations.
    ``match`` selects the enrichment records that answer the area."""
    return [
        (area, e.source, e.match)
        for e in ENRICHERS
        if e.entity_type == entity_type
        for area in e.areas
    ]


def options_by_source() -> Dict[Tuple[str, str | None], set]:
    """Which resolve option produced an enrichment record, by source and data kind."""
    return {(e.source, e.match.get("data")): {e.option} for e in ENRICHERS}


def run_stage(
    stage: str,
    context: Context,
    requested: Dict[str, Tuple[Any, Any]],
    mappings: List[Dict[str, Any]],
    enrichments: List[Dict[str, Any]],
) -> None:
    """Run the requested enrichers of one stage, in the declared order.
    ``requested`` maps each option to ``(options, client)``."""
    for enricher in ENRICHERS:
        if enricher.stage != stage:
            continue
        options, client = requested.get(enricher.option, (None, None))
        if enricher.requested(options):
            run(enricher, context, options, client, mappings, enrichments)
