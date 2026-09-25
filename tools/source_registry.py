"""Validate the source registry and render its documentation page.

``devguide/sources/registry.yaml`` is the source of truth for the online resources
Sabueso uses, has set aside or has yet to review. ``python tools/source_registry.py
--write`` regenerates ``docs/content/user/data_sources.md`` from it, and ``--check``
fails when that page is out of date or the registry breaks a rule.
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "devguide" / "sources" / "registry.yaml"
PAGE = ROOT / "docs" / "content" / "user" / "data_sources.md"
STATUSES = (
    "in_use",
    "evaluating",
    "queued",
    "deferred",
    "rejected",
    "retired",
    "out_of_scope",
)
REQUIRED = ("id", "name", "url", "category", "status", "description", "since")
#: What each status must state besides the required keys.
STATUS_KEYS = {
    "in_use": ("reason", "access", "licence", "module"),
    "deferred": ("reason", "revisit_when"),
    "rejected": ("reason",),
    "retired": ("reason",),
    "out_of_scope": ("reason", "owner"),
}
KNOWN = set(REQUIRED) | {
    "reason",
    "access",
    "licence",
    "module",
    "via",
    "revisit_when",
    "owner",
    "proposed_by",
    "decided_by",
    "links",
}
ID = re.compile(r"[a-z0-9][a-z0-9_]*\Z")


def load(path: Path = REGISTRY) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def problems(data: Dict[str, Any]) -> List[str]:
    """Every rule the registry breaks, as messages; empty when it is valid."""
    out: List[str] = []
    if data.get("format") != 1:
        out.append(f"format must be 1, not {data.get('format')!r}")
    categories = data.get("categories") or {}
    resources = data.get("resources") or []
    ids = [r.get("id") for r in resources]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        out.append(f"{dup}: duplicated id")
    by_id = {r.get("id"): r for r in resources}
    for r in resources:
        rid = r.get("id") or "<no id>"
        for key in REQUIRED:
            if not r.get(key):
                out.append(f"{rid}: missing {key}")
        if r.get("id") and not ID.fullmatch(str(r["id"])):
            out.append(f"{rid}: ids are lower-case letters, digits and _")
        unknown = sorted(set(r) - KNOWN)
        if unknown:
            out.append(f"{rid}: unknown keys {unknown}")
        if r.get("status") not in STATUSES:
            out.append(f"{rid}: unknown status {r.get('status')!r}")
        if r.get("category") not in categories:
            out.append(f"{rid}: unknown category {r.get('category')!r}")
        for key in STATUS_KEYS.get(r.get("status"), ()):
            if not r.get(key):
                out.append(f"{rid}: a {r['status']} resource states its {key}")
        if not isinstance(r.get("since"), datetime.date):
            out.append(f"{rid}: since is a date (YYYY-MM-DD)")
        if r.get("via") and by_id.get(r["via"], {}).get("status") != "in_use":
            out.append(f"{rid}: via {r['via']!r} is not an in_use resource")
        for module in r.get("module") or []:
            if importlib.util.find_spec(module) is None:
                out.append(f"{rid}: module {module} does not exist")
    # Every source module is registered as in use.
    registered = {
        m
        for r in resources
        if r.get("status") == "in_use"
        for m in r.get("module") or []
    }
    for path in sorted((ROOT / "sabueso" / "tools" / "db").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        module = f"sabueso.tools.db.{path.stem}"
        if module not in registered:
            out.append(f"{module} is not registered as an in_use resource")
    return out


def render(data: Dict[str, Any]) -> str:
    categories = data["categories"]
    resources = data["resources"]
    lines = [
        "# Data sources",
        "",
        "<!-- Generated from devguide/sources/registry.yaml by",
        "     `python tools/source_registry.py --write`. Do not edit by hand. -->",
        "",
        "The online resources Sabueso uses, has set aside, or has yet to review. To",
        "propose one, open a discussion in the **Data sources** category of the",
        "repository's GitHub Discussions; triage adds it here as *queued*.",
        "",
    ]
    counts = {s: sum(1 for r in resources if r["status"] == s) for s in STATUSES}
    lines.append(
        "Summary: "
        + ", ".join(f"{s.replace('_', ' ')} {n}" for s, n in counts.items() if n)
        + "."
    )
    titles = {
        "in_use": "In use",
        "evaluating": "Being evaluated",
        "queued": "Queued for review",
        "deferred": "Deferred",
        "rejected": "Rejected",
        "retired": "Retired",
        "out_of_scope": "Out of scope for Sabueso",
    }
    for status in STATUSES:
        group = [r for r in resources if r["status"] == status]
        if not group:
            continue
        lines += ["", f"## {titles[status]}", ""]
        if status == "in_use":
            header = "| Resource | Category | Access | Licence | Since |"
            rows = [
                f"| [{r['name']}]({r['url']}) | {categories[r['category']]} | "
                f"{r['access']} | {r['licence']} | {r['since']} |"
                for r in group
            ]
        elif status in ("queued", "evaluating"):
            header = "| Resource | Category | What it would bring | Since |"
            rows = [
                f"| [{r['name']}]({r['url']}) | {categories[r['category']]} | "
                f"{r['description']} | {r['since']} |"
                for r in sorted(group, key=lambda r: (r["category"], r["name"].lower()))
            ]
        else:
            extra = {"deferred": "Revisit when", "out_of_scope": "Belongs to"}.get(
                status
            )
            header = (
                "| Resource | Reason | " + (f"{extra} | " if extra else "") + "Since |"
            )
            key = {"deferred": "revisit_when", "out_of_scope": "owner"}.get(status)
            rows = [
                f"| [{r['name']}]({r['url']}) | {r['reason']} | "
                + (f"{r[key]} | " if key else "")
                + f"{r['since']} |"
                for r in group
            ]
        lines.append(header)
        lines.append("|" + " --- |" * header.count(" | ") + " --- |")
        lines += [row.replace("\n", " ") for row in rows]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="regenerate the page")
    group.add_argument(
        "--check", action="store_true", help="validate, and compare the page"
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    data = load()
    found = problems(data)
    for problem in found:
        print(f"registry: {problem}")
    if found:
        return 1
    page = render(data)
    if args.write:
        PAGE.write_text(page, encoding="utf-8")
        print(f"wrote {PAGE.relative_to(ROOT)}")
        return 0
    if not PAGE.is_file() or PAGE.read_text(encoding="utf-8") != page:
        print("docs/content/user/data_sources.md is out of date: run --write")
        return 1
    print("OK: source registry and its page")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
