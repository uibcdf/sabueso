"""Early, read-only dependency-contract preflight (uibcdf/sabueso#76).

MOLI's distribution policy asks each component to check, before an expensive candidate
build, that every route installing its runtime agrees with ``pyproject.toml``, which
stays the authority for runtime names, constraints and ``requires-python``. The routes
and the reasons for excluding some are listed in ``devtools/dependency_routes.toml``.

For each checked route it fails on:
- a required runtime dependency that is missing;
- a weaker or stale floor, or a missing constraint (an exact pin counts as its version);
- a ceiling above the public one;
- a missing, or incompatible, Python constraint.

It also fails on a conda environment, recipe or package-installing workflow that the
inventory does not list. It never rewrites a file, and never weakens metadata to pass.
Standard library only, so it runs before any environment is built:

    python devtools/dependency_preflight.py [--root PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

Version = Tuple[int, ...]
_SPEC = re.compile(r"(>=|<=|==|~=|!=|<|>|=)\s*([0-9][0-9A-Za-z.*]*)")


def _version(text: str) -> Version:
    parts = []
    for piece in text.split("."):
        digits = re.match(r"\d+", piece)
        if not digits:
            break
        parts.append(int(digits.group()))
    return tuple(parts)


def _bounds(spec: str) -> Tuple[Optional[Version], Optional[Version], bool]:
    """``(floor, ceiling, exact)`` of a version constraint. An exact pin (``==`` or
    conda's ``name=version=build``) is both floor and ceiling. The ceiling is exclusive
    for ``<``, and inclusive for an exact pin (``exact`` says which)."""
    floor = ceiling = None
    exact = False
    for op, value in _SPEC.findall(spec):
        v = _version(value)
        if op in (">=", ">", "~="):
            floor = v
        elif op in ("<", "<="):
            ceiling = v
        elif op in ("==", "="):
            floor = ceiling = v
            exact = True
    return floor, ceiling, exact


def _name_and_spec(entry: str) -> Tuple[str, str]:
    entry = entry.split("#", 1)[0].strip()
    entry = entry.split("::", 1)[-1]  # channel prefix of a conda spec
    match = re.match(r"([A-Za-z0-9_.\-]+)\s*(.*)$", entry)
    if not match:
        return "", ""
    name, spec = match.group(1).lower(), match.group(2).strip()
    # conda's name=version=build: keep the version as an exact pin.
    if spec.startswith("=") and not spec.startswith("=="):
        spec = "=" + spec[1:].split("=", 1)[0]
    return name, spec


def public_contract(root: Path) -> Tuple[Dict[str, str], str]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    required = dict(_name_and_spec(d) for d in project.get("dependencies", []))
    return required, project.get("requires-python", "")


def _list_after(lines: List[str], header: str) -> List[str]:
    """Entries of a YAML list that follows ``header`` (``dependencies:``, ``run:``)."""
    out, inside, indent = [], False, None
    for line in lines:
        stripped = line.strip()
        if not inside:
            if stripped == header:
                inside, indent = True, len(line) - len(line.lstrip())
            continue
        if not stripped or stripped.startswith("#"):
            continue
        current = len(line) - len(line.lstrip())
        if stripped.startswith("- ") and current >= indent:
            out.append(stripped[2:])
        elif current <= indent:
            break
    return out


def route_specs(path: Path, kind: str) -> Dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if kind == "recipe":
        entries = _list_after(lines, "run:")
    elif kind == "environment":
        entries = _list_after(lines, "dependencies:")
    elif kind == "pins":
        entries = [
            s
            for line in lines
            for s in [line.strip()]
            if "::" in s and "=" in s and not s.startswith("#")
        ] + [s for line in lines for s in [line.strip()] if s.startswith("python=")]
    else:
        return {}
    specs: Dict[str, str] = {}
    for entry in entries:
        name, spec = _name_and_spec(entry)
        if name == "python" and "${{" in spec:
            spec = ""  # a matrix value; the workflow's matrix lists supported versions
        if name:
            specs[name] = spec
    return specs


def check_route(
    route: str, specs: Dict[str, str], required: Dict[str, str], python: str, kind: str
) -> List[str]:
    problems = []
    for name, public in sorted(required.items()):
        p_floor, p_ceiling, _ = _bounds(public)
        if name not in specs:
            problems.append(
                f"{route}: missing required runtime dependency {name} {public}"
            )
            continue
        floor, ceiling, exact = _bounds(specs[name])
        if p_floor and (floor is None or floor < p_floor):
            stated = specs[name] or "no constraint"
            problems.append(
                f"{route}: {name} {stated} is weaker than the public floor {public}"
            )
        if (
            p_ceiling
            and ceiling
            and (ceiling > p_ceiling or (exact and ceiling == p_ceiling))
        ):
            problems.append(
                f"{route}: {name} {specs[name]} goes above the public ceiling {public}"
            )
    p_floor, p_ceiling, _ = _bounds(python)
    py = specs.get("python")
    if kind in ("recipe", "environment"):
        if py is None:
            problems.append(f"{route}: missing Python constraint (public {python})")
        else:
            floor, ceiling, exact = _bounds(py)
            if floor is None or (p_floor and floor < p_floor):
                problems.append(
                    f"{route}: python {py or 'unconstrained'} is weaker than {python}"
                )
            if p_ceiling and (ceiling is None or ceiling > p_ceiling):
                problems.append(
                    f"{route}: python {py or 'unconstrained'} allows versions {python} excludes"
                )
    return problems


def unlisted_routes(root: Path, listed: Dict[str, dict]) -> List[str]:
    found = set()
    for path in (root / "devtools" / "conda-envs").glob("*.y*ml"):
        found.add(path.relative_to(root).as_posix())
    for path in (root / "devtools").rglob("meta.yaml"):
        found.add(path.relative_to(root).as_posix())
    for path in (root / ".github" / "workflows").glob("*.y*ml"):
        text = path.read_text(encoding="utf-8")
        if re.search(
            r"environment-file:|create-args:|pip install|conda install|mamba install",
            text,
        ):
            found.add(path.relative_to(root).as_posix())
    return sorted(
        f"{r}: installs packages but is not in dependency_routes.toml"
        for r in found - set(listed)
    )


def preflight(root: Path) -> List[str]:
    inventory = tomllib.loads(
        (root / "devtools" / "dependency_routes.toml").read_text(encoding="utf-8")
    )
    routes = inventory.get("routes", {})
    required, python = public_contract(root)
    problems = unlisted_routes(root, routes)
    for route, entry in sorted(routes.items()):
        kind = entry.get("kind")
        path = root / route
        if kind == "excluded":
            if not entry.get("reason"):
                problems.append(f"{route}: excluded without a reason")
            continue
        if kind not in ("recipe", "environment", "pins"):
            problems.append(f"{route}: unknown kind {kind!r}")
            continue
        if not path.is_file():
            problems.append(f"{route}: listed but missing")
            continue
        problems += check_route(route, route_specs(path, kind), required, python, kind)
    source = inventory.get("source_routes", {})
    if source.get("applicable") is not False and not source.get("routes"):
        problems.append(
            "source_routes: declare applicable = false, or list the source lanes"
        )
    return problems


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--root", default=Path(__file__).resolve().parents[1], type=Path
    )
    args = parser.parse_args(argv)
    problems = preflight(args.root)
    for problem in problems:
        print(f"FAIL {problem}")
    if not problems:
        print("OK: every runtime route agrees with pyproject.toml")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
