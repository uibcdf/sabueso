"""Validate a Card dict against the formal YAML schema (basic structural check)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import json
import yaml

SCHEMA = Path("schemas/card_schema_0.1.0.yaml")


def _load_schema() -> Dict[str, Any]:
    return yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))


def _is_leaf(node: Any) -> bool:
    return isinstance(node, dict) and ("value" in node and "evidence_ids" in node)


def _validate_node(schema_node: Any, data_node: Any, path: str, errors: list[str]) -> None:
    if schema_node == "*":
        return

    if _is_leaf(schema_node):
        if not isinstance(data_node, dict):
            errors.append(f"{path}: expected dict with value/evidence_ids")
            return
        if "value" not in data_node or "evidence_ids" not in data_node:
            errors.append(f"{path}: missing value/evidence_ids")
        return

    if isinstance(schema_node, dict):
        if not isinstance(data_node, dict):
            errors.append(f"{path}: expected dict")
            return
        for key, sub in schema_node.items():
            if key in {"note", "inherits", "schema"}:
                continue
            if key not in data_node:
                # optional fields are allowed to be missing
                continue
            _validate_node(sub, data_node[key], f"{path}.{key}" if path else key, errors)
        return

    # lists and primitives are not validated deeply in this minimal checker


def _wrap_meta(card: Dict[str, Any]) -> Dict[str, Any]:
    if "meta" not in card or not isinstance(card["meta"], dict):
        return card
    wrapped = dict(card)
    meta = {}
    for k, v in card["meta"].items():
        if isinstance(v, dict) and "value" in v and "evidence_ids" in v:
            meta[k] = v
        else:
            meta[k] = {"value": v, "evidence_ids": []}
    wrapped["meta"] = meta
    return wrapped


def validate_card(card: Dict[str, Any]) -> list[str]:
    schema = _load_schema()
    errors: list[str] = []
    base = schema.get("card_base", {})
    _validate_node(base, _wrap_meta(card), "", errors)
    return errors


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to card JSON file")
    args = parser.parse_args()

    data = json.loads(Path(args.path).read_text(encoding="utf-8"))
    errors = validate_card(data)
    if errors:
        print("Invalid card:")
        for err in errors:
            print("-", err)
        raise SystemExit(1)
    print("OK: card matches schema (basic)")


if __name__ == "__main__":
    main()
