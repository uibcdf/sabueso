"""Card snapshots: content-addressed identity and pinned references (uibcdf/sabueso#7).

A card keeps its entity-level identity, ``meta.card_id``, across rebuilds. A *snapshot*
is one exact state of that card: its selected values, conflicts, SourceAssertions,
relationships, curation outcomes, selection rules and quality, as ``Card.to_dict()``
stores them. Its id is the SHA-256 of that stored form in canonical JSON:

- the ``quantities`` seal is left out: it is derived from the card and verified on
  every read, and its format belongs to PyUnitWizard;
- SourceAssertions and relationships are hashed in a canonical order, so the order in
  which a build added them does not change the id; stores keep the order they had.

The same content always gets the same id, whoever computes it and wherever the card is
stored, so a JSON copy of a card can be checked against a pin without any store.

References (provisional; the form other MOLI components may rely on is agreed in
uibcdf/moli#3)::

    sabueso:protein:uniprot:P52270                          the card, latest state
    sabueso:protein:uniprot:P52270@sha256:<64 hex>          one exact state (pinned)
    sabueso:protein:uniprot:P52270@sha256:<64 hex>#SA_...   an assertion in that state
    sabueso:protein:uniprot:P52270@sha256:<64 hex>#REL_...  a relationship in that state

An item reference must be pinned: SourceAssertion and relationship ids name what was
stated, not in which state of the card it was read.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Mapping, NamedTuple

from .errors import StorageError

#: The only hash in use; the prefix leaves room for another without ambiguity.
ALGORITHM = "sha256"
SNAPSHOT_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
CARD_ID = re.compile(r"sabueso:[a-z_]+:[^\s@#]+\Z")
ITEM_ID = re.compile(r"(SA|REL)_[^\s@#]+\Z")
#: Stored keys that are not part of the snapshot content.
DERIVED = ("quantities",)
ORDERLESS = ("source_assertion_store", "relationship_store")


def canonical_json(data: Any) -> str:
    """Sorted keys, no whitespace, UTF-8 text; NaN and infinities are refused."""
    try:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except ValueError as exc:
        raise StorageError(f"A card holds a value JSON cannot state ({exc}).") from exc


def digest(text: str) -> str:
    return f"{ALGORITHM}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def snapshot_content(stored: Mapping[str, Any]) -> Dict[str, Any]:
    """What a snapshot id hashes: the stored card without its seal, in canonical order."""
    content = {k: v for k, v in stored.items() if k not in DERIVED}
    for key in ORDERLESS:
        content[key] = sorted(content.get(key) or [], key=canonical_json)
    return content


def snapshot_id(stored: Mapping[str, Any]) -> str:
    """``sha256:<hex>`` of a stored card (``Card.to_dict()`` output)."""
    return digest(canonical_json(snapshot_content(stored)))


class Ref(NamedTuple):
    card_id: str
    snapshot_id: str | None = None
    item_id: str | None = None

    def __str__(self) -> str:
        text = self.card_id
        if self.snapshot_id:
            text += f"@{self.snapshot_id}"
        if self.item_id:
            text += f"#{self.item_id}"
        return text


def pinned_ref(card_id: str, snapshot: str, item_id: str | None = None) -> str:
    return str(Ref(card_id, snapshot, item_id))


def parse_ref(ref: str) -> Ref:
    """Split ``<card_id>[@<snapshot_id>][#<item_id>]``; anything malformed is refused.

    A malformed pin is an error, never a reference to the latest card.
    """
    if not isinstance(ref, str):
        raise StorageError(f"A card reference is text, not {type(ref).__name__}.")
    rest, _, item = ref.strip().partition("#")
    card_id, at, snapshot = rest.partition("@")
    if not CARD_ID.fullmatch(card_id):
        raise StorageError(
            f"{ref!r} does not start with a card id such as "
            "'sabueso:protein:uniprot:P52270'."
        )
    if at and not SNAPSHOT_ID.fullmatch(snapshot):
        raise StorageError(
            f"{ref!r} has a malformed pin; a snapshot id is 'sha256:' and 64 hex digits."
        )
    if item:
        if not ITEM_ID.fullmatch(item):
            raise StorageError(
                f"{ref!r}: after '#' comes a SourceAssertion (SA_...) or relationship "
                "(REL_...) id."
            )
        if not at:
            raise StorageError(
                f"{ref!r} names an item of an unpinned card; pin the card state it was "
                "read in (<card_id>@<snapshot_id>#<item_id>)."
            )
    return Ref(card_id, snapshot or None, item or None)
