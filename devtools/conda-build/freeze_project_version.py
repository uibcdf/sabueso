#!/usr/bin/env python
"""Freeze the Conda package version into the ephemeral build source (uibcdf/sabueso#34).

conda-build copies the repository into a work directory. There, the dynamic versioningit
configuration is replaced by the package's own version, so the installed distribution
and ``sabueso.__version__`` report exactly the version of the conda package. The
repository itself is never modified.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

# MOLI release-version policy: public releases are X.Y.Z.
VERSION_PATTERN = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
PROJECT_VERSION_MARKER = 'dynamic = ["version"]'


def _without_versioningit_configuration(text: str) -> str:
    """Remove versioningit's configuration once the project version is static."""
    kept: list[str] = []
    skipping = False
    for line in text.splitlines(keepends=True):
        if line.startswith("["):
            skipping = line.startswith("[tool.versioningit")
        if not skipping:
            kept.append(line)
    return "".join(kept)


def freeze_project_version(root: Path, version: str) -> None:
    """Replace dynamic VCS versioning with the conda package version."""
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ValueError(f"Invalid package version (expected X.Y.Z): {version!r}")
    pyproject = root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    if text.count(PROJECT_VERSION_MARKER) != 1:
        raise RuntimeError(
            f"Expected one {PROJECT_VERSION_MARKER!r} marker in {pyproject}"
        )
    frozen = text.replace(PROJECT_VERSION_MARKER, f'version = "{version}"')
    frozen = frozen.replace('"versioningit~=3.0", ', "")
    pyproject.write_text(_without_versioningit_configuration(frozen), encoding="utf-8")
    (root / "sabueso" / "_version.py").write_text(
        f'__version__ = "{version}"\n', encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    args = parser.parse_args()
    freeze_project_version(Path.cwd(), args.version)


if __name__ == "__main__":
    main()
