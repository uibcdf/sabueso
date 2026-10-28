"""Frozen declaration admission; coordinate/reference validation is a separate rule.

An exact subject match scopes a retained declaration to its Card. It does not
merge entities, certify source authenticity or establish a sequence mapping.
Keep this policy stable for independently read original saved results (#169).
"""

import re
from copy import deepcopy

RULE = "experimental_structure_admission@1"
INVENTORY_RULE = "structure_inventory@2"
_CARD = re.compile(r"sabueso:protein:(uniprot:[A-Za-z0-9]+)\Z")


def declaration_scope(card):
    """Read an explicit Card anchor, without deriving identity from its contents."""
    match = _CARD.fullmatch(card.id) if isinstance(card.id, str) else None
    subject = match[1] if match else None
    node = card.get("identifiers.uniprot")
    value = node.get("value") if isinstance(node, dict) else node
    conflicts = card.quality.get("conflicts", [])
    reason = None
    if card.meta.get("entity_type") != "protein":
        reason = "not_protein"
    elif subject is None:
        reason = "canonical_card_subject_unavailable"
    elif not isinstance(conflicts, list):
        reason = "canonical_card_identity_context_unavailable"
    elif any(
        isinstance(row, dict)
        and str(row.get("field")).removesuffix(".value") == "identifiers.uniprot"
        for row in conflicts
    ):
        reason = "canonical_card_subject_conflicting"
    elif not isinstance(node, dict) or not isinstance(value, str) or not value:
        reason = "canonical_card_identifier_unavailable"
    elif value != subject.removeprefix("uniprot:"):
        reason = "canonical_card_subject_mismatch"
    return {
        "subject_ref": subject,
        "basis": "exact_declared_card_subject",
        "scope": "relationship_declaration_only",
        "identifier_state": "not_retained" if node is None else "retained",
        "identifier_value": deepcopy(value),
        "reason": reason,
    }


def decision(card, relationship):
    """A missing/foreign/ambiguous subject remains unplaced, never a negative fact."""
    scope = declaration_scope(card)
    subject = relationship.get("subject_ref")
    reason = scope["reason"]
    if reason is None:
        reason = (
            "relationship_subject_unavailable"
            if not isinstance(subject, str) or not subject
            else "relationship_subject_mismatch"
            if subject != scope["subject_ref"]
            else None
        )
    return {
        "rule": RULE,
        "status": "unplaced" if reason else "admitted",
        "reason": reason,
        "subject_ref": deepcopy(subject),
        "card_subject": scope,
    }


def _unplaced(card, relationship, admission):
    pin = card.pinned_ref() if card.id else None

    def location(store, key):
        if pin is None:
            return None
        return {
            "format": "card_access_location@1",
            "kind": "card",
            "card_ref": pin,
            "snapshot_id": pin.rsplit("@", 1)[1],
            "segments": [
                {"type": "Key", "value": store},
                {"type": "Record", "value": key},
            ],
        }

    return {
        "relationship_id": relationship["id"],
        "structure_ref": relationship.get("object_ref"),
        "reason": admission["reason"],
        "admission": admission,
        "relationship": deepcopy(relationship),
        "relationship_location": location("relationship_store", relationship["id"]),
        "source_assertions": [
            {
                "id": key,
                "state": "present"
                if card.source_assertion_store.get(key) is not None
                else "not_retained",
                "location": location("source_assertion_store", key)
                if card.source_assertion_store.get(key) is not None
                else None,
            }
            for key in relationship.get("source_assertion_ids") or []
        ],
    }


class _AdmittedCard:
    """Read-only relationship filter; original fields, stores and pin stay intact."""

    def __init__(self, card):
        self._card = card
        self.admissions = {}
        self.unplaced = []
        for row in card.relationships("has_structure"):
            admitted = decision(card, row)
            self.admissions[row["id"]] = admitted
            if admitted["status"] == "unplaced":
                self.unplaced.append(_unplaced(card, row, admitted))

    def __getattr__(self, key):
        return getattr(self._card, key)

    def relationships(self, predicate=None, object_ref=None):
        return [
            row
            for row in self._card.relationships(predicate, object_ref=object_ref)
            if row["predicate"] != "has_structure"
            or self.admissions[row["id"]]["status"] == "admitted"
        ]


def derivation(rule):
    return rule(
        RULE,
        inputs=[
            "meta.card_id",
            "meta.entity_type",
            "identifiers.uniprot",
            "quality.conflicts",
            "has_structure.subject_ref",
        ],
        parameters={"scope": "relationship_declaration_only"},
    )


def view(card, *, include_fragments=False, region=None, summary, rule):
    """Apply admission before interpreting any qualifiers, including malformed ones."""
    admitted = _AdmittedCard(card)
    result = summary(admitted, include_fragments=include_fragments, region=region)
    for row in result["items"]:
        row["admission"] = deepcopy(admitted.admissions[row["relationship_id"]])
    return {
        **result,
        "admission_rule": derivation(rule),
        "unplaced": deepcopy(admitted.unplaced),
    }


def inventory(cards, *, summarize, rule, **options):
    """Preserve original classification/grouping over the admitted declarations."""
    from .errors import ArgumentError

    if len({card.id for card in cards}) != len(cards):
        raise ArgumentError("A structure inventory requires distinct protein card ids.")
    admitted = [_AdmittedCard(card) for card in cards]
    result = summarize(admitted, **options)
    decisions = {card.id: card.admissions for card in admitted}
    for row in result["items"]:
        row["admission"] = deepcopy(decisions[row["card_id"]][row["relationship_id"]])
    original = result["rule"]
    result["rule"] = rule(
        INVENTORY_RULE,
        inputs=original["inputs"],
        parameters={**original["parameters"], "admission_rule": RULE},
    )
    result["admission_rule"] = derivation(rule)
    result["unplaced"] = {
        card.id: deepcopy(card.unplaced) for card in admitted if card.unplaced
    }
    return result
