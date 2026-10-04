"""Reject stale or missing source modules/resources in a local diagnostic wheel."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
SUFFIXES = {".py", ".json", ".yaml", ".cff"}
GENERATED = "sabueso/_version.py"


def check(wheel: Path, root: Path = ROOT) -> list[str]:
    expected = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in (root / "sabueso").rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUFFIXES
        and path.relative_to(root).as_posix() != GENERATED
    }
    with ZipFile(wheel) as archive:
        actual = {
            name: archive.read(name)
            for name in archive.namelist()
            if name.startswith("sabueso/")
            and Path(name).suffix.lower() in SUFFIXES
            and name != GENERATED
        }
    errors = [f"missing: {name}" for name in sorted(expected.keys() - actual.keys())]
    errors += [
        f"unexpected: {name}" for name in sorted(actual.keys() - expected.keys())
    ]
    errors += [
        f"stale bytes: {name}"
        for name in sorted(expected.keys() & actual.keys())
        if expected[name] != actual[name]
    ]
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    options = parser.parse_args()
    errors = check(options.wheel)
    if errors:
        print("FAIL: local wheel differs from source")
        for error in errors:
            print(error)
        return 1
    print(
        "OK: local wheel modules/resources equal source (generated _version.py excluded)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
