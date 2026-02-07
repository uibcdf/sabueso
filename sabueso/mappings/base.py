"""Mapping helpers (source → canonical)."""

from __future__ import annotations
from typing import Any, Dict, List


def get_in(data: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    """Safely traverse nested dicts/lists by key path."""
    cur: Any = data
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur
