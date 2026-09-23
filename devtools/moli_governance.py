"""Validate the local universal MOLI governance surface."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    "AGENTS.md",
    "MOLI_GUIDE.md",
    "devguide/pending_bugs/README.md",
    "devguide/pending_proposals/README.md",
    "devguide/archive/README.md",
    "devguide/templates/report.md",
]


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"{relative}: missing")
    agents = ROOT / "AGENTS.md"
    if agents.is_file() and "MOLI_GUIDE.md" not in agents.read_text(encoding="utf-8"):
        errors.append("AGENTS.md: must reference MOLI_GUIDE.md")
    guide = ROOT / "MOLI_GUIDE.md"
    if guide.is_file():
        text = guide.read_text(encoding="utf-8")
        if "Canonical source: https://github.com/uibcdf/moli/blob/main/MOLI_GUIDE.md" not in text:
            errors.append("MOLI_GUIDE.md: canonical-source marker missing")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Local MOLI governance surface is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
