"""Every non-Python file the package needs is shipped (uibcdf/sabueso#35).

0.1.0 was published without sabueso/resolver/selection_rules.json because setuptools
installs only .py files unless package-data says otherwise; the tests, run from the
checkout, could not notice.
"""

import fnmatch
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "sabueso"
NOT_SHIPPED = {
    "mappings/README.md"
}  # documentation for developers, not read at runtime


def test_every_runtime_data_file_is_declared_as_package_data():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = pyproject["tool"]["setuptools"]["package-data"]["sabueso"]
    data_files = sorted(
        p.relative_to(PACKAGE).as_posix()
        for p in PACKAGE.rglob("*")
        if p.is_file()
        and p.suffix not in {".py", ".pyc"}
        and "__pycache__" not in p.parts
    )
    assert data_files, "the scan must find the package's data files"
    undeclared = [
        f
        for f in data_files
        if f not in NOT_SHIPPED and not any(fnmatch.fnmatch(f, pat) for pat in patterns)
    ]
    assert undeclared == []
