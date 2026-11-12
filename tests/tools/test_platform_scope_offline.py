"""The prospective support exception keeps equivalent Linux/Windows release gates."""

from itertools import product
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def workflow(name):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def cells(job, python_key):
    matrix = job["strategy"]["matrix"]
    result = set(product(matrix["os"], matrix[python_key]))
    for row in matrix.get("include", []):
        result.add((row["os"], row[python_key]))
    for row in matrix.get("exclude", []):
        result.discard((row["os"], row[python_key]))
    return result


def test_current_source_and_staged_package_cover_every_claimed_os_and_minor():
    source = workflow("ci.yml")["jobs"]["test"]
    installed = workflow("test_staged_conda_package.yaml")["jobs"]["install"]
    required = set(
        product(("ubuntu-latest", "windows-latest"), ("3.11", "3.12", "3.13", "3.14"))
    )
    assert cells(source, "python-version") == cells(installed, "python") == required
    assert installed["needs"] == "verify-producer"
    for job in (source, installed):
        assert not job.get("continue-on-error", False)
        assert not any(step.get("continue-on-error", False) for step in job["steps"])
    run = "\n".join(step.get("run", "") for step in installed["steps"])
    assert "verify_staged_install.py" in run and "--sha256" in run
    assert "--receptor=ci" in run and '"$checker" installed --prefix' in run


def test_no_macos_lane_remains_in_automatic_ci_or_required_staging():
    for name in ("ci.yml", "test_staged_conda_package.yaml"):
        jobs = workflow(name)["jobs"]
        for job in jobs.values():
            runner = job["runs-on"]
            assert "macos" not in runner.lower()
            matrix = job.get("strategy", {}).get("matrix", {})
            assert not any("macos" in os.lower() for os in matrix.get("os", []))
            assert not any(
                "macos" in row.get("os", "").lower()
                for row in matrix.get("include", [])
            )
