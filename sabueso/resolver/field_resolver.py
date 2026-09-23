"""Field-level resolver: selects a canonical value from competing SourceAssertions."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple

from sabueso.core.source_assertion_store import assertion_value


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


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
        return {k: _normalize_value(v) for k, v in sorted(value.items(), key=lambda kv: kv[0])}
    return value


def _values_equal(a: Any, b: Any, mode: str) -> bool:
    if mode == "strict":
        return a == b
    # tolerant
    na = _normalize_value(a)
    nb = _normalize_value(b)
    return na == nb


def _group_assertions(assertions: List[Dict[str, Any]], mode: str) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for a in assertions:
        val = assertion_value(a)
        key = repr(val) if mode == "strict" else repr(_normalize_value(val))
        groups[key].append(a)
    return groups


def _most_recent_group(groups: Dict[str, List[Dict[str, Any]]]) -> Tuple[str, List[Dict[str, Any]]]:
    def group_recent(assertion_list: List[Dict[str, Any]]) -> datetime:
        dates = [_parse_dt(a.get("retrieved_at")) for a in assertion_list]
        dates = [d for d in dates if d]
        return max(dates) if dates else datetime.min

    best_key = None
    best_dt = datetime.min
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
    strategy = field_rules.get("strategy") or selection_rules.get("strategy") or "priority_sources"
    allow_multiple = field_rules.get("allow_multiple", False)
    priority_sources = selection_rules.get("priority_sources", [])

    if not assertions:
        return {
            "field": field_path,
            "selected_value": None,
            "source_assertion_ids": [],
            "conflict": None,
        }

    groups = _group_assertions(assertions, mode)
    conflict_all = _build_conflict(groups)

    # Strategy: priority_sources
    if strategy == "priority_sources" and priority_sources:
        for src in priority_sources:
            src_assertions = [a for a in assertions if a.get("source", {}).get("name") == src]
            if not src_assertions:
                continue
            src_groups = _group_assertions(src_assertions, mode)
            if allow_multiple:
                selected_values = [assertion_value(g[0]) for g in src_groups.values()]
                source_assertion_ids = [a.get("id") for group in src_groups.values() for a in group]
                return {
                    "field": field_path,
                    "selected_value": selected_values,
                    "source_assertion_ids": source_assertion_ids,
                    "conflict": conflict_all,
                }
            key, group = _most_recent_group(src_groups)
            selected_value = assertion_value(group[0])
            source_assertion_ids = [a.get("id") for a in group]
            return {
                "field": field_path,
                "selected_value": selected_value,
                "source_assertion_ids": source_assertion_ids,
                "conflict": conflict_all,
            }

    # Strategy: most_recent
    if strategy == "most_recent":
        if allow_multiple:
            # all values ordered by most recent
            ordered = sorted(
                groups.values(),
                key=lambda group: _parse_dt(group[0].get("retrieved_at")) or datetime.min,
                reverse=True,
            )
            selected_values = [assertion_value(group[0]) for group in ordered]
            source_assertion_ids = [a.get("id") for group in ordered for a in group]
            return {
                "field": field_path,
                "selected_value": selected_values,
                "source_assertion_ids": source_assertion_ids,
                "conflict": conflict_all,
            }
        key, group = _most_recent_group(groups)
        return {
            "field": field_path,
            "selected_value": assertion_value(group[0]),
            "source_assertion_ids": [a.get("id") for a in group],
            "conflict": conflict_all,
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
        }

    # Tie
    key, group = _most_recent_group(top_groups)
    conflict = _build_conflict(top_groups)
    return {
        "field": field_path,
        "selected_value": assertion_value(group[0]),
        "source_assertion_ids": [a.get("id") for a in group],
        "conflict": conflict,
    }
