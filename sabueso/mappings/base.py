"""Mapping helpers (source → canonical)."""

from __future__ import annotations
from typing import Any, Dict, List


def get_in(data: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    """Safely traverse nested dicts/lists by key path."""
    cur: Any = data
    for key in path:
        if isinstance(cur, dict):
            if key in cur:
                cur = cur[key]
                continue
            return default
        if isinstance(cur, list) and isinstance(key, int):
            if 0 <= key < len(cur):
                cur = cur[key]
                continue
            return default
        return default
    return cur
