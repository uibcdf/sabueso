"""ProteinCards built from resolved entities (uibcdf/sabueso#6, step 4c).

``resolve_protein_card`` resolves a query with the EntityResolver and builds the card of
the resolved protein entity:
- only SourceAssertions about the entity (its anchor record and ``same_as`` records) feed
  card fields (``entity_subjects`` guard);
- identity links (``same_as``, ``superseded_by``, ``isoform_of``, derived
  ``possibly_same_as``) are kept as relationships;
- experimental structures are relationships shown through ``Card.structures()``,
  optionally enriched with RCSB polymer-entity data;
- STRING functional associations and ChEMBL bioactivities can be added on request;
  every enrichment outcome is recorded in ``quality.enrichments``;
- the resolution trace (policy, alternatives, decision) is kept in
  ``quality.entity_resolution``.

``ambiguity_deck`` turns unresolved candidates, or non-preferred alternatives, into a Deck
of light candidate cards built only from what the source already reported.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.merge import merge_mapping_results
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.chembl import map_bioactivities
from sabueso.mappings.rcsb_structures import map_structure_entities
from sabueso.mappings.stringdb import map_string_partners
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver.entity_resolver import (
    EntityQuery,
    EntityResolution,
    EntityResolver,
)

UNIPROT_PREFIX = "sabueso:protein:uniprot:"


def resolve_protein_card(
    query: EntityQuery | str,
    resolver: EntityResolver | None = None,
    structures: Iterable[str] | str = (),
    string: Dict[str, Any] | None = None,
    string_client: Any | None = None,
    chembl: Dict[str, Any] | None = None,
    chembl_client: Any | None = None,
) -> Tuple[Card | None, EntityResolution]:
    """Resolve ``query`` and build the ProteinCard of the resolved entity.

    ``structures`` lists PDB ids to enrich with RCSB polymer-entity data, or ``"all"``
    for every PDB cross-reference of the entry. ``string`` (e.g. ``{}`` or
    ``{"required_score": 900, "limit": 20}``) adds STRING functional associations for the
    entry's organism. ``chembl`` (e.g. ``{}`` or ``{"limit": 1000}``) adds the ChEMBL
    bioactivities of the targets the entry cross-references (``Card.bioactivities()``).
    Every enrichment outcome (added, not_found, error) is recorded in
    ``quality.enrichments``. Returns ``(card, resolution)``; ``card`` is None when the
    query did not resolve to a protein entity.
    """
    resolver = resolver or EntityResolver()
    resolution = resolver.resolve(query)
    entity_ref = resolution.entity_ref or ""
    if resolution.status != "resolved" or not entity_ref.startswith(UNIPROT_PREFIX):
        return None, resolution

    anchor = entity_ref[len(UNIPROT_PREFIX) :]
    entry, retrieved_at = resolver.uniprot.fetch_entry(anchor)
    protein_mapping = map_protein(entry, retrieved_at)
    mappings: List[Dict[str, Any]] = [protein_mapping]

    if structures == "all":
        structures = [
            rel["object_ref"].split(":", 1)[1]
            for rel in protein_mapping["relationships"]
            if rel["predicate"] == "has_structure"
        ]
    length = (entry.get("sequence") or {}).get("length")
    enrichments: List[Dict[str, Any]] = []
    for pdb_id in structures:
        record = {"source": "RCSB PDB", "structure": pdb_id}
        try:
            rcsb_entry, rcsb_retrieved_at = resolver.rcsb.fetch_structure(pdb_id)
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
            continue
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
            continue
        mapped = map_structure_entities(
            rcsb_entry,
            rcsb_retrieved_at,
            subjects={anchor},
            reference_lengths={anchor: length} if length else None,
        )
        mappings.append(mapped)
        enrichments.append(
            {**record, "status": "added", "count": len(mapped["relationships"])}
        )

    if string is not None:
        from sabueso.tools.db.stringdb import OnlineStringClient

        client = string_client or OnlineStringClient()
        species = (entry.get("organism") or {}).get("taxonId")
        record = {
            "source": "STRING",
            "identifier": anchor,
            "species": species,
            **string,
        }
        try:
            response = client.partners(anchor, species, **string)
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_string_partners(
                response, anchor, response.get("retrieved_at", "")
            )
            mappings.append(mapped)
            enrichments.append(
                {
                    **record,
                    "required_score": response.get("query", {}).get("required_score"),
                    "limit": response.get("query", {}).get("limit"),
                    "status": "added",
                    "version": response.get("version"),
                    "count": len(mapped["relationships"]),
                }
            )

    if chembl is not None:
        from sabueso.tools.db.chembl import OnlineChEMBLClient

        client = chembl_client or OnlineChEMBLClient()
        targets = [
            x["id"]
            for x in entry.get("uniProtKBCrossReferences", [])
            if x.get("database") == "ChEMBL"
        ]
        if not targets:
            enrichments.append(
                {
                    "source": "ChEMBL",
                    "status": "not_found",
                    "detail": "no ChEMBL cross-reference in the UniProt entry",
                }
            )
        for target in targets:
            record = {"source": "ChEMBL", "target": target, **chembl}
            try:
                response = client.bioactivities(target, **chembl)
            except RecordNotFoundError:
                enrichments.append({**record, "status": "not_found"})
                continue
            except ConnectorError as exc:
                enrichments.append({**record, "status": "error", "detail": str(exc)})
                continue
            mapped = map_bioactivities(
                response, anchor, response.get("retrieved_at", "")
            )
            mappings.append(mapped)
            enrichments.append(
                {
                    **record,
                    "status": "added",
                    "version": response.get("version"),
                    "count": len(mapped["relationships"]),
                    "total_count": response.get("total_count"),
                    "truncated": response.get("truncated"),
                }
            )

    mappings.append(
        {
            "fields": {},
            "source_assertions": list(resolution.source_assertions),
            "field_source_assertions": {},
            "relationships": list(resolution.identity_links),
        }
    )
    subjects = {f"uniprot:{anchor}"} | {
        link["subject_ref"]
        for link in resolution.identity_links
        if link["predicate"] == "same_as" and link["object_ref"] == f"uniprot:{anchor}"
    }
    card = build_card_from_mapping(
        merge_mapping_results(mappings),
        meta={"entity_type": "protein"},
        card_id=entity_ref,
        entity_subjects=subjects,
    )
    if enrichments:
        card.quality["enrichments"] = enrichments
    card.quality["entity_resolution"] = {
        "status": resolution.status,
        "entity_ref": resolution.entity_ref,
        "qualifiers": resolution.qualifiers,
        "policy": resolution.policy,
        "alternatives": resolution.alternatives,
        "decision": resolution.decision,
    }
    return card, resolution


def _candidate_card(
    candidate: Dict[str, Any], resolution: EntityResolution, retrieved_at: str
) -> Card:
    basis = candidate["basis"]
    accession = basis["accession"]
    mapping: Dict[str, Any] = {
        "fields": {},
        "source_assertions": [],
        "field_source_assertions": {},
    }
    for fp, value in (
        ("identifiers.uniprot", accession),
        ("annotations.organism", basis.get("organism_name")),
        ("sequence.length", basis.get("length")),
    ):
        if value is None:
            continue
        assertion = make_source_assertion(fp, value, "UniProt", accession, retrieved_at)
        mapping["fields"][fp] = value
        mapping["source_assertions"].append(assertion)
        mapping["field_source_assertions"][fp] = [assertion["id"]]
    card = build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id=candidate["entity_ref"],
        entity_subjects={f"uniprot:{accession}"},
    )
    card.quality["entity_resolution"] = {
        "status": "candidate",
        "basis": basis,
        "query": resolution.decision.get("query"),
        "rules": resolution.decision.get("rules"),
    }
    return card


def ambiguity_deck(resolution: EntityResolution) -> Deck:
    """Deck of candidate cards: the candidates of an ambiguous resolution, or the
    non-preferred alternatives of a resolved one. Nothing is fetched again."""
    items = resolution.candidates if resolution.status == "ambiguous" else []
    items = items or resolution.alternatives
    retrieved = next(
        (
            s["retrieved_at"]
            for s in resolution.decision.get("sources", [])
            if s.get("retrieved_at")
        ),
        "",
    )
    return Deck(
        [_candidate_card(c, resolution, retrieved) for c in items],
        meta={
            "kind": "entity_ambiguity"
            if resolution.status == "ambiguous"
            else "entity_alternatives",
            "status": resolution.status,
            "entity_ref": resolution.entity_ref,
            "policy": resolution.policy,
            "decision": resolution.decision,
        },
    )
