"""Navigating knowledge: from a card to its related entities, as a deck (#91).

``expand(card, predicate)`` follows a card's relationships of one predicate (or several),
resolves each related entity with ``sabueso.resolve``, and returns a deck of their cards
under the rule ``relationship_expansion@1``:

- each member's basis names the card it came from, and every relationship and
  SourceAssertion that brought it (source, record, version, retrieval). Two refs that
  resolve to the same entity (a ChEMBL id and its InChIKey) become one member, with
  both statements;
- what cannot be followed is excluded, with the reason: ``no_card_type`` (e.g. a
  Reactome pathway or a STRING protein, which Sabueso has no card for),
  ``not_resolved`` (with the resolution's status), or ``limit``;
- each member is a whole card, so 50 are built by default (``limit``), and the cut is
  recorded. The entities with the most statements are followed first.

``Deck.expand(predicate)`` does the same from every card of a deck.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from sabueso._private.argdigest import arg_digest

RULE = "relationship_expansion@1"
DEFAULT_LIMIT = 50
#: Ref namespaces a card can be resolved from, and how.
MOLECULE_NAMESPACES = ("inchikey:", "chembl:", "pubchem:", "pdb.ligand:")


def resolvable(ref: str) -> str | None:
    """The query ``sabueso.resolve`` takes for a related entity's ref, or None."""
    from sabueso.tools.db.mondo import normalize

    if ref.startswith("uniprot:"):
        return ref.split(":", 1)[1]
    if ref.startswith(MOLECULE_NAMESPACES):
        return ref
    if normalize(ref) is not None:
        return ref
    return None


def _statement(card: Any, rel: Dict[str, Any]) -> Dict[str, Any]:
    store = card.source_assertion_store
    assertions = []
    for sa_id in rel.get("source_assertion_ids") or []:
        sa = store.get(sa_id) or {}
        source = sa.get("source") or {}
        assertions.append(
            {
                "id": sa_id,
                "source": source.get("name"),
                "record": source.get("record_id"),
                "version": source.get("version"),
                "retrieved_at": sa.get("retrieved_at"),
            }
        )
    out = {
        "relationship": rel.get("id"),
        "predicate": rel.get("predicate"),
        "object_ref": rel.get("object_ref"),
        "source_assertions": assertions,
    }
    if rel.get("derivation"):
        out["derivation"] = rel["derivation"]
    return out


def _entity_type(ref: str) -> str:
    if ref.startswith("uniprot:"):
        return "protein"
    if ref.startswith(MOLECULE_NAMESPACES):
        return "small_molecule"
    return "disease"


@arg_digest()
def expand(
    card: Any,
    predicate: Any,
    limit: int = DEFAULT_LIMIT,
    options: Dict[str, Dict[str, Any]] | None = None,
    terms: str | None = None,
    skip_digestion: bool = False,
) -> Any:
    """Deck of the cards of the entities ``card`` relates to by ``predicate`` (one
    predicate or several); see the module docstring.

    ``options`` gives resolve options per entity type (``{"protein": {...},
    "small_molecule": {...}, "disease": {...}}``), e.g. fixture clients or
    enrichments; ``terms`` builds every member under a terms profile (#94).
    """
    return _expand([card], predicate, limit, options or {}, terms)


def _expand(
    cards: Iterable[Any],
    predicate: Any,
    limit: int,
    options: Dict[str, Dict[str, Any]],
    terms: str | None,
) -> Any:
    from sabueso._private.smonitor.outcomes import report_outcomes
    from sabueso.core.deck import Deck
    from sabueso.tools.resolve import resolve

    predicates = [predicate] if isinstance(predicate, str) else list(predicate)
    candidates: Dict[str, List[Dict[str, Any]]] = {}
    origins: Dict[str, List[str]] = {}
    excluded: List[Dict[str, Any]] = []
    sources = []
    cards = list(cards)
    for card in cards:
        for name in predicates:
            for rel in card.relationships(name):
                ref = rel.get("object_ref")
                if not ref:
                    continue
                candidates.setdefault(ref, []).append(_statement(card, rel))
                origins.setdefault(ref, [])
                if card.id not in origins[ref]:
                    origins[ref].append(card.id)
    members: Dict[str, Any] = {}
    membership: Dict[str, Dict[str, Any]] = {}
    followed = 0
    # The best-supported entities first: most statements, then by ref.
    for ref in sorted(candidates, key=lambda r: (-len(candidates[r]), r)):
        query = resolvable(ref)
        if query is None:
            excluded.append({"candidate": ref, "reason": "no_card_type", "by": RULE})
            continue
        if followed >= limit:
            excluded.append({"candidate": ref, "reason": "limit", "by": RULE})
            continue
        followed += 1
        kind = _entity_type(ref)
        extra = dict(options.get(kind) or {})
        if terms is not None:
            extra["terms"] = terms
        member, resolution = resolve(query, **extra)
        if member is None:
            excluded.append(
                {
                    "candidate": ref,
                    "reason": f"not_resolved: {resolution.status}",
                    "by": RULE,
                }
            )
            continue
        basis = membership.setdefault(
            member.id,
            {"rule": RULE, "from": [], "refs": [], "statements": []},
        )
        members.setdefault(member.id, member)
        basis["refs"].append(ref)
        basis["statements"] += candidates[ref]
        for origin in origins[ref]:
            if origin not in basis["from"]:
                basis["from"].append(origin)
    reachable = sum(1 for ref in candidates if resolvable(ref) is not None)
    if reachable > limit:
        sources.append(
            {
                "source": "Sabueso",
                "data": "relationship_expansion",
                "status": "added",
                "count": limit,
                "total_count": reachable,
                "truncated": True,
            }
        )
        report_outcomes(sources, subject=", ".join(c.id for c in cards))
    return Deck(
        [members[i] for i in sorted(members)],
        meta={
            "kind": "relationship_expansion",
            "rule": RULE,
            "from": [c.id for c in cards],
            "predicates": predicates,
            "membership": membership,
            "excluded": excluded,
            "sources": sources,
            "limit": limit,
            **({"terms": terms} if terms else {}),
        },
    )
