"""Validate FIELD_PATHS vs card_schema_0.1.0.yaml"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

FIELD_PATHS = Path("devguide/FIELD_PATHS.md")
SCHEMA = Path("schemas/card_schema_0.1.0.yaml")


def load_schema_paths() -> List[str]:
    data = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    paths: List[str] = []

    def walk(prefix: str, obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in {"schema", "note", "inherits"}:
                    continue
                path = f"{prefix}.{k}" if prefix else k
                if isinstance(v, str) and v == "*":
                    paths.append(path + ".*")
                    continue
                if isinstance(v, dict) and ("value" in v or "evidence_ids" in v):
                    paths.append(path)
                else:
                    walk(path, v)
        elif isinstance(obj, list):
            pass

    for root in ("card_base", "protein_card", "peptide_card", "small_molecule_card"):
        if root in data:
            walk("", data[root])

    return sorted(set(paths))


def load_field_paths() -> List[str]:
    text = FIELD_PATHS.read_text(encoding="utf-8")
    out: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- `"):
            end = line.find("`", 3)
            if end != -1:
                out.append(line[3:end])
    return sorted(set(out))


def main() -> None:
    schema_paths = load_schema_paths()
    schema_wildcards = [p for p in schema_paths if p.endswith(".*")]
    schema_expanded = []
    for p in schema_paths:
        if not p.endswith(".*"):
            schema_expanded.append(p)
    schema_paths = schema_expanded
    field_paths = load_field_paths()

    missing_in_schema = [p for p in field_paths if p not in schema_paths]
    # allow wildcards (e.g., clinical.*)
    if schema_wildcards:
        filtered = []
        for p in missing_in_schema:
            if any(p.startswith(w[:-1]) for w in schema_wildcards):
                continue
            filtered.append(p)
        missing_in_schema = filtered
    missing_in_field_paths = [p for p in schema_paths if p not in field_paths]

    if missing_in_schema:
        print("Missing in schema:")
        for p in missing_in_schema:
            print("-", p)
    if missing_in_field_paths:
        print("Missing in FIELD_PATHS:")
        for p in missing_in_field_paths:
            print("-", p)

    if not missing_in_schema and not missing_in_field_paths:
        print("OK: FIELD_PATHS and schema are aligned")


if __name__ == "__main__":
    main()
