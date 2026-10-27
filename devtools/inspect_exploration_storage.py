"""Account for canonical storage and exact repeated view parts without restoring.

This diagnostic parses a local JSON artifact. It does not verify its scientific
claims or replace ``sabueso.read_exploration``. The full JSON tree is held in
memory; run large inputs under an owned memory supervisor. No source is queried.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON member: {key!r}")
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError(f"Non-finite JSON number: {value}")


def _fingerprint(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def _measure(value):
    """Match snapshot canonical JSON, encoding chunks rather than one large text."""
    encoder = json.JSONEncoder(
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    size, result = 0, hashlib.sha256()
    for text in encoder.iterencode(value):
        chunk = text.encode("utf-8")
        size += len(chunk)
        result.update(chunk)
    return size, result.hexdigest()


def inspect_storage(path):
    """Return an aggregate observation while preserving the original file."""
    path = Path(path)
    original = _fingerprint(path)
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream, object_pairs_hook=_unique, parse_constant=_nonfinite)
    if not isinstance(data, dict) or not isinstance(data.get("views"), dict):
        raise ValueError("Expected an exploration object with a views mapping.")
    if any(not isinstance(view, dict) for view in data["views"].values()):
        raise ValueError("Each stored view must be an object.")

    sections = {key: _measure(value)[0] for key, value in data.items()}
    framing = 2 + max(0, len(data) - 1) + sum(_measure(key)[0] + 1 for key in data)
    view_parts = {}
    for part in ("selection", "state", "native_payload", "flags"):
        total, count, distinct = 0, 0, {}
        for view in data["views"].values():
            if part not in view:
                continue
            size, key = _measure(view[part])
            total += size
            count += 1
            distinct.setdefault(key, size)
        unique = sum(distinct.values())
        view_parts[part] = {
            "occurrences": count,
            "distinct_canonical_values": len(distinct),
            "canonical_bytes": total,
            "distinct_canonical_bytes": unique,
            "repeated_occurrence_bytes": total - unique,
        }
    if _fingerprint(path) != original:
        raise ValueError("The input changed during inspection.")
    return {
        "format": "exploration_storage_observation@1",
        "owner": "uibcdf/sabueso#167",
        "review_trigger": "next persistence optimization or workload acceptance",
        "input": {"path": str(path), "sha256": original, "unchanged": True},
        "input_file_bytes": path.stat().st_size,
        "inspected_format": data.get("format"),
        "root_view_ref": data.get("root_view_ref"),
        "card_refs": sorted(data["cards"])
        if isinstance(data.get("cards"), dict)
        else None,
        "counts": {
            key: len(data[key])
            for key in ("cards", "inputs", "objects", "views", "locations")
            if isinstance(data.get(key), (dict, list))
        },
        "section_canonical_bytes": sections,
        "root_framing_bytes": framing,
        "canonical_total_bytes": sum(sections.values()) + framing,
        "view_parts": view_parts,
        "source_queries": 0,
        "verification": "parsed structure only; original scientific verification is separate",
        "limits": (
            "Exact repeated serialized values are physical storage candidates, "
            "not molecular identity or permission to discard history/support. "
            "Repeated-byte counts exclude reference/index overhead and are not "
            "an achieved reduction. Noncanonical input whitespace may change size."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    try:
        report = inspect_storage(args.input_file)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    report["python"] = sys.version
    report["platform"] = platform.platform()
    report["tool_sha256"] = _fingerprint(Path(__file__))
    report["source_head"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    args.output_directory.mkdir(parents=True, exist_ok=False)
    (args.output_directory / "observation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
