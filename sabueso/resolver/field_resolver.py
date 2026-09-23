"""Field-level resolver: selects a canonical value from competing SourceAssertions.

Two field rules decide which assertions are comparable at all (uibcdf/sabueso#10):

- ``compare_within``: a list of paths into the assertion (e.g. ``"source.name"``,
  ``"source_metadata.method"``). Assertions are compared only with those that share the
  same values at those paths. Values computed by different methods (ALogP and XLogP3), or
  representations that only one toolkit can canonicalise (SMILES), are different
  quantities, not a disagreement. They are returned as ``alternatives``, never as a
  ``conflict``.
- ``numeric_agreement: "stated_precision"``: two numbers agree when they are equal at the
  coarser of the precisions their sources state (``824.97`` and ``825.0`` agree at one
  decimal; ``171.17`` and ``171`` at zero). The precision is read from the asserted value
  as the source wrote it, never guessed.

A real disagreement, within one method and beyond the stated precision, is still a
``conflict``. Only the assertions that state the selected value support it.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from sabueso.core.source_assertion_store import assertion_value

# Retrieval times mix timezone-aware stamps (online clients) and plain dates (fixtures);
# naive values are read as UTC so they can be compared.
_EARLIEST = datetime.min.replace(tzinfo=timezone.utc)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, int):
        return value
    if isinstance(value, list):
        return sorted((_normalize_value(v) for v in value), key=lambda x: str(x))
    if isinstance(value, dict):
        return {
            k: _normalize_value(v)
            for k, v in sorted(value.items(), key=lambda kv: kv[0])
        }
    return value


def _values_equal(a: Any, b: Any, mode: str) -> bool:
    if mode == "strict":
        return a == b
    # tolerant
    na = _normalize_value(a)
    nb = _normalize_value(b)
    return na == nb


def _stated_decimals(value: Any) -> int | None:
    """Decimal places of a number as its source wrote it (``"825.0"`` -> 1)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return 0
    if isinstance(value, float):
        text = repr(value)
    elif isinstance(value, str):
        text = value.strip()
    else:
        return None
    try:
        float(text)
    except ValueError:
        return None
    if "e" in text.lower():
        return None
    return len(text.split(".", 1)[1]) if "." in text else 0


def _precision_groups(
    assertions: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]] | None:
    """Group numbers that agree at the coarser stated precision; None if not numeric."""
    items = []
    for a in assertions:
        decimals = _stated_decimals(a.get("asserted_value"))
        try:
            number = float(assertion_value(a))
        except (TypeError, ValueError):
            return None
        if decimals is None:
            return None
        items.append((number, decimals, a))
    clusters: List[List[tuple]] = []
    for item in sorted(items, key=lambda i: i[0]):
        for cluster in clusters:
            if all(
                abs(item[0] - other[0]) <= 0.5 * 10 ** -min(item[1], other[1]) + 1e-9
                for other in cluster
            ):
                cluster.append(item)
                break
        else:
            clusters.append([item])
    return {
        f"~{c[0][0]!r}": [a for _, _, a in sorted(c, key=lambda i: -i[1])]
        for c in clusters
    }


def _group_assertions(
    assertions: List[Dict[str, Any]],
    mode: str,
    field_rules: Dict[str, Any] | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    if (field_rules or {}).get("numeric_agreement") == "stated_precision":
        groups = _precision_groups(assertions)
        if groups is not None:
            return groups
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for a in assertions:
        val = assertion_value(a)
        key = repr(val) if mode == "strict" else repr(_normalize_value(val))
        groups[key].append(a)
    return groups


def _at(assertion: Dict[str, Any], path: str) -> Any:
    node: Any = assertion
    for part in path.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node


def _partitions(
    assertions: List[Dict[str, Any]], paths: List[str]
) -> Dict[tuple, List[Dict[str, Any]]]:
    parts: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for a in assertions:
        parts[tuple(_at(a, p) for p in paths)].append(a)
    return dict(parts)


def _most_recent_group(
    groups: Dict[str, List[Dict[str, Any]]],
) -> Tuple[str, List[Dict[str, Any]]]:
    def group_recent(assertion_list: List[Dict[str, Any]]) -> datetime:
        dates = [_parse_dt(a.get("retrieved_at")) for a in assertion_list]
        dates = [d for d in dates if d]
        return max(dates) if dates else _EARLIEST

    best_key = None
    best_dt = _EARLIEST
    for k, group in groups.items():
        dt = group_recent(group)
        if dt > best_dt:
            best_key = k
            best_dt = dt
    if best_key is None:
        # fallback deterministic
        best_key = sorted(groups.keys())[0]
    return best_key, groups[best_key]


def _build_conflict(groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any] | None:
    if len(groups) <= 1:
        return None
    return {
        "type": "disagreement",
        "values": [assertion_value(g[0]) for g in groups.values()],
        "source_assertion_ids": [[a.get("id") for a in g] for g in groups.values()],
    }


def _comparable(
    assertions: List[Dict[str, Any]], mode: str, field_rules: Dict[str, Any]
) -> tuple:
    """(conflict, alternatives): disagreements inside comparable partitions only."""
    paths = field_rules.get("compare_within") or []
    if not paths:
        return _build_conflict(_group_assertions(assertions, mode, field_rules)), None
    partitions = _partitions(assertions, paths)
    conflicts = [
        c
        for part in partitions.values()
        if (c := _build_conflict(_group_assertions(part, mode, field_rules)))
    ]
    conflict = None
    if conflicts:
        conflict = {
            "type": "disagreement",
            "values": [v for c in conflicts for v in c["values"]],
            "source_assertion_ids": [
                ids for c in conflicts for ids in c["source_assertion_ids"]
            ],
        }
    alternatives = None
    if len(partitions) > 1:
        alternatives = {
            "type": "not_comparable",
            "compare_within": paths,
            "values": [
                {
                    "within": dict(zip(paths, key)),
                    "values": [
                        assertion_value(g[0])
                        for g in _group_assertions(part, mode, field_rules).values()
                    ],
                    "source_assertion_ids": [a.get("id") for a in part],
                }
                for key, part in sorted(partitions.items(), key=lambda kv: repr(kv[0]))
            ],
        }
    return conflict, alternatives


def resolve_field(
    field_path: str,
    assertions: List[Dict[str, Any]],
    selection_rules: Dict[str, Any],
    mode: str = "strict",
) -> Dict[str, Any]:
    """Resolve a canonical value for a single field.

    Returns a dict with selected_value, source_assertion_ids, and optional conflict.
    """

    field_rules = selection_rules.get("field_rules", {}).get(field_path, {})
    strategy = (
        field_rules.get("strategy")
        or selection_rules.get("strategy")
        or "priority_sources"
    )
    allow_multiple = field_rules.get("allow_multiple", False)
    priority_sources = selection_rules.get("priority_sources", [])

    if not assertions:
        return {
            "field": field_path,
            "selected_value": None,
            "source_assertion_ids": [],
            "conflict": None,
            "alternatives": None,
        }

    groups = _group_assertions(assertions, mode, field_rules)
    conflict_all, alternatives = _comparable(assertions, mode, field_rules)

    def support(selected: Dict[str, Any]) -> List[str]:
        """Every assertion that states the selected value, within its comparable
        partition: agreeing sources support it, other methods never do."""
        paths = field_rules.get("compare_within") or []
        pool = assertions
        if paths:
            key = tuple(_at(selected, p) for p in paths)
            pool = [a for a in assertions if tuple(_at(a, p) for p in paths) == key]
        for group in _group_assertions(pool, mode, field_rules).values():
            if any(a is selected for a in group):
                return [a.get("id") for a in group]
        return [selected.get("id")]

    # Strategy: priority_sources
    if strategy == "priority_sources" and priority_sources:
        for src in priority_sources:
            src_assertions = [
                a for a in assertions if a.get("source", {}).get("name") == src
            ]
            if not src_assertions:
                continue
            src_groups = _group_assertions(src_assertions, mode, field_rules)
            if allow_multiple:
                selected_values = [assertion_value(g[0]) for g in src_groups.values()]
                source_assertion_ids = [
                    a.get("id") for group in src_groups.values() for a in group
                ]
                return {
                    "field": field_path,
                    "selected_value": selected_values,
                    "source_assertion_ids": source_assertion_ids,
                    "conflict": conflict_all,
                    "alternatives": alternatives,
                }
            key, group = _most_recent_group(src_groups)
            selected_value = assertion_value(group[0])
            source_assertion_ids = support(group[0])
            return {
                "field": field_path,
                "selected_value": selected_value,
                "source_assertion_ids": source_assertion_ids,
                "conflict": conflict_all,
                "alternatives": alternatives,
            }

    # Strategy: most_recent
    if strategy == "most_recent":
        if allow_multiple:
            # all values ordered by most recent
            ordered = sorted(
                groups.values(),
                key=lambda group: _parse_dt(group[0].get("retrieved_at")) or _EARLIEST,
                reverse=True,
            )
            selected_values = [assertion_value(group[0]) for group in ordered]
            source_assertion_ids = [a.get("id") for group in ordered for a in group]
            return {
                "field": field_path,
                "selected_value": selected_values,
                "source_assertion_ids": source_assertion_ids,
                "conflict": conflict_all,
                "alternatives": alternatives,
            }
        key, group = _most_recent_group(groups)
        return {
            "field": field_path,
            "selected_value": assertion_value(group[0]),
            "source_assertion_ids": [a.get("id") for a in group],
            "conflict": conflict_all,
            "alternatives": alternatives,
        }

    # Strategy: most_frequent (default fallback)
    max_count = max(len(group) for group in groups.values())
    top_groups = {k: group for k, group in groups.items() if len(group) == max_count}

    if len(top_groups) == 1:
        key = next(iter(top_groups))
        group = top_groups[key]
        return {
            "field": field_path,
            "selected_value": assertion_value(group[0]),
            "source_assertion_ids": [a.get("id") for a in group],
            "conflict": conflict_all,
            "alternatives": alternatives,
        }

    # Tie
    key, group = _most_recent_group(top_groups)
    conflict = (
        conflict_all
        if field_rules.get("compare_within")
        else _build_conflict(top_groups)
    )
    return {
        "field": field_path,
        "selected_value": assertion_value(group[0]),
        "source_assertion_ids": [a.get("id") for a in group],
        "conflict": conflict,
        "alternatives": alternatives,
    }
