"""Which stored cards this Sabueso reads (card schema policy, uibcdf/sabueso#42).

A card states the schema it was written with (``meta.schema_version``, ``x.y.z``):

- before 1.0, ``z`` grows with additive, optional fields and ``y`` with anything else
  (meaning, shape or unit changes, removals, required fields); from 1.0, semver;
- a schema version is fixed once a release publishes it; until then, additive changes
  accumulate in the next version.

Reading, with no silent upgrade:

- the same version, or an older one of the same ``0.y`` (or the same major from 1.0): read;
- a newer one within that range, i.e. written by a newer Sabueso: read, with
  ``NewerCardSchemaWarning``. Keys this version does not know are kept, not dropped. A
  quantity at a path this version did not negotiate is still refused by the seal check
  (the reader cannot declare what it expects there);
- any other version: refused with StorageError, until an explicit migration exists
  (uibcdf/sabueso#51);
- no version at all: refused.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Tuple

from .errors import StorageError

VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def parse(version: Any) -> Tuple[int, int, int] | None:
    if not isinstance(version, str):
        return None
    match = VERSION.fullmatch(version)
    return tuple(int(p) for p in match.groups()) if match else None


def same_line(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> bool:
    """Whether two versions are readable by each other's reader (the same ``0.y``
    before 1.0, the same major from 1.0)."""
    return a[0] == b[0] and (a[0] > 0 or a[1] == b[1])


def check_card_schema(meta: Mapping[str, Any] | None, current: str) -> bool:
    """Raise StorageError for a card this version cannot read; return True when the
    card was written with a newer schema of the same line (the caller warns)."""
    meta = meta or {}
    card_id = meta.get("card_id")
    stated = meta.get("schema_version")
    if stated is None:
        raise StorageError(
            f"Card {card_id} states no schema_version; its fields cannot be interpreted."
        )
    mine, theirs = parse(current), parse(stated)
    if theirs is None:
        raise StorageError(
            f"Card {card_id} states an invalid schema_version {stated!r}."
        )
    if not same_line(theirs, mine):
        raise StorageError(
            f"Card {card_id} was written with card schema {stated}; this Sabueso reads "
            f"{mine[0]}.{mine[1]}.x. Migrate it explicitly with sabueso.migrate_card(data), "
            "which records what it converts and what it cannot (uibcdf/sabueso#51)."
        )
    return theirs > mine
