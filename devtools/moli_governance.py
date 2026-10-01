"""Validate the local universal MOLI governance surface."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md",
    "MOLI_GUIDE.md",
    "devguide/AGENTS.md",
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
    if agents.is_file():
        content = agents.read_text(encoding="utf-8")
        if "MOLI_GUIDE.md" not in content:
            errors.append("AGENTS.md: must reference MOLI_GUIDE.md")
        if "MOLI_GUIDE.md#durable-instructions-for-development-agents" not in content:
            errors.append("AGENTS.md: must link to the agent-instruction lifecycle")
        if "devguide/AGENTS.md" not in content:
            errors.append(
                "AGENTS.md: must route developer-guide work to devguide/AGENTS.md"
            )
    nested = ROOT / "devguide/AGENTS.md"
    if nested.is_file():
        content = nested.read_text(encoding="utf-8")
        for reference in (
            "../AGENTS.md",
            "MOLI_GUIDE.md#reporting-bugs-and-proposals",
            "pending_bugs/",
            "pending_proposals/",
            "archive/",
        ):
            if reference not in content:
                errors.append(f"devguide/AGENTS.md: must reference {reference}")
    guide = ROOT / "MOLI_GUIDE.md"
    if guide.is_file():
        text = guide.read_text(encoding="utf-8")
        if (
            "Canonical source: https://github.com/uibcdf/moli/blob/main/MOLI_GUIDE.md"
            not in text
        ):
            errors.append("MOLI_GUIDE.md: canonical-source marker missing")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Local MOLI governance surface is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
