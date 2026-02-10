"""Load selection rules for Resolver."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_RULES_PATH = Path(__file__).with_name("selection_rules.json")


def load_selection_rules(path: str | Path | None = None) -> Dict[str, Any]:
    rules_path = Path(path) if path else DEFAULT_RULES_PATH
    return json.loads(rules_path.read_text(encoding="utf-8"))
