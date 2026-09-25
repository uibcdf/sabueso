"""The distinct names of a deck's cards, as ``numpy.unique`` gives distinct values (rule
``unique_names@1``).

A name is any value of ``names.canonical_name``, ``names.synonyms``,
``names.abbreviations`` or ``names.gene_names``, whatever source states it (UniProt, or
a curator). Two spellings are one name when they agree ignoring case, spaces, hyphens
and underscores ("Triose-phosphate isomerase" and "Triosephosphate isomerase"). A name
is shown in its most common spelling: the one most cards use, then one used as a
canonical name, then the first in alphabetical order.

Most names are shared on purpose: "TIM" abbreviates the name of an enzyme, and every
organism's triosephosphate isomerase carries it. A shared name is a fact to read, never
a reason to join cards: only accessions and gene loci identify an entry.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

NAMES_RULE = "unique_names@1"
NAME_FIELDS = (
    "names.canonical_name",
    "names.synonyms",
    "names.abbreviations",
    "names.gene_names",
)
_IGNORED = re.compile(r"[\s\-_]+")


def name_key(name: str) -> str:
    """The key under which two spellings of one name agree."""
    return _IGNORED.sub("", name.casefold())


def card_names(card: Any) -> List[Tuple[str, str]]:
    """``(field path, name)`` for every name the card carries."""
    out = []
    for field_path in NAME_FIELDS:
        node = card.get(field_path) or {}
        values = node.get("value")
        for value in values if isinstance(values, list) else [values]:
            name = value.get("name") if isinstance(value, dict) else value
            if isinstance(name, str) and name.strip():
                out.append((field_path, name.strip()))
    return out


def unique_names(
    cards: Iterable[Any], return_cards: bool = False
) -> List[str] | Tuple[List[str], List[List[str]]]:
    """The distinct names of ``cards``, sorted; see the module docstring.

    With ``return_cards=True``, also the ids of the distinct cards that carry each name,
    in the same order: ``names, cards = unique_names(deck, return_cards=True)``.
    """
    spellings: Dict[str, Dict[str, set]] = {}
    canonical: set = set()
    carriers: Dict[str, List[str]] = {}
    for card in cards:
        for field_path, name in card_names(card):
            key = name_key(name)
            spellings.setdefault(key, {}).setdefault(name, set()).add(card.id)
            if field_path == "names.canonical_name":
                canonical.add(name)
            if card.id not in carriers.setdefault(key, []):
                carriers[key].append(card.id)
    shown = {
        key: min(
            forms,
            key=lambda n: (-len(forms[n]), n not in canonical, n),
        )
        for key, forms in spellings.items()
    }
    order = sorted(shown, key=lambda k: (shown[k].casefold(), shown[k]))
    names = [shown[k] for k in order]
    if not return_cards:
        return names
    return names, [sorted(carriers[k]) for k in order]
