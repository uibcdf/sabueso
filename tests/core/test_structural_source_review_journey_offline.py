"""The combined public structural review preserves positive and unknown scope."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "examples/user_journeys/structural_source_review.py").is_file():
    ROOT = Path.cwd()
SCRIPT = ROOT / "examples/user_journeys/structural_source_review.py"
DATA = ROOT / "temp_data"

READER = """
import importlib, runpy, sys
import sabueso
from sabueso.core.card import Card

def forbidden(*a, **k):
    raise AssertionError('Saved structural review used current science, fixtures or acquisition')

targets = {
    'card_scientific_access': ['materialize'],
    'card_assembly_access': ['materialize'],
    'card_assembly_access_v2': ['materialize'],
    'structures': ['structures_view', 'structure_inventory'],
    'structure_explanation': ['explain_structure_inventory'],
    'assembly_generation_v4': ['generation'],
    'assembly_generation_v5': ['generation'],
    'knowledge_state': ['knowledge_state'],
    'source_assertion_store': ['make_source_assertion'],
    'relationship_store': ['make_derivation'],
}
modules = {key: importlib.import_module('sabueso.core.' + key) for key in targets}
for name, attributes in targets.items():
    for attribute in attributes:
        setattr(modules[name], attribute, forbidden)
sabueso.resolve = forbidden
Card.__init__ = Card.from_dict = Card.structures = Card.assembly_generation = forbidden
def audit(event, args):
    if event == 'open' and 'temp_data' in str(args[0]).replace(chr(92), '/').split('/'):
        forbidden()
    if event == 'import' and args[0].split('.')[0] == 'molsysmt':
        forbidden()
sys.addaudithook(audit)
script = sys.argv.pop(1)
runpy.run_path(script, run_name='__main__')
"""


def invoke(script, command, output):
    arguments = [sys.executable, str(script)]
    if command == "read":
        arguments = [sys.executable, "-c", READER, str(script)]
    arguments.extend([command, "--output", str(output)])
    if command == "produce":
        arguments.extend(["--fixtures", str(DATA)])
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        arguments,
        cwd=output.parent,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=240,
        check=False,
    )


@pytest.fixture(scope="module")
def walkthrough(tmp_path_factory):
    parent = tmp_path_factory.mktemp("structural-source-review")
    script = parent / "review.py"
    output = parent / "results"
    shutil.copyfile(SCRIPT, script)
    with pytest.MonkeyPatch.context() as inherited:
        inherited.setenv("PYTHONIOENCODING", "cp1252")
        for command in ("produce", "read"):
            result = invoke(script, command, output)
            assert result.returncode == 0, result.stdout + result.stderr
    return script, output


def test_public_review_keeps_chain_contacts_and_assembly_declarations_separate(
    walkthrough,
):
    _, output = walkthrough
    manifest = json.loads((output / "review.json").read_text(encoding="utf-8"))
    assert manifest["format"] == "sabueso.structural_source_review_example@1"
    assert manifest["acceptance"] == "technical_preparation_only"
    current = manifest["sessions"]["current"]["observation"]
    assert current["complete_chains"] == ["A", "B"]
    assert [chain["missing_count"] for chain in current["chains"]] == [0, 0]
    assert current["coordinate_status"] == "comparable"
    assert current["reference_revision"] == "not_stated"
    assert [row["component_id"] for row in current["ligands"]] == ["BTS", "SO4"]
    assert [row["instance_count"] for row in current["ligands"]] == [1, 7]
    assert len(current["contacts"]) == 8
    assert sum(len(row["contacts"]["items"]) for row in current["contacts"]) > 0
    assert len(current["positions"]) == 12
    assert "K" in current["positions"][-2]["label"]
    assert "L" in current["positions"][-1]["label"]
    assert all(
        "No retained native match" in row["label"] for row in current["positions"][-2:]
    )
    assert current["physical_membership"] == "not_computed"
    assert current["agent_assembly"][0]["cells"]["declaration_count"]["value"] == 12
    assert len(current["sources"]) == 2
    assert (
        manifest["sessions"]["historical"]["observation"]["outcome"]["status"]
        == "missing_prerequisite"
    )


@pytest.mark.parametrize("change", ["source", "position-order"])
def test_review_refuses_changed_recorded_sources_or_component_order(
    walkthrough, tmp_path, change
):
    script, output = walkthrough
    changed = tmp_path / "changed"
    shutil.copytree(output, changed)
    path = changed / "review.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    current = manifest["sessions"]["current"]["observation"]
    if change == "source":
        current["sources"][0] = "different-source-digest"
    else:
        current["positions"].reverse()
    path.write_text(json.dumps(manifest), encoding="utf-8")
    result = invoke(script, "read", changed)
    assert result.returncode != 0
    assert "Original current structural observations changed" in result.stderr


def test_review_protects_existing_output(walkthrough):
    script, output = walkthrough
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    result = invoke(script, "produce", output)
    assert result.returncode != 0
    assert "Choose an empty output directory" in result.stderr
    assert before == {path.name: path.read_bytes() for path in output.iterdir()}
