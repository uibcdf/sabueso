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


@signal(tags=["api"])
@arg_digest()
def resolve(
    query: EntityQuery | str,
    entity_type: str | None = None,
    skip_digestion: bool = False,
    **options: Any,
) -> Tuple[Card | None, EntityResolution]:
    """Resolve ``query`` and build the card of its entity: ``(card, resolution)``.

    ``card`` is None when the query does not resolve to one entity; the resolution says
    why (``status`` and ``decision``). See the module docstring for the routing.
    """
    kind, basis = _route(query, entity_type)
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

        card, resolution = resolve_protein_card(query, **options)
        tool = "resolve_protein_card"
    resolution.decision["route"] = {"entity_type": kind, "tool": tool, "basis": basis}
    return card, resolution
