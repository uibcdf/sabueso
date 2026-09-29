"""Validate the source registry and render its documentation page.

``devguide/sources/registry.yaml`` is the source of truth for the online resources
Sabueso uses, has set aside or has yet to review. ``python tools/source_registry.py
--write`` regenerates ``docs/content/user/data_sources.md`` and the packaged source
terms (``sabueso/resolver/source_terms.json``, #29) from it, and ``--check`` fails when
either is out of date or the registry breaks a rule.
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
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
    "limit",
    "note",
    "terms",
}
TERMS = ROOT / "sabueso" / "resolver" / "source_terms.json"
TERMS_KEYS = {"source_names", "licence", "attribution", "statement", "reviewed"}
ID = re.compile(r"[a-z0-9][a-z0-9_]*\Z")


def load(path: Path = REGISTRY) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _constant(path: str) -> Any:
    """The value of a module constant named by its dotted path, or None."""
    import importlib

    module, _, name = str(path).rpartition(".")
    try:
        return getattr(importlib.import_module(module), name)
    except (ImportError, AttributeError, ValueError):
        return None


def _licences() -> Dict[str, Any]:
    from sabueso.core.terms import LICENCES

    return LICENCES


def terms_export(data: Dict[str, Any]) -> str:
    """The terms of every source, by SourceAssertion source name, as packaged JSON."""
    sources: Dict[str, Any] = {}
    for r in data["resources"]:
        terms = r.get("terms")
        if not terms:
            continue
        for name in terms["source_names"]:
            sources[name] = {
                "registry_id": r["id"],
                "licence": terms["licence"],
                "attribution": terms["attribution"],
                "statement": terms["statement"],
                "reviewed": str(terms["reviewed"]),
                **({"caveats": terms["caveats"]} if terms.get("caveats") else {}),
            }
    body = {
        "note": "Generated from devguide/sources/registry.yaml by "
        "`python tools/source_registry.py --write`. Do not edit by hand.",
        "sources": dict(sorted(sources.items())),
    }
    return json.dumps(body, indent=1, ensure_ascii=False) + "\n"


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
        if (
            r.get("status") == "in_use"
            and any(m.startswith("sabueso.tools.db.") for m in r.get("module") or [])
            and "terms" not in r
        ):
            out.append(f"{rid}: a source Sabueso reads states its terms (#29)")
        if "terms" in r:
            terms = r["terms"] or {}
            missing = TERMS_KEYS - set(terms)
            if missing:
                out.append(f"{rid}: terms state {sorted(missing)}")
            elif terms["licence"] not in _licences():
                out.append(f"{rid}: terms licence {terms['licence']} is not classified")
            elif not isinstance(terms["reviewed"], datetime.date):
                out.append(f"{rid}: terms reviewed is a date (YYYY-MM-DD)")
        if "limit" in r:
            limit = r["limit"] or {}
            if set(limit) != {"constant", "of"}:
                out.append(f"{rid}: limit states its constant and what it counts (of)")
            elif not isinstance(_constant(limit["constant"]), int):
                out.append(f"{rid}: limit constant {limit['constant']} is not an int")
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
            header = "| Resource | Category | What it would bring | State | Since |"
            rows = [
                f"| [{r['name']}]({r['url']}) | {categories[r['category']]} | "
                f"{r['description']} | {r.get('note') or 'under review'} | "
                f"{r['since']} |"
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
        if status == "in_use":
            lines += _limits(group)
    return "\n".join(lines) + "\n"


def _limits(group: List[Dict[str, Any]]) -> List[str]:
    """Where Sabueso stops by default, with the value read from the code."""
    capped = [r for r in group if r.get("limit")]
    lines = [
        "",
        "### How much Sabueso asks for",
        "",
        "By default Sabueso asks each source for everything it states about an entry.",
        "Where an answer can be very large, a safety ceiling applies; an option such as",
        '`open_targets={"limit": n}` asks for fewer. A cut is never silent: the card',
        "records it as `truncated`, with the source's total when the source states one,",
        "and Sabueso warns. The other sources in use are read whole.",
        "",
        "| Resource | Default ceiling | Counts |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| {r['name']} | {_constant(r['limit']['constant'])} | {r['limit']['of']} |"
        for r in capped
    ]
    return lines


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
    terms = terms_export(data)
    if args.write:
        PAGE.write_text(page, encoding="utf-8")
        TERMS.write_text(terms, encoding="utf-8")
        print(f"wrote {PAGE.relative_to(ROOT)} and {TERMS.relative_to(ROOT)}")
        return 0
    if not PAGE.is_file() or PAGE.read_text(encoding="utf-8") != page:
        print("docs/content/user/data_sources.md is out of date: run --write")
        return 1
    if not TERMS.is_file() or TERMS.read_text(encoding="utf-8") != terms:
        print("sabueso/resolver/source_terms.json is out of date: run --write")
        return 1
    print("OK: source registry, its page and the packaged source terms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
