"""Offline, deterministic notebook reports of exact stored Card snapshots.

Recovers the July reporting workflow using current fields, relationships and
SourceAssertions. Rendering reads the card; it never refreshes or creates credit.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

from smonitor import signal

from sabueso._private.argdigest import arg_digest
from sabueso.core.residues import field_nodes

REPORT_FORMAT = "sabueso.card_notebook@1"


def _execution_directory() -> Path:
    """Use an explicit notebook frontend path, a calling script, or the cwd.

    Do not query Jupyter servers: rendering must also work without network access.
    """
    ipython = sys.modules.get("IPython")
    shell = ipython.get_ipython() if ipython else None
    source = (getattr(shell, "user_ns", {}) or {}).get("__vsc_ipynb_file__")
    if source:
        return Path(source).expanduser().resolve().parent
    source = getattr(sys.modules.get("__main__"), "__file__", None)
    if source and Path(source).suffix == ".py" and Path(source).is_file():
        return Path(source).resolve().parent
    return Path.cwd()


def _stem(card) -> str:
    name = (
        (card.get("names.canonical_name") or {}).get("value")
        or card.id
        or "sabueso_card"
    )
    name = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-") or "sabueso_card"


def _escape(value) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    return (
        html.escape(str(value if value is not None else ""), quote=False)
        .replace("[", "&#91;")
        .replace("]", "&#93;")
        .replace("`", "&#96;")
        .replace("|", "\\|")
        .replace("\n", "<br>")
    )


def _table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(_escape(value) for value in row) + " |" for row in rows
    )
    return "\n".join(lines)


def _cell(source, kind, index):
    cell = {
        "cell_type": kind,
        "id": hashlib.sha256(f"{kind}:{index}:{source}".encode()).hexdigest()[:12],
        "metadata": {},
        "source": source,
    }
    if kind == "code":
        cell.update(execution_count=None, outputs=[])
    return cell


@signal(tags=["api", "report"])
@arg_digest()
def write_notebook(
    card,
    path=".",
    *,
    title=None,
    mode="full",
    language="en",
    include_code=True,
    include_card_snapshot=False,
    skip_digestion=False,
) -> Path:
    """Render a snapshot report; optionally save a sealed card beside it.

    ``full`` includes every stored field and assertion. ``minimal`` summarizes
    field and relationship counts without asserting that omitted values are absent.
    The scientific card schema and acquisition/attribution sidecars are unchanged.
    """
    output = Path(path).expanduser()
    if not output.is_absolute():
        output = _execution_directory() / output
    if output.suffix != ".ipynb":
        if output.suffix and not output.is_dir():
            raise ValueError("path must be a directory or an .ipynb file")
        output = output / f"{_stem(card)}.ipynb"
    data = card.to_dict()
    snapshot_id = card.snapshot_id()
    card_ref = card.pinned_ref() if card.id else None
    nodes = list(field_nodes(data["sections"]))
    assertions = data["source_assertion_store"]
    relationships = data["relationship_store"]
    known = {assertion["id"] for assertion in assertions}
    missing = sorted(
        (
            {
                identifier
                for _, node in nodes
                for identifier in node.get("source_assertion_ids") or []
            }
            | {
                identifier
                for rel in relationships
                for identifier in rel.get("source_assertion_ids") or []
            }
        )
        - known
    )
    labels = {
        "en": (
            "Scope and coverage",
            "Stored knowledge",
            "Relationships",
            "Conflicts and alternatives",
            "SourceAssertions and reproducibility",
        ),
        "es": (
            "Alcance y cobertura",
            "Conocimiento almacenado",
            "Relaciones",
            "Conflictos y alternativas",
            "Afirmaciones de fuentes y reproducibilidad",
        ),
    }[language]
    cells = []

    def markdown(text):
        cells.append(_cell(text, "markdown", len(cells)))

    name = (card.get("names.canonical_name") or {}).get("value") or "Sabueso Card"
    markdown(
        f"# {_escape(title or name)}\n\n**Card:** {_escape(card_ref or snapshot_id)}  \n**Schema:** {_escape(card.meta.get('schema_version'))}"
    )
    markdown(
        f"## {labels[0]}\n\n"
        + (
            "This report reads stored knowledge only. Missing information is not biological absence."
            if language == "en"
            else "Este informe lee únicamente conocimiento almacenado. La información ausente no demuestra ausencia biológica."
        )
        + "\n\n"
        + _table(
            ["Source", "Status", "Version", "Detail"],
            (
                (
                    row.get("source"),
                    row.get("status"),
                    row.get("version"),
                    row.get("detail"),
                )
                for row in data["quality"].get("enrichments") or []
            ),
        )
    )
    sections = {}
    for path_name, node in nodes:
        sections.setdefault(path_name.split(".")[0], []).append((path_name, node))
    for section, items in sections.items():
        if mode == "full":
            rows = []
            for field, node in items:
                value = (
                    {"value": node["value"], "unit": node["unit"]}
                    if "unit" in node
                    else node["value"]
                )
                rows.append((field, value, node.get("source_assertion_ids") or []))
            markdown(
                f"## {labels[1]}: {_escape(section)}\n\n"
                + _table(["Field", "Value", "SourceAssertion ids"], rows)
            )
        else:
            markdown(
                f"## {labels[1]}: {_escape(section)}\n\n"
                + _table(
                    ["Field", "Items", "SourceAssertion ids"],
                    (
                        (
                            field,
                            len(node["value"])
                            if isinstance(node["value"], list)
                            else 1,
                            node.get("source_assertion_ids") or [],
                        )
                        for field, node in items
                    ),
                )
            )
    rows = (
        (
            rel.get("subject_ref"),
            rel.get("predicate"),
            rel.get("object_ref"),
            rel.get("qualifiers"),
            rel.get("source_assertion_ids"),
        )
        for rel in relationships
    )
    if mode == "full":
        markdown(
            f"## {labels[2]}\n\n"
            + _table(
                ["Subject", "Predicate", "Object", "Qualifiers", "SourceAssertion ids"],
                rows,
            )
        )
    else:
        from collections import Counter

        markdown(
            f"## {labels[2]}\n\n"
            + _table(
                ["Predicate", "Count"],
                sorted(
                    Counter(
                        rel.get("predicate", "unknown") for rel in relationships
                    ).items()
                ),
            )
        )
    markdown(
        f"## {labels[3]}\n\n"
        + _table(
            ["Kind", "Stored reports"],
            (
                (key, data["quality"].get(key) or [])
                for key in ("conflicts", "alternatives", "qualifier_conflicts")
            ),
        )
    )
    markdown(f"## {labels[4]}\n\n" + _table(["Missing support ids"], [(missing,)]))
    if mode == "full":
        markdown(
            _table(
                [
                    "Id",
                    "Subject",
                    "Field",
                    "Asserted value",
                    "Source",
                    "Retrieved",
                    "Source metadata",
                    "Normalization",
                ],
                (
                    (
                        row.get("id"),
                        row.get("subject_ref"),
                        row.get("field_path"),
                        row.get("asserted_value"),
                        row.get("source"),
                        row.get("retrieved_at"),
                        row.get("source_metadata"),
                        row.get("normalized_value"),
                    )
                    for row in assertions
                ),
            )
        )
    markdown(
        "Runtime acquisition and attribution are separate from the scientific snapshot. Keep original sidecars; this report does not create new credit."
    )
    if include_code and include_card_snapshot:
        source = (
            "from pathlib import Path\n"
            "from sabueso.core.card import Card\n\n"
            f"snapshot_path = Path({output.with_suffix('.card.json').name!r}).resolve()\n"
            "card = Card.from_json(snapshot_path)\n"
            f"assert card.snapshot_id() == {snapshot_id!r}\n"
            "card.to_notebook(\n"
            f"    snapshot_path.with_name({(output.stem + '_regenerated.ipynb')!r}),\n"
            f"    title={title!r}, mode={mode!r}, language={language!r},\n"
            "    include_code=True, include_card_snapshot=True,\n"
            ")\n"
        )
        cells.append(_cell(source, "code", len(cells)))
    from sabueso import __version__

    manifest = {
        "format": REPORT_FORMAT,
        "sabueso_version": __version__,
        "card_ref": card_ref,
        "snapshot_id": snapshot_id,
        "card_schema_version": card.meta.get("schema_version"),
        "mode": mode,
        "language": language,
        "missing_source_assertion_ids": missing,
        "includes_card_snapshot": include_card_snapshot,
        "runtime_sidecars_included": False,
    }
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"sabueso": manifest},
        "cells": cells,
    }
    serialized = (
        json.dumps(notebook, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    snapshot = (
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if include_card_snapshot
        else None
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if snapshot is not None:
        output.with_suffix(".card.json").write_text(snapshot, encoding="utf-8")
    output.write_text(serialized, encoding="utf-8")
    return output
