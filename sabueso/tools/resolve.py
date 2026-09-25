"""One entry point for resolution: ``sabueso.resolve(query, **options)`` (uibcdf/sabueso#38).

The query's namespace decides which card tool answers it, and the choice is recorded in
the resolution (``resolution.decision["route"]``):

- small-molecule namespaces (``chembl:``, ``pdb.ligand:``, ``inchikey:``), bare ChEMBL ids
  and standard InChIKeys go to ``resolve_molecule_card``;
- anything else, including UniProt accessions, ``pdb:`` ids and an ``EntityQuery`` (name
  and organism), goes to ``resolve_protein_card``, whose resolver keeps its own rules
  (ambiguity is reported, never silently chosen).

``entity_type`` overrides the namespace. Options are passed to the chosen tool; one it
does not take is refused there, never ignored.
"""

from __future__ import annotations

from typing import Any, Tuple

from smonitor import signal

from sabueso._private.argdigest import arg_digest
from sabueso.core.card import Card
from sabueso.resolver.entity_resolver import EntityQuery, EntityResolution

PROTEIN, SMALL_MOLECULE = "protein", "small_molecule"


def _route(query: EntityQuery | str, entity_type: str | None) -> Tuple[str, str]:
    """``(entity type, basis)`` for a query."""
    from sabueso.tools.card.small_molecule import _parse

    if entity_type is not None:
        return entity_type, "entity_type"
    if isinstance(query, EntityQuery):
        if query.entity_type in (PROTEIN, SMALL_MOLECULE):
            return query.entity_type, "query.entity_type"
        if query.identifier is None:
            return PROTEIN, "name_and_organism"
        query = query.identifier
    namespace, _ = _parse(query)
    if namespace is not None:
        return SMALL_MOLECULE, f"namespace:{namespace}"
    return PROTEIN, "default"


def _curated_anchor(query: EntityQuery, curations: Any) -> Tuple[str, Any, Any] | None:
    """A name a curator anchored to an entry (#55).

    Returns None when no curated name matches, ``("ambiguous", resolution, None)`` when
    the name designates several entries, and ``("resolved", query, record)`` otherwise.
    """
    named = curations.entities_named(query.name)
    if not named:
        return None
    summary = {
        ref: [
            {
                "source_assertion_id": r["source_assertion_id"],
                "publication": r.get("publication"),
                "curator": r.get("curator"),
            }
            for r in records
        ]
        for ref, records in sorted(named.items())
    }
    if len(named) > 1:
        return (
            "ambiguous",
            EntityResolution(
                "ambiguous",
                candidates=[
                    {"entity_ref": ref, "basis": {"curated_name": query.name}}
                    for ref in sorted(named)
                ],
                decision={
                    "query": str(query),
                    "rules": ["curated_name_ambiguous"],
                    "curated_name": {"name": query.name, "designates": summary},
                },
            ),
            None,
        )
    ((ref, _),) = named.items()
    accession = ref.split(":", 1)[1]
    return (
        "resolved",
        EntityQuery(identifier=accession),
        {"name": query.name, "designates": summary},
    )


def _organism_fits(card: Card, organism: Any) -> bool:
    if organism is None:
        return True

    def value(path: str) -> Any:
        node = card.get(path)
        return node.get("value") if isinstance(node, dict) else None

    if isinstance(organism, int) or str(organism).isdigit():
        return value("annotations.taxon_id") == int(organism) or False
    name = str(organism).casefold()
    return (value("annotations.organism") or "").casefold() == name or name in {
        t.casefold() for t in value("annotations.lineage") or []
    }


@signal(tags=["api"])
@arg_digest()
def resolve(
    query: EntityQuery | str,
    entity_type: str | None = None,
    profile: str | None = None,
    curations: Any = None,
    skip_digestion: bool = False,
    **options: Any,
) -> Tuple[Card | None, EntityResolution]:
    """Resolve ``query`` and build the card of its entity: ``(card, resolution)``.

    ``card`` is None when the query does not resolve to one entity; the resolution says
    why (``status`` and ``decision``). See the module docstring for the routing.

    ``profile`` names a versioned set of options, e.g. ``"structural_baseline@1"``
    (``sabueso/resolver/enrichment_profiles.json``). Options passed explicitly override
    it, and ``resolution.decision["profile"]`` records the name, the options it gave and
    those overridden.

    ``curations`` (a ``CurationStore`` or the path of one) applies the curated literature
    assertions recorded for the entity, with their outcomes recomputed against the
    fresh sources (``card.quality["curation_store"]``).
    """
    kind, basis = _route(query, entity_type)
    applied = None
    if profile is not None:
        from sabueso.resolver.loader import load_enrichment_profiles

        given = dict(load_enrichment_profiles()[profile].get(kind) or {})
        applied = {
            "name": profile,
            "options": given,
            "overridden": sorted(set(given) & set(options)),
        }
        options = {**given, **options}
    if kind == SMALL_MOLECULE:
        from sabueso.tools.card.small_molecule import resolve_molecule_card

        identifier = query.identifier if isinstance(query, EntityQuery) else query
        if identifier is None:
            card, resolution = (
                None,
                EntityResolution(
                    status="unsupported",
                    decision={
                        "query": str(query),
                        "rules": ["small_molecule_needs_an_identifier"],
                    },
                ),
            )
        else:
            card, resolution = resolve_molecule_card(identifier, **options)
        tool = "resolve_molecule_card"
    else:
        from sabueso.tools.card.protein import resolve_protein_card

        anchored = (
            _curated_anchor(query, curations)
            if basis == "name_and_organism" and curations is not None
            else None
        )
        if anchored is not None and anchored[0] == "ambiguous":
            card, resolution = None, anchored[1]
        else:
            target = anchored[1] if anchored else query
            card, resolution = resolve_protein_card(target, **options)
            if anchored:
                resolution.decision["curated_name"] = anchored[2]
                resolution.decision.setdefault("rules", []).insert(0, "curated_name")
                if card is not None and not _organism_fits(card, query.organism):
                    # The curated name designates an entry of another organism: it
                    # does not answer this query, and the search decides.
                    card, resolution = resolve_protein_card(query, **options)
                    resolution.decision["rules"].insert(
                        0, "curated_name_other_organism"
                    )
        tool = "resolve_protein_card"
    resolution.decision["route"] = {"entity_type": kind, "tool": tool, "basis": basis}
    if applied is not None:
        resolution.decision["profile"] = applied
    if card is not None:
        # The card says how it was built, also once stored and read back.
        card.quality.setdefault("entity_resolution", {})["decision"] = (
            resolution.decision
        )
    if curations is not None and card is not None:
        curations.apply(card)
    return card, resolution
