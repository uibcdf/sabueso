"""The source registry (devguide/sources/registry.yaml) and its generated page."""

import copy
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "source_registry", "tools/source_registry.py"
)
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


@pytest.fixture(scope="module")
def data():
    return registry.load()


def test_the_registry_is_valid(data):
    assert registry.problems(data) == []


def test_the_page_is_generated_from_the_registry(data):
    page = Path("docs/content/user/data_sources.md").read_text(encoding="utf-8")
    assert page == registry.render(data), "run: python tools/source_registry.py --write"


def test_every_source_module_is_in_use(data):
    in_use = {
        m for r in data["resources"] if r["status"] == "in_use" for m in r["module"]
    }
    assert "sabueso.tools.db.alphafold" in in_use


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda r: r.update(status="deferred", revisit_when=None), "revisit_when"),
        (lambda r: r.update(status="rejected", reason=None), "reason"),
        (lambda r: r.update(status="out_of_scope", owner=None), "owner"),
        (lambda r: r.update(status="unknown"), "unknown status"),
        (lambda r: r.update(category="nowhere"), "unknown category"),
        (lambda r: r.update(colour="blue"), "unknown keys"),
        (lambda r: r.update(module=["sabueso.tools.db.nowhere"]), "does not exist"),
    ],
)
def test_a_decision_without_its_basis_is_refused(data, change, message):
    broken = copy.deepcopy(data)
    (entry,) = [r for r in broken["resources"] if r["id"] == "biogrid"]
    change(entry)
    assert any(message in p for p in registry.problems(broken))


def test_an_unregistered_source_module_is_refused(data):
    broken = copy.deepcopy(data)
    broken["resources"] = [r for r in broken["resources"] if r["id"] != "alphafold_db"]
    assert "sabueso.tools.db.alphafold is not registered as an in_use resource" in (
        registry.problems(broken)
    )
