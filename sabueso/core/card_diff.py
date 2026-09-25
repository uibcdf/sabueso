"""Compare the knowledge of two cards (uibcdf/sabueso#59, rule ``card_knowledge_diff@1``).

For paralogs, orthologs, or a target and its counterpart in another species, the
comparison says, area by area, what both cards state, what only one states, and what
they state differently:

- **fields**: equal or different values. List fields whose items have an identity
  (``curation.ITEM_IDENTITY``) are compared item by item. Free-text items cannot be
  compared without reading them, and are reported as ``not_compared``;
- **positional features** are compared only through a residue mapping (``residue_map``,
  ``{position in this card: position in the other}``, e.g. from a MolSysMT alignment).
  Without one they are ``not_compared``: the same number in two entries is not the same
  residue. An item with an unmapped position is ``not_comparable``;
- **relationships**: per predicate, the objects both cards point at and those only one
  does (GO terms, classifications and orthology groups, structures, measured molecules);
- **knowledge states** (#56) that differ, so "only this card states it" is told apart
  from "the other card did not query it".

The comparison is a derived view with its rule named, never a SourceAssertion.
Sequence and structure alignment belong to MolSysMT; a mapping passed in is recorded as
the basis of every position-level result.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List

DIFF_RULE = "card_knowledge_diff@1"


def _fields(card: Any) -> Dict[str, Any]:
    out = {}
    for path in card.list_fields():
        node = card.get(path)
        if isinstance(node, dict) and "source_assertion_ids" in node:
            out[path] = node.get("value")
    return out


def _remap(item: Dict[str, Any], residue_map: Dict[int, int]) -> Dict[str, Any] | None:
    """The item with its positions in the other card's numbering, or None."""
    from .curation import _positions

    positions = _positions(item)
    if not positions or any(p not in residue_map for p in positions):
        return None
    mapped = copy.deepcopy(item)
    sequence = mapped.setdefault("location", {}).setdefault("sequence", {})
    sequence.pop("start", None)
    sequence.pop("end", None)
    sequence["fragments"] = [
        {"start": residue_map[p], "end": residue_map[p]} for p in positions
    ]
    return mapped


def _compare_items(
    path: str, mine: List[Any], theirs: List[Any], residue_map: Dict[int, int] | None
) -> Dict[str, Any]:
    from .curation import ITEM_IDENTITY, _key

    if path not in ITEM_IDENTITY:
        # A list of plain values (a lineage, gene loci): compared as values.
        identity = _key
    elif ITEM_IDENTITY[path] is None:
        return {"status": "not_compared", "reason": "free text"}
    else:
        identity = ITEM_IDENTITY[path]
    positional = path.startswith("features_positional.")
    if positional and residue_map is None:
        return {"status": "not_compared", "reason": "no residue mapping"}
    theirs_by_key: Dict[Any, List[Any]] = {}
    for item in theirs:
        theirs_by_key.setdefault(identity(item), []).append(item)
    both, differ, only_self, not_comparable = [], [], [], []
    matched = set()
    for item in mine:
        probe = _remap(item, residue_map) if positional else item
        if probe is None:
            not_comparable.append(item)
            continue
        key = identity(probe)
        if key in theirs_by_key:
            matched.add(key)
            other = theirs_by_key[key][0]
            if positional:
                probe_key = _key({**probe, "location": other.get("location")})
            else:
                probe_key = _key(probe)
            (both if probe_key == _key(other) else differ).append(
                {"self": item, "other": other}
            )
        else:
            only_self.append(item)
    only_other = [
        i for k, items in theirs_by_key.items() if k not in matched for i in items
    ]
    status = (
        "same"
        if not (differ or only_self or only_other or not_comparable)
        else "differs"
    )
    result: Dict[str, Any] = {
        "status": status,
        "both": both,
        "differ": differ,
        "only_self": only_self,
        "only_other": only_other,
    }
    if not_comparable:
        result["not_comparable"] = not_comparable
    return result


def compare_knowledge(
    card: Any, other: Any, residue_map: Dict[int, int] | None = None
) -> Dict[str, Any]:
    """See the module docstring."""
    from .relationship_store import make_derivation

    mine, theirs = _fields(card), _fields(other)
    fields: Dict[str, Any] = {}
    for path in sorted(set(mine) | set(theirs)):
        if path not in theirs:
            fields[path] = {"status": "only_self"}
        elif path not in mine:
            fields[path] = {"status": "only_other"}
        elif isinstance(mine[path], list) and isinstance(theirs[path], list):
            fields[path] = _compare_items(path, mine[path], theirs[path], residue_map)
        elif path == "sequence.primary":
            fields[path] = {
                "status": "same" if mine[path] == theirs[path] else "differs",
                "lengths": [len(mine[path] or ""), len(theirs[path] or "")],
            }
        else:
            fields[path] = (
                {"status": "same"}
                if mine[path] == theirs[path]
                else {"status": "differs", "self": mine[path], "other": theirs[path]}
            )

    def objects(c: Any) -> Dict[str, set]:
        out: Dict[str, set] = {}
        for rel in c.relationship_store.to_list():
            out.setdefault(rel["predicate"], set()).add(rel["object_ref"])
        return out

    a, b = objects(card), objects(other)
    relationships = {
        predicate: {
            "both": sorted(a.get(predicate, set()) & b.get(predicate, set())),
            "only_self": sorted(a.get(predicate, set()) - b.get(predicate, set())),
            "only_other": sorted(b.get(predicate, set()) - a.get(predicate, set())),
        }
        for predicate in sorted(set(a) | set(b))
    }

    def states(c: Any) -> Dict[tuple, str]:
        return {
            (r["area"], r["source"]): r["state"] for r in c.knowledge_state()["rows"]
        }

    sa, sb = states(card), states(other)
    knowledge_states = [
        {
            "area": area,
            "source": source,
            "self": sa.get((area, source)),
            "other": sb.get((area, source)),
        }
        for area, source in sorted(set(sa) | set(sb))
        if sa.get((area, source)) != sb.get((area, source))
    ]
    return {
        "self": card.id,
        "other": other.id,
        "fields": fields,
        "relationships": relationships,
        "knowledge_states": knowledge_states,
        "rule": make_derivation(
            DIFF_RULE,
            inputs=[card.id, other.id],
            parameters={
                "residue_map": None
                if residue_map is None
                else {"positions": len(residue_map), "supplied_by": "caller"},
                "positional_without_map": "not_compared",
                "free_text": "not_compared",
            },
        ),
    }
