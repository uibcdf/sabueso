"""Check the reviewed recovery file set without assigning data permissions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("devguide/sources/fixture_delivery.json")


def inventory(root=ROOT):
    return json.loads((Path(root) / MANIFEST).read_text(encoding="utf-8"))


def _git_paths(root, *options):
    return set(
        subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "-z", *options, "--", "temp_data"],
        )
        .decode()
        .rstrip("\0")
        .split("\0")
    ) - {""}


def problems(
    root=ROOT, *, local_inputs=False, versioned_paths=None, candidate_paths=None
):
    """Check file identity, recorded terms and the prospective repository boundary."""
    root = Path(root).resolve()
    data = inventory(root)
    out = []
    if data.get("format") != "sabueso.fixture_delivery@1":
        out.append("Unsupported fixture delivery inventory format.")
    catalog = json.loads(
        (root / "sabueso/resolver/source_catalog.json").read_text(encoding="utf-8")
    )
    resources = {r["id"]: r for r in catalog["resources"]}
    versioned = _git_paths(root) if versioned_paths is None else set(versioned_paths)
    candidates = (
        _git_paths(root, "--cached", "--others", "--exclude-standard")
        if candidate_paths is None
        else set(candidate_paths)
    )
    seen = set()
    for row in data.get("files", []):
        name = row["path"]
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or len(relative.parts) < 3
            or relative.parts[0] != "temp_data"
        ):
            out.append(f"{name}: expected a contained temp_data file path.")
            continue
        if name in seen:
            out.append(f"{name}: duplicate inventory entry.")
        seen.add(name)
        if row.get("delivery") not in {"repository", "local_only"}:
            out.append(f"{name}: unknown delivery decision.")
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
            out.append(f"{name}: invalid original-byte digest.")
        source = resources.get(row.get("source_id"), {})
        terms = source.get("terms", {})
        terms_digest = hashlib.sha256(
            json.dumps(
                terms, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()
        if (
            any(
                row.get(key) != terms.get(term)
                for key, term in (
                    ("recorded_licence", "licence"),
                    ("reviewed", "reviewed"),
                    ("statement", "statement"),
                )
            )
            or row.get("terms_sha256") != terms_digest
        ):
            out.append(f"{name}: source terms changed; review the file decision.")
        if not row.get("basis"):
            out.append(f"{name}: missing file-specific decision basis.")
        if row["delivery"] == "local_only" and name in versioned:
            out.append(f"{name}: local-only input is present in the Git index.")
        if row["delivery"] == "local_only" and name in candidates:
            out.append(f"{name}: local-only input is not protected from Git inclusion.")
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            out.append(f"{name}: fixture path escapes the checkout or is a symlink.")
            continue
        required = row["delivery"] == "repository" or local_inputs
        if not path.is_file():
            if required:
                out.append(f"{name}: reviewed input is missing.")
            continue
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            out.append(f"{name}: original bytes changed; review the input and notice.")
    # Earlier committed fixtures have their existing declarations. Every newly
    # added input must enter the recovery inventory before it can be delivered.
    old = set(
        subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "ls-tree",
                "-rz",
                "--name-only",
                "HEAD",
                "temp_data",
            ],
        )
        .decode()
        .rstrip("\0")
        .split("\0")
    ) - {""}
    unexpected = candidates - old - seen - {"temp_data/NOTICE.md"}
    out.extend(
        f"{name}: new fixture has no reviewed delivery decision."
        for name in sorted(unexpected)
    )
    for name in data.get("local_qualification_tests", {}):
        if not (root / name).is_file():
            out.append(f"{name}: local qualification module is missing.")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument(
        "--local-inputs",
        action="store_true",
        help="Also require every local-only original.",
    )
    args = parser.parse_args()
    errors = problems(local_inputs=args.local_inputs)
    if errors:
        print("\n".join(errors))
        return 1
    data = inventory()
    public = sum(r["delivery"] == "repository" for r in data["files"])
    local = sum(r["delivery"] == "local_only" for r in data["files"])
    print(
        f"OK: {public} reviewed repository inputs; {local} protected local-only originals."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
