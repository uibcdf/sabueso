"""The early dependency-contract preflight (uibcdf/sabueso#76, MOLI distribution policy).

Each negative case copies the repository's real routes into a temporary root, breaks one
thing, and checks that the preflight names the route and the constraint.
"""

import importlib.util
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "dependency_preflight", ROOT / "devtools" / "dependency_preflight.py"
)
preflight_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(preflight_module)
preflight = preflight_module.preflight


@pytest.fixture
def root(tmp_path):
    for relative in (
        "pyproject.toml",
        "devtools/dependency_routes.toml",
        "devtools/conda-build/meta.yaml",
        "devtools/conda-envs",
        ".github/workflows",
    ):
        source, target = ROOT / relative, tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy(source, target)
    return tmp_path


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_the_repository_passes():
    assert preflight(ROOT) == []


def test_a_missing_recipe_dependency_fails(root):
    recipe = root / "devtools/conda-build/meta.yaml"
    lines = recipe.read_text(encoding="utf-8").splitlines(keepends=True)
    recipe.write_text(
        "".join(line for line in lines if "- argdigest" not in line), encoding="utf-8"
    )
    (problem,) = preflight(root)
    assert (
        "meta.yaml" in problem
        and "missing required runtime dependency argdigest" in problem
    )


def test_an_environment_with_a_stale_floor_fails(root):
    _edit(
        root / "devtools/conda-envs/development_env.yaml",
        "smonitor >=0.17.0",
        "smonitor >=0.16.0",
    )
    (problem,) = preflight(root)
    assert "development_env.yaml: smonitor >=0.16.0 is weaker" in problem


def test_an_unconstrained_dependency_is_weaker(root):
    _edit(
        root / "devtools/conda-envs/test_env.yaml",
        "pyunitwizard >=0.27.0",
        "pyunitwizard",
    )
    (problem,) = preflight(root)
    assert "test_env.yaml: pyunitwizard no constraint is weaker" in problem


def test_a_staged_pin_below_the_floor_fails(root):
    _edit(
        root / ".github/workflows/test_staged_conda_package.yaml",
        "uibcdf::depdigest=0.11.0=py_2",
        "uibcdf::depdigest=0.10.1=py_0",
    )
    (problem,) = preflight(root)
    assert "test_staged_conda_package.yaml: depdigest =0.10.1 is weaker" in problem


def test_a_missing_or_wider_python_constraint_fails(root):
    _edit(root / "devtools/conda-envs/docs_env.yaml", "  - python >=3.11,<3.15\n", "")
    _edit(
        root / "devtools/conda-envs/test_env.yaml",
        "python >=3.11,<3.15",
        "python >=3.10",
    )
    problems = preflight(root)
    assert any("docs_env.yaml: missing Python constraint" in p for p in problems)
    assert any("test_env.yaml: python >=3.10 is weaker" in p for p in problems)
    assert any("test_env.yaml: python >=3.10 allows versions" in p for p in problems)


def test_an_unlisted_route_fails_until_reviewed(root):
    (root / "devtools/conda-envs/gpu_env.yaml").write_text(
        "dependencies:\n  - python >=3.11,<3.15\n", encoding="utf-8"
    )
    (problem,) = preflight(root)
    assert (
        "gpu_env.yaml: installs packages but is not in dependency_routes.toml"
        in problem
    )


def test_an_exclusion_needs_a_reason(root):
    _edit(
        root / "devtools/dependency_routes.toml",
        'reason = "installs build_env.yaml only, to remove a label"',
        "",
    )
    (problem,) = preflight(root)
    assert "withdraw_conda_package.yaml: excluded without a reason" in problem


def test_the_preflight_never_rewrites_a_file(root):
    _edit(
        root / "devtools/conda-envs/development_env.yaml",
        "smonitor >=0.17.0",
        "smonitor >=0.16.0",
    )
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    preflight(root)
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
