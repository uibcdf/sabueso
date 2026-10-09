"""Validate the source registry and render its documentation page.

``devguide/sources/registry.yaml`` is the source of truth for the online resources
Sabueso uses, has set aside or has yet to review. ``python tools/source_registry.py
--write`` regenerates ``docs/content/user/data_sources.md`` and the packaged source
terms (``sabueso/resolver/source_terms.json``, #29) and the public metadata catalog
(``sabueso/resolver/source_catalog.json``) from it. ``--check`` fails when a generated
artifact is out of date or the registry breaks a rule.
"""

from __future__ import annotations

import argparse
import ast
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
    "requires",
    "requires_note",
}
REQUIRES = {
    "account": "an account (login)",
    "key": "a personal key",
    "academic_licence": "an academic licence",
    "licence": "a licence",
    "agreement": "a written agreement",
}
TERMS = ROOT / "sabueso" / "resolver" / "source_terms.json"
CATALOG = ROOT / "sabueso" / "resolver" / "source_catalog.json"
CAPABILITIES_PAGE = ROOT / "docs/content/user/source_capabilities.md"
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


def _terms_owners(data: Dict[str, Any]) -> Dict[str, Any]:
    """One explicitly declared terms owner per scientific source name (#136)."""
    resources = {r["id"]: r for r in data["resources"]}
    if len(resources) != len(data["resources"]):
        raise ValueError("Duplicated resource ids cannot identify terms owners")
    owners: Dict[str, Any] = {}
    for r in data["resources"]:
        terms = r.get("terms")
        if not terms:
            continue
        names = terms.get("source_names")
        if (
            not isinstance(names, list)
            or not names
            or any(not isinstance(name, str) or not name.strip() for name in names)
            or len(set(names)) != len(names)
        ):
            raise ValueError(
                f"{r['id']}: terms source_names are unique nonempty strings"
            )
    for r in data["resources"]:
        terms = r.get("terms")
        if not terms:
            continue
        names = terms["source_names"]
        owner = r
        if "shared_with" in terms:
            rid = terms["shared_with"]
            if not isinstance(rid, str) or not rid or rid == r["id"]:
                raise ValueError(f"{r['id']}: invalid shared terms owner {rid!r}")
            owner = resources.get(rid)
            owned = (owner or {}).get("terms") or {}
            if (
                not owned
                or "shared_with" in owned
                or not set(names) <= set(owned.get("source_names") or [])
            ):
                raise ValueError(
                    f"{r['id']}: shared terms owner {rid!r} must directly declare {names}"
                )
            policy = {
                k: v
                for k, v in terms.items()
                if k not in {"source_names", "shared_with"}
            }
            canonical = {k: v for k, v in owned.items() if k != "source_names"}
            if policy != canonical:
                raise ValueError(f"{r['id']}: shared terms differ from owner {rid!r}")
        for name in names:
            if name in owners and owners[name]["id"] != owner["id"]:
                raise ValueError(
                    f"{name}: multiple terms owners {owners[name]['id']!r} and {owner['id']!r}; "
                    "declare shared_with explicitly"
                )
            owners[name] = owner
    return owners


def terms_export(data: Dict[str, Any]) -> str:
    """Terms by source name; refuse collisions even outside the registry gate."""
    sources: Dict[str, Any] = {}
    for name, owner in _terms_owners(data).items():
        terms = owner["terms"]
        sources[name] = {
            "registry_id": owner["id"],
            "licence": terms["licence"],
            "attribution": terms["attribution"],
            "statement": terms["statement"],
            "reviewed": str(terms["reviewed"]),
            **(
                {"retention_licence": terms["retention_licence"]}
                if terms.get("retention_licence")
                else {}
            ),
            **({"caveats": terms["caveats"]} if terms.get("caveats") else {}),
            **({"depositors": terms["depositors"]} if terms.get("depositors") else {}),
        }
    body = {
        "note": "Generated from devguide/sources/registry.yaml by "
        "`python tools/source_registry.py --write`. Do not edit by hand.",
        "sources": dict(sorted(sources.items())),
    }
    return json.dumps(body, indent=1, ensure_ascii=False) + "\n"


def capability_inventory(data, *, enrichers=None):
    """Describe code declarations and reviewed recovery inputs, without readiness inference."""
    if enrichers is None:
        from sabueso.enrichers import ENRICHERS

        enrichers = ENRICHERS
    delivery = json.loads(
        (ROOT / "devguide/sources/fixture_delivery.json").read_text(encoding="utf-8")
    )
    resources = {}
    for resource in sorted(data["resources"], key=lambda r: r["id"]):
        getters, mappings, clients = [], [], []
        for module in resource.get("module", []):
            spec = importlib.util.find_spec(module)
            if spec is None or not spec.origin or not spec.origin.endswith(".py"):
                continue
            tree = ast.parse(Path(spec.origin).read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = f"{module}.{node.name}"
                    if node.name.startswith("get_"):
                        getters.append(name)
                    elif node.name.startswith("map_"):
                        mappings.append(name)
                elif isinstance(node, ast.ClassDef) and node.name.startswith(
                    ("Online", "Fixture", "Snapshot")
                ):
                    clients.append(f"{module}.{node.name}")
        declarations = [
            {"option": e.option, "entity_type": e.entity_type, "areas": list(e.areas)}
            for e in enrichers
            if e.registry_id == resource["id"]
        ]
        inputs = [r for r in delivery["files"] if r["source_id"] == resource["id"]]
        resources[resource["id"]] = {
            "adoption_status": resource["status"],
            "via": resource.get("via"),
            "get_functions": sorted(getters),
            "mapping_functions": sorted(mappings),
            "client_classes": sorted(clients),
            "declared_enrichers": declarations,
            "recovery_inputs": {
                "repository": [
                    r["path"] for r in inputs if r["delivery"] == "repository"
                ],
                "local_only": [
                    r["path"] for r in inputs if r["delivery"] == "local_only"
                ],
            },
            "live_health": "not_assessed_by_offline_inventory",
            "consumer_acceptance": "not_assessed_by_offline_inventory",
        }
    return {
        "rule": "source_capability_inventory@1",
        "basis": "registry, Python declarations, ENRICHERS and reviewed recovery file inventory",
        "scope": "metadata_only; no source access, card admission, live-health or consumer qualification",
        "limits": [
            "Function/client lists describe local top-level definitions; imported aliases are not counted.",
            "An absent declared enricher does not describe established bespoke card routes.",
            "Recovery inputs cover reviewed recovered files and release compatibility cards, not all existing fixtures.",
            "Code declarations do not establish scientific completeness or public-package delivery.",
        ],
        "resources": resources,
    }


def render_capabilities(data):
    inventory = capability_inventory(data)
    lines = [
        "# Source capabilities in development",
        "",
        "<!-- Generated by python tools/source_registry.py --write. Do not edit by hand. -->",
        "",
        "This development inventory distinguishes native access, mappings and declared",
        "card contributions. It is derived from the maintained registry and code;",
        "`in_use` is adoption, not live availability, a complete scientific journey or",
        "public-package delivery. Established bespoke card routes are documented in",
        "the source architecture; absence of an enricher declaration alone does not",
        "describe those routes.",
        "",
        "The input counts below cover **reviewed recovery inputs and release compatibility cards**. They do not count",
        "older fixtures or grant reuse rights. Local-only originals are not distributed",
        "with the public repository. Native qualification of those scopes requires",
        "the explicit local test route; public tests use reviewed repository inputs.",
        "",
        "Use `sabueso.tools.sources.get_catalog()['capabilities']` to inspect full",
        "function/class names and file scopes under `source_capability_inventory@1`.",
        "",
        "| Source | Declared getters / mappings | Declared card options | Reviewed inputs: repository / local |",
        "| --- | --- | --- | --- |",
    ]
    for source in sorted(data["resources"], key=lambda r: r["name"].lower()):
        if source["status"] != "in_use":
            continue
        row = inventory["resources"][source["id"]]
        options = (
            ", ".join(f"`{e['option']}`" for e in row["declared_enrichers"])
            or "none declared"
        )
        access = f"{len(row['get_functions'])} / {len(row['mapping_functions'])}"
        if row["via"]:
            access += f"; via `{row['via']}`"
        counts = f"{len(row['recovery_inputs']['repository'])} / {len(row['recovery_inputs']['local_only'])}"
        lines.append(
            f"| [{source['name']}]({source['url']}) | {access} | {options} | {counts} |"
        )
    lines += [
        "",
        "See [data sources](data_sources.md) for scientific scopes, access requirements",
        "and recorded terms, and [scientific journeys](journeys.md) for bounded",
        "producer/reader/reacquisition acceptance. The catalogue performs no source queries.",
        "",
    ]
    return "\n".join(lines)


def catalog_export(data: Dict[str, Any]) -> str:
    """Package current decisions and category groups, without readiness or activation claims."""
    resources = []
    for resource in sorted(data["resources"], key=lambda r: r["id"]):
        record = dict(resource)
        if "limit" in record:
            record["limit"] = {
                **record["limit"],
                "value": _constant(record["limit"]["constant"]),
            }
        resources.append(record)
    catalog = {
        "format": "sabueso.source_catalog@1",
        "rule": "registry_catalog@1",
        "basis": "devguide/sources/registry.yaml; recorded_repository_decisions_not_live_source_health",
        "scope": "metadata_only; no_source_access_or_automatic_query_profile",
        "resources": resources,
        "capabilities": capability_inventory(data),
        "profiles": {
            category: {
                "name": name,
                "in_use": [
                    r["id"]
                    for r in resources
                    if r["category"] == category and r["status"] == "in_use"
                ],
                "other_statuses": {
                    status: [
                        r["id"]
                        for r in resources
                        if r["category"] == category and r["status"] == status
                    ]
                    for status in STATUSES
                    if status != "in_use"
                },
            }
            for category, name in data["categories"].items()
        },
    }

    def native_date(value):
        if isinstance(value, datetime.date):
            return value.isoformat()
        raise TypeError(f"Unsupported source registry value: {type(value).__name__}")

    return json.dumps(catalog, indent=1, ensure_ascii=False, default=native_date) + "\n"


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
        if "requires" in r:
            unknown = sorted(set(r["requires"] or []) - set(REQUIRES))
            if unknown or not r["requires"]:
                out.append(f"{rid}: requires is a list of {sorted(REQUIRES)}")
            if not r.get("requires_note"):
                out.append(f"{rid}: requires states its requires_note")
        if "terms" in r:
            terms = r["terms"] or {}
            missing = TERMS_KEYS - set(terms)
            if missing:
                out.append(f"{rid}: terms state {sorted(missing)}")
            elif terms["licence"] not in _licences():
                out.append(f"{rid}: terms licence {terms['licence']} is not classified")
            elif not isinstance(terms["reviewed"], datetime.date):
                out.append(f"{rid}: terms reviewed is a date (YYYY-MM-DD)")
            if (
                terms.get("retention_licence")
                and terms["retention_licence"] not in _licences()
            ):
                out.append(
                    f"{rid}: retention licence {terms['retention_licence']} is not classified"
                )
        if "limit" in r:
            limit = r["limit"] or {}
            if set(limit) != {"constant", "of"}:
                out.append(f"{rid}: limit states its constant and what it counts (of)")
            elif not isinstance(_constant(limit["constant"]), int):
                out.append(f"{rid}: limit constant {limit['constant']} is not an int")
    # Every source module is registered as in use.
    try:
        _terms_owners(data)
    except ValueError as error:
        out.append(str(error))
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
        "See [source capabilities](source_capabilities.md) for declared access, mapping,",
        "card contributions and recovered input scope; adoption is not complete integration.",
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
    lines += _requirements(resources)
    return "\n".join(lines) + "\n"


def _requirements(resources: List[Dict[str, Any]]) -> List[str]:
    """The sources that need an account, a key or a licence from the user (#94)."""
    needing = [r for r in resources if r.get("requires")]
    if not needing:
        return []
    titles = {
        "in_use": "in use",
        "evaluating": "being evaluated",
        "queued": "queued",
        "deferred": "deferred",
        "rejected": "rejected",
        "retired": "retired",
        "out_of_scope": "out of scope",
    }
    lines = [
        "",
        "## Sources that need an account, a key or a licence",
        "",
        "Some sources answer only to a registered user, or only under a licence the",
        "user holds. Sabueso never stores, logs or ships a user's credentials: a key or",
        "an account is passed to its client, or set in `SABUESO_<SERVICE>_KEY`, and a",
        "source that needs one it was not given is recorded as not queried. A licence",
        "or an agreement is the user's to obtain; Sabueso only reports which one binds.",
        "",
        "| Resource | Status | Needs | What |",
        "| --- | --- | --- | --- |",
    ]
    for r in sorted(needing, key=lambda r: (r["status"], r["name"].lower())):
        needs = ", ".join(REQUIRES[k] for k in r["requires"])
        lines.append(
            f"| [{r['name']}]({r['url']}) | {titles[r['status']]} | {needs} | "
            f"{r['requires_note']} |"
        )
    return lines


def _limits(group: List[Dict[str, Any]]) -> List[str]:
    """Where Sabueso stops by default, with the value read from the code."""
    capped = [r for r in group if r.get("limit")]
    lines = [
        "",
        "### How much Sabueso asks for",
        "",
        "An explicitly requested route preserves its declared received scope.",
        "Where an answer can be very large, a safety ceiling applies; an option such as",
        '`open_targets={"limit": n}` asks for fewer. A cut is never silent: the card',
        "records it as `truncated`, with the source's total when the source states one,",
        "and Sabueso warns. Standalone source scopes remain explicit; `in_use` never",
        "activates all providers or asks for unrequested records and links.",
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
    catalog = catalog_export(data)
    capabilities = render_capabilities(data)
    if args.write:
        PAGE.write_text(page, encoding="utf-8")
        TERMS.write_text(terms, encoding="utf-8")
        CATALOG.write_text(catalog, encoding="utf-8")
        CAPABILITIES_PAGE.write_text(capabilities, encoding="utf-8")
        print(
            f"wrote {PAGE.relative_to(ROOT)}, {TERMS.relative_to(ROOT)}, {CATALOG.relative_to(ROOT)} and {CAPABILITIES_PAGE.relative_to(ROOT)}"
        )
        return 0
    if not PAGE.is_file() or PAGE.read_text(encoding="utf-8") != page:
        print("docs/content/user/data_sources.md is out of date: run --write")
        return 1
    if not TERMS.is_file() or TERMS.read_text(encoding="utf-8") != terms:
        print("sabueso/resolver/source_terms.json is out of date: run --write")
        return 1
    if not CATALOG.is_file() or CATALOG.read_text(encoding="utf-8") != catalog:
        print("sabueso/resolver/source_catalog.json is out of date: run --write")
        return 1
    if (
        not CAPABILITIES_PAGE.is_file()
        or CAPABILITIES_PAGE.read_text(encoding="utf-8") != capabilities
    ):
        print("docs/content/user/source_capabilities.md is out of date: run --write")
        return 1
    print("OK: source registry, its page, packaged source terms and metadata catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
