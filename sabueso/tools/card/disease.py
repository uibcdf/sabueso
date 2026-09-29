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
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.mappings.mondo import disease_ref, map_disease
from sabueso.resolver.entity_resolver import EntityResolution
from sabueso.tools.db.mondo import normalize

IDENTITY_RULE = "mondo_equivalence@1"


def disease_card_id(mondo_id: str) -> str:
    return make_card_id("disease", disease_ref(mondo_id))


@arg_digest()
def resolve_disease_card(
    identifier: str,
    mondo_client: Any | None = None,
    skip_digestion: bool = False,
) -> Tuple[Card | None, EntityResolution]:
    """Resolve a disease id and build the card of its MONDO term; see the module
    docstring."""
    decision: Dict[str, Any] = {"query": identifier, "rules": [], "sources": []}

    def outcome(status: str, rule: str, **extra: Any) -> Tuple[None, EntityResolution]:
        decision["rules"].append(rule)
        decision.update(extra)
        return None, EntityResolution(status=status, decision=decision)

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
    return card, resolution
