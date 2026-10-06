"""Disease cards: one disease across terminologies, anchored at MONDO (#90).

``resolve_disease_card(identifier)`` takes a MONDO id (``mondo:MONDO:0014221``,
``MONDO:0014221``) or an id of a terminology MONDO maps: ``doid:``, ``orphanet:`` (or
``ORPHA:``), ``omim:``, ``mesh:``, ``efo:``, ``ncit:``, ``medgen:``, ``umls:``,
``icd10cm:``…

Identity (rule ``mondo_equivalence@1``):
- an external id resolves only when MONDO states that it is the same disease as one of
  its terms (``MONDO:equivalentTo``). The decision names that statement and the MONDO
  release;
- an id MONDO relates without equivalence, or does not mention, stays unresolved
  (``not_found``, ``no_stated_equivalence``). Nothing is matched by name;
- an obsolete MONDO term is not followed to its replacement: the resolution names the
  replacement MONDO states (``replaced_by``, ``consider``) as candidates, for a person or
  a caller to choose.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from sabueso._private.argdigest import arg_digest
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card, make_card_id
from sabueso.core.disease_deck_support import DiseaseDeckSupport
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.source_acquisition import capture_acquisitions
from sabueso.mappings.disease_decks import native_assertion
from sabueso.mappings.mondo import disease_ref, map_disease
from sabueso.resolver.entity_resolver import EntityResolution
from sabueso.tools.db.mondo import normalize

IDENTITY_RULE = "mondo_equivalence@1"


def disease_card_id(mondo_id: str) -> str:
    return make_card_id("disease", disease_ref(mondo_id))


@arg_digest()
@capture_acquisitions
def resolve_disease_card(
    identifier: str,
    mondo_client: Any | None = None,
    terms: str | None = None,
    skip_digestion: bool = False,
) -> Tuple[Card | None, EntityResolution]:
    """Resolve a disease id and build the card of its MONDO term; see the module
    docstring. ``terms`` builds it only if MONDO's stated terms allow the profile's use
    (#94)."""
    decision: Dict[str, Any] = {"query": identifier, "rules": [], "sources": []}

    def outcome(status: str, rule: str, **extra: Any) -> Tuple[None, EntityResolution]:
        decision["rules"].append(rule)
        decision.update(extra)
        return None, EntityResolution(status=status, decision=decision)

    profile = None
    if terms is not None:
        from sabueso.core.terms import TermsProfile

        profile = TermsProfile(terms)
        if not profile.admits("MONDO"):
            return outcome(
                "unsupported",
                "excluded_by_terms_profile",
                terms_profile=profile.record(),
            )

    curie = normalize(identifier)
    if curie is None:
        return outcome("unsupported", "unsupported_identifier")
    if mondo_client is None:
        from sabueso.tools.db.mondo import OnlineMONDOClient

        mondo_client = OnlineMONDOClient()
    try:
        if curie.startswith("MONDO:"):
            mondo_id = curie
        else:
            answer = mondo_client.equivalent(curie)
            decision["sources"].append(
                {"name": "MONDO", "release": answer.get("version"), "records": [curie]}
            )
            if answer.get("mondo") is None:
                return outcome("not_found", "no_stated_equivalence")
            mondo_id = answer["mondo"]
            decision["rules"].append(IDENTITY_RULE)
            decision["identity"] = {
                "rule": IDENTITY_RULE,
                "stated_by": "MONDO",
                "release": answer.get("version"),
                "equivalent_id": curie,
                "mondo": mondo_id,
            }
        response = mondo_client.term(mondo_id)
    except RecordNotFoundError as exc:
        return outcome("not_found", "record_not_found", detail=str(exc))
    except ConnectorError as exc:
        return outcome("error", "source_error", detail=str(exc))
    term = response["record"]
    if not any(s.get("records") == [mondo_id] for s in decision["sources"]):
        decision["sources"].append(
            {"name": "MONDO", "release": response.get("version"), "records": [mondo_id]}
        )
    if term.get("obsolete"):
        candidates = [
            {
                "entity_ref": disease_card_id(ref),
                "basis": {"stated_by": "MONDO", kind: ref},
            }
            for kind in ("replaced_by", "consider")
            for ref in term.get(kind) or []
        ]
        decision["rules"].append("obsolete_term")
        return None, EntityResolution(
            status="obsolete", candidates=candidates, decision=decision
        )

    mapping = map_disease(
        term, response.get("retrieved_at", ""), response.get("version")
    )
    card = build_card_from_mapping(
        mapping,
        meta={"entity_type": "disease"},
        card_id=disease_card_id(mondo_id),
        entity_subjects={disease_ref(mondo_id)},
    )
    resolution = EntityResolution(
        status="resolved", entity_ref=disease_card_id(mondo_id), decision=decision
    )
    card.quality["entity_resolution"] = {
        "status": resolution.status,
        "entity_ref": resolution.entity_ref,
        "decision": decision,
    }
    if profile is not None:
        card.quality["terms_profile"] = profile.record()
    return card, resolution


# --- From a disease to its targets and its drugs (#90; #82, point 2) --------------------

#: Members built by default. Each member is a whole card (one UniProt or ChEMBL request
#: at least), so a deck asks for fewer than an enrichment does; the cut is recorded in
#: ``deck.meta`` and reported, and ``limit`` asks for more.
DEFAULT_DECK_LIMIT = 50
TARGETS_RULE = "disease_targets@2"
DRUGS_RULE = "disease_drugs@2"


def _disease_card(disease: Any, mondo_client: Any) -> Card:
    """A disease card, given or resolved; ``ResolverError`` when it does not resolve."""
    from sabueso.core.errors import ResolverError

    if isinstance(disease, Card):
        return disease
    card, resolution = resolve_disease_card(disease, mondo_client=mondo_client)
    if card is None:
        raise ResolverError(
            f"{disease} did not resolve to a disease ({resolution.status}: "
            f"{', '.join(resolution.decision.get('rules') or [])})."
        )
    return card


def _ids(card: Card) -> Tuple[str, list]:
    mondo = (card.get("identifiers.mondo") or {}).get("value")
    equivalents = (card.get("identifiers.equivalent_ids") or {}).get("value") or []
    return mondo, list(equivalents)


def _deck(cards, meta, sources, subject):
    from sabueso._private.smonitor.outcomes import report_outcomes
    from sabueso.core.deck import Deck

    report_outcomes(sources, subject=subject)
    return Deck(cards, meta=meta)


@arg_digest()
@capture_acquisitions
def disease_targets(
    disease: Any,
    limit: int = DEFAULT_DECK_LIMIT,
    resolver: Any | None = None,
    open_targets_client: Any | None = None,
    orphadata_client: Any | None = None,
    mondo_client: Any | None = None,
    skip_digestion: bool = False,
) -> Any:
    """Deck of the protein cards of a disease's targets (rule ``disease_targets@2``).

    ``disease`` is a disease card or any id ``resolve_disease_card`` takes. The targets
    are those the sources state, through the disease's MONDO id and the ids MONDO states
    are the same disease:

    - Open Targets' associated targets (by the MONDO id, then its EFO equivalents): each
      gene's Swiss-Prot products, with the overall score as stated;
    - Orphanet's genes of the disorder (by its Orphanet equivalents), with the
      association type and status, through the UniProt accession Orphanet states.

    Each member's ``basis`` lists every source statement that brought it. A gene with
    no Swiss-Prot product is excluded (``no_swissprot_product``), and so is anything past
    ``limit`` (``limit``), in Open Targets' order and then Orphanet's. Every source
    outcome is in ``deck.meta["sources"]``.
    """
    from sabueso.tools.card.protein import resolve_protein_card

    card = _disease_card(disease, mondo_client)
    support = DiseaseDeckSupport(card, TARGETS_RULE, limit)
    mondo, equivalents = _ids(card)
    candidates: Dict[str, list] = {}
    excluded = []
    sources = []

    if open_targets_client is None:
        from sabueso.tools.db.open_targets import OnlineOpenTargetsClient

        open_targets_client = OnlineOpenTargetsClient()
    asked = [mondo] + [e for e in equivalents if e.startswith("EFO:")]
    for disease_id in asked:
        record = {"source": "Open Targets", "identifier": disease_id}
        try:
            response = open_targets_client.targets(disease_id)
        except RecordNotFoundError as exc:
            sources.append({**record, "status": "not_found", "detail": str(exc)})
            continue
        except ConnectorError as exc:
            sources.append({**record, "status": "error", "detail": str(exc)})
            continue
        rows = response["record"]["rows"]
        response_assertion_id = support.add(
            native_assertion(
                "Open Targets",
                f"disease:{disease_id}",
                response["record"],
                response,
                disease_ref(disease_id),
            )
        )
        sources.append(
            {
                **record,
                "status": "added" if rows else "not_found",
                "version": response.get("version"),
                "count": len(rows),
                "total_count": response["record"].get("count"),
                "truncated": (response["record"].get("count") or 0) > len(rows),
            }
        )
        for rank, row in enumerate(rows, 1):
            target = row.get("target") or {}
            assertion_id = support.add(
                native_assertion(
                    "Open Targets",
                    f"{target.get('id')}:{disease_id}",
                    {"disease": response["record"].get("disease"), "row": row},
                    response,
                    f"ensembl:{target.get('id')}",
                )
            )
            swissprot = sorted(
                p["id"]
                for p in target.get("proteinIds") or []
                if p.get("source") == "uniprot_swissprot"
            )
            if not swissprot:
                excluded.append(
                    {
                        "candidate": f"ensembl:{target.get('id')}",
                        "reason": "no_swissprot_product",
                        "by": "Open Targets",
                        "basis": support.basis(
                            f"ensembl:{target.get('id')}",
                            [disease_id],
                            [assertion_id, response_assertion_id],
                        ),
                    }
                )
            for accession in swissprot:
                candidates.setdefault(accession, []).append(
                    {
                        "source": "Open Targets",
                        "disease": disease_id,
                        "gene": f"ensembl:{target.get('id')}",
                        "symbol": target.get("approvedSymbol"),
                        "score": row.get("score"),
                        "rank": rank,
                        "version": response.get("version"),
                        "source_assertion_ids": [assertion_id, response_assertion_id],
                    }
                )
        break  # the first id Open Targets holds answers for the disease

    if orphadata_client is None:
        from sabueso.tools.db.orphadata import OnlineOrphadataClient

        orphadata_client = OnlineOrphadataClient()
    for code in [e for e in equivalents if e.startswith("Orphanet:")]:
        record = {"source": "Orphanet", "identifier": code}
        try:
            response = orphadata_client.genes(code.split(":", 1)[1])
        except RecordNotFoundError as exc:
            sources.append({**record, "status": "not_found", "detail": str(exc)})
            continue
        except ConnectorError as exc:
            sources.append({**record, "status": "error", "detail": str(exc)})
            continue
        sources.append(
            {
                **record,
                "status": "added",
                "version": response.get("version"),
                "count": len(response["record"]),
            }
        )
        for row in response["record"]:
            assertion_id = support.add(
                native_assertion(
                    "Orphanet",
                    f"ORPHA:{row.get('orpha_code')}:{row.get('gene_symbol')}",
                    row,
                    response,
                    f"uniprot:{row['uniprot']}",
                )
            )
            candidates.setdefault(row["uniprot"], []).append(
                {
                    "source": "Orphanet",
                    "disease": code,
                    "gene": row.get("gene_symbol"),
                    "association_type": row.get("association_type"),
                    "association_status": row.get("association_status"),
                    "version": response.get("version"),
                    "source_assertion_ids": [assertion_id],
                }
            )

    ordered = sorted(
        candidates,
        key=lambda a: (
            min(
                (b["rank"] for b in candidates[a] if "rank" in b),
                default=len(candidates) + 1,
            ),
            a,
        ),
    )
    cards, membership = [], {}

    def basis(accession):
        rows = candidates[accession]
        return support.basis(
            f"uniprot:{accession}",
            [r["disease"] for r in rows],
            [i for r in rows for i in r["source_assertion_ids"]],
            target_of=card.id,
            rule=TARGETS_RULE,
            statements=rows,
        )

    for accession in ordered[:limit]:
        try:
            protein, _ = resolve_protein_card(accession, resolver=resolver)
        except ConnectorError as exc:
            excluded.append(
                {
                    "candidate": f"uniprot:{accession}",
                    "reason": f"card_not_built: {exc}",
                    "basis": basis(accession),
                }
            )
            continue
        if protein is None:
            excluded.append(
                {
                    "candidate": f"uniprot:{accession}",
                    "reason": "card_not_built",
                    "basis": basis(accession),
                }
            )
            continue
        cards.append(protein)
        membership[protein.id] = support.bind(basis(accession), protein)
    excluded += [
        {"candidate": f"uniprot:{a}", "reason": "limit", "basis": basis(a)}
        for a in ordered[limit:]
    ]
    for exclusion in excluded:
        support.bind(exclusion["basis"])
    if len(ordered) > limit:
        sources.append(
            {
                "source": "Sabueso",
                "data": "disease_targets",
                "status": "added",
                "count": limit,
                "total_count": len(ordered),
                "truncated": True,
            }
        )
    return _deck(
        cards,
        {
            "kind": "disease_targets",
            "disease": card.id,
            "rule": TARGETS_RULE,
            "membership": membership,
            "excluded": excluded,
            "sources": sources,
            "limit": limit,
            "support": support.to_dict(),
        },
        sources,
        card.id,
    )


@arg_digest()
@capture_acquisitions
def disease_drugs(
    disease: Any,
    limit: int = DEFAULT_DECK_LIMIT,
    chembl_client: Any | None = None,
    ccd_client: Any | None = None,
    unichem_client: Any | None = None,
    mondo_client: Any | None = None,
    skip_digestion: bool = False,
) -> Any:
    """Deck of the small-molecule cards whose ChEMBL drug indications name a disease
    (rule ``disease_drugs@2``).

    ChEMBL names an indication's disease by an EFO or MONDO id (``efo_id``) and a MeSH
    heading. The disease is asked by its MONDO id and by the EFO and MeSH ids MONDO
    states are the same disease; never by name. Each member's ``basis`` lists the
    indications that brought it, with ChEMBL's ``max_phase_for_ind``. Molecules are
    ordered by that phase, highest first; past ``limit`` they are excluded (``limit``).
    """
    from sabueso.tools.card.small_molecule import resolve_molecule_card

    card = _disease_card(disease, mondo_client)
    support = DiseaseDeckSupport(card, DRUGS_RULE, limit)
    mondo, equivalents = _ids(card)
    asked = [mondo] + [e for e in equivalents if e.startswith(("EFO:", "MESH:"))]
    if chembl_client is None:
        from sabueso.tools.db.chembl import OnlineChEMBLClient

        chembl_client = OnlineChEMBLClient()
    record = {"source": "ChEMBL", "data": "drug_indication", "identifier": asked}
    excluded, cards, membership = [], [], {}
    try:
        response = chembl_client.indications_for(asked)
    except ConnectorError as exc:
        sources = [{**record, "status": "error", "detail": str(exc)}]
        return _deck(
            [],
            {"kind": "disease_drugs", "disease": card.id, "rule": DRUGS_RULE,
             "sources": sources, "membership": {}, "excluded": [],
             "limit": limit, "support": support.to_dict()},
            sources,
            card.id,
        )  # fmt: skip
    found = response["indications"]
    assertion_ids = {
        molecule: [
            support.add(
                native_assertion(
                    "ChEMBL",
                    str(row.get("drugind_id") or f"{molecule}:{index}"),
                    row,
                    response,
                    f"chembl:{molecule}",
                    indication=True,
                )
            )
            for index, row in enumerate(rows)
        ]
        for molecule, rows in found.items()
    }
    sources = [
        {
            **record,
            "status": "added" if found else "not_found",
            "version": response.get("version"),
            "count": len(found),
        }
    ]

    def phase(molecule: str) -> float:
        return max(float(i.get("max_phase_for_ind") or 0) for i in found[molecule])

    ordered = sorted(found, key=lambda m: (-phase(m), m))

    def basis(molecule):
        return support.basis(
            f"chembl:{molecule}",
            asked,
            assertion_ids[molecule],
            investigated_for=card.id,
            rule=DRUGS_RULE,
            indications=found[molecule],
        )

    for molecule in ordered[:limit]:
        drug, resolution = resolve_molecule_card(
            f"chembl:{molecule}",
            chembl_client=chembl_client,
            ccd_client=ccd_client,
            unichem_client=unichem_client,
        )
        if drug is None:
            excluded.append(
                {
                    "candidate": f"chembl:{molecule}",
                    "reason": f"card_not_built: {resolution.status}",
                    "basis": basis(molecule),
                }
            )
            continue
        cards.append(drug)
        membership[drug.id] = support.bind(basis(molecule), drug)
    excluded += [
        {"candidate": f"chembl:{m}", "reason": "limit", "basis": basis(m)}
        for m in ordered[limit:]
    ]
    for exclusion in excluded:
        support.bind(exclusion["basis"])
    if len(ordered) > limit:
        sources.append(
            {
                "source": "Sabueso",
                "data": "disease_drugs",
                "status": "added",
                "count": limit,
                "total_count": len(ordered),
                "truncated": True,
            }
        )
    return _deck(
        cards,
        {
            "kind": "disease_drugs",
            "disease": card.id,
            "rule": DRUGS_RULE,
            "membership": membership,
            "excluded": excluded,
            "sources": sources,
            "limit": limit,
            "support": support.to_dict(),
        },
        sources,
        card.id,
    )
