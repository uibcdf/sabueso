"""Field-level resolver for canonical value selection."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple


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


def _group_evidences(evidences: List[Dict[str, Any]], mode: str) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in evidences:
        val = ev.get("value")
        key = repr(val) if mode == "strict" else repr(_normalize_value(val))
        groups[key].append(ev)
    return groups


def _most_recent_group(groups: Dict[str, List[Dict[str, Any]]]) -> Tuple[str, List[Dict[str, Any]]]:
    def group_recent(ev_list: List[Dict[str, Any]]) -> datetime:
        dates = [_parse_dt(ev.get("retrieved_at")) for ev in ev_list]
        dates = [d for d in dates if d]
        return max(dates) if dates else datetime.min

    best_key = None
    best_dt = datetime.min
    for k, evs in groups.items():
        dt = group_recent(evs)
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
        "values": [g[0].get("value") for g in groups.values()],
        "evidence_ids": [[ev.get("evidence_id") for ev in g] for g in groups.values()],
    }


def resolve_field(
    field_path: str,
    evidences: List[Dict[str, Any]],
    selection_rules: Dict[str, Any],
    mode: str = "strict",
) -> Dict[str, Any]:
    """Resolve a canonical value for a single field.

    Returns a dict with selected_value, evidence_ids, and optional conflict.
    """

    field_rules = selection_rules.get("field_rules", {}).get(field_path, {})
    strategy = field_rules.get("strategy") or selection_rules.get("strategy") or "priority_sources"
    allow_multiple = field_rules.get("allow_multiple", False)
    priority_sources = selection_rules.get("priority_sources", [])

    if not evidences:
        return {
            "field": field_path,
            "selected_value": None,
            "evidence_ids": [],
            "conflict": None,
        }

    groups = _group_evidences(evidences, mode)
    conflict_all = _build_conflict(groups)

    # Strategy: priority_sources
    if strategy == "priority_sources" and priority_sources:
        for src in priority_sources:
            src_evs = [ev for ev in evidences if ev.get("source", {}).get("name") == src]
            if not src_evs:
                continue
            src_groups = _group_evidences(src_evs, mode)
            if allow_multiple:
                selected_values = [g[0].get("value") for g in src_groups.values()]
                evidence_ids = [ev.get("evidence_id") for evs in src_groups.values() for ev in evs]
                return {
                    "field": field_path,
                    "selected_value": selected_values,
                    "evidence_ids": evidence_ids,
                    "conflict": conflict_all,
                }
            key, evs = _most_recent_group(src_groups)
            selected_value = evs[0].get("value")
            evidence_ids = [ev.get("evidence_id") for ev in evs]
            return {
                "field": field_path,
                "selected_value": selected_value,
                "evidence_ids": evidence_ids,
                "conflict": conflict_all,
            }

    # Strategy: most_recent
    if strategy == "most_recent":
        if allow_multiple:
            # all values ordered by most recent
            ordered = sorted(
                groups.values(),
                key=lambda evs: _parse_dt(evs[0].get("retrieved_at")) or datetime.min,
                reverse=True,
            )
            selected_values = [evs[0].get("value") for evs in ordered]
            evidence_ids = [ev.get("evidence_id") for evs in ordered for ev in evs]
            return {
                "field": field_path,
                "selected_value": selected_values,
                "evidence_ids": evidence_ids,
                "conflict": conflict_all,
            }
        key, evs = _most_recent_group(groups)
        return {
            "field": field_path,
            "selected_value": evs[0].get("value"),
            "evidence_ids": [ev.get("evidence_id") for ev in evs],
            "conflict": conflict_all,
        }

    # Strategy: most_frequent (default fallback)
    max_count = max(len(evs) for evs in groups.values())
    top_groups = {k: evs for k, evs in groups.items() if len(evs) == max_count}

    if len(top_groups) == 1:
        key = next(iter(top_groups))
        evs = top_groups[key]
        return {
            "field": field_path,
            "selected_value": evs[0].get("value"),
            "evidence_ids": [ev.get("evidence_id") for ev in evs],
            "conflict": conflict_all,
        }

    # Tie
    key, evs = _most_recent_group(top_groups)
    conflict = _build_conflict(top_groups)
    return {
        "field": field_path,
        "selected_value": evs[0].get("value"),
        "evidence_ids": [ev.get("evidence_id") for ev in evs],
        "conflict": conflict,
    }
