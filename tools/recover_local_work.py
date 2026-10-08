"""Export the pre-pull local work as explicitly historical, verified source material.

This does not apply a stash or import an old package. Original source bytes and
snapshots stay available separately from the current implementation. Generated
scientific artifacts remain local under the ignored recovered_work/ directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath


def git(*arguments):
    return subprocess.check_output(["git", *arguments])


def export(revision: str, output: Path):
    revision = git("rev-parse", "--verify", revision).decode().strip()
    base = git("rev-parse", f"{revision}^1").decode().strip()
    changed = git("diff", "--name-only", "-z", base, revision).decode().split("\0")
    new = (
        git("ls-tree", "-r", "--name-only", "-z", f"{revision}^3").decode().split("\0")
    )
    records = []
    for original_revision, paths in ((revision, changed), (f"{revision}^3", new)):
        for path in sorted(p for p in paths if p):
            relative = PurePosixPath(path)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Unsafe historical path: {path}")
            if (
                relative.parts[0] == ".antigravitycli"
                or ".ipynb_checkpoints" in relative.parts
            ):
                records.append(
                    {"path": path, "disposition": "tool_state_or_notebook_checkpoint"}
                )
                continue
            content = git("show", f"{original_revision}:{path}")
            target = output / path
            if (
                target.is_symlink()
                or target.exists()
                and target.read_bytes() != content
            ):
                raise ValueError(
                    f"Refusing to replace different existing source material: {target}"
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            records.append(
                {
                    "path": path,
                    "disposition": "historical_original",
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "bytes": len(content),
                }
            )
    manifest = {
        "format": "sabueso.local_work_recovery@1",
        "stash": revision,
        "base_commit": base,
        "files": records,
        "warning": "Historical originals, not current APIs or validated migrated cards. Do not import the legacy sabueso tree into the development environment.",
    }
    manifest_path = output / "recovery_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stash",
        required=True,
        help="Exact stash commit, retained independently of its stack position",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("recovered_work/legacy_2026-07")
    )
    arguments = parser.parse_args()
    manifest = export(arguments.stash, arguments.output)
    restored = sum(
        row["disposition"] == "historical_original" for row in manifest["files"]
    )
    print(f"Exported and verified {restored} historical files to {arguments.output}")


if __name__ == "__main__":
    main()
