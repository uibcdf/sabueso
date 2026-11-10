"""The public combined B6 walkthrough reopens outside checkout without live science."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "examples/user_journeys/protein_context_review.py").is_file():
    ROOT = Path.cwd()
SCRIPT = ROOT / "examples/user_journeys/protein_context_review.py"
DATA = ROOT / "temp_data"

READER = """
import importlib, runpy, sys
import sabueso
from sabueso.core.card import Card

def forbidden(*args, **kwargs):
    raise AssertionError('Saved walkthrough used current science, acquisition or Card construction')

targets = {
    'card_knowledge_comparison_access': ['materialize'],
    'card_knowledge_diff_v2': ['compare'],
    'card_protein_context_access': ['materialize'],
    'card_variant_access': ['materialize'],
    'card_sequence_change_access': ['materialize'],
    'knowledge_state': ['knowledge_state'],
    'scoped_tissue_usage': ['variant_view', 'isoform_view'],
    'source_assertion_store': ['make_source_assertion'],
    'relationship_store': ['make_derivation'],
}
modules = {name: importlib.import_module('sabueso.core.' + name) for name in targets}
for name, attributes in targets.items():
    for attribute in attributes:
        setattr(modules[name], attribute, forbidden)
sabueso.resolve = forbidden
Card.__init__ = Card.from_dict = Card.compare_knowledge = Card.knowledge_state = forbidden
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
    parent = tmp_path_factory.mktemp("protein-context-review")
    output = parent / "results"
    # The example itself is copied: its independent reader cannot use script siblings.
    script = parent / "review.py"
    shutil.copyfile(SCRIPT, script)
    with pytest.MonkeyPatch.context() as inherited:
        inherited.setenv("PYTHONIOENCODING", "cp1252")
        for command in ("produce", "read"):
            result = invoke(script, command, output)
            assert result.returncode == 0, result.stdout + result.stderr
    return script, output


def test_public_complete_b6_review_has_positive_source_and_agent_routes(walkthrough):
    _, output = walkthrough
    manifest = json.loads((output / "review.json").read_text(encoding="utf-8"))
    assert manifest["format"] == "sabueso.protein_context_review_example@1"
    assert manifest["acceptance"] == "technical_preparation_only"
    routes = {
        route["question"]: route
        for session in manifest["sessions"].values()
        for route in session["routes"]
    }
    assert set(routes) == {
        "related_proteins",
        "sequence_differences",
        "knowledge_differences",
        "variant_tissue_context",
        "isoform_tissue_context",
        "sequence_changes",
        "protein_associations",
    }
    assert routes["variant_tissue_context"]["count"] == 15
    assert routes["isoform_tissue_context"]["count"] == 3
    assert all(
        route["count"] > 0 and route["source"]["source"] for route in routes.values()
    )
    assert routes["knowledge_differences"]["options"] == {
        "mode": "knowledge",
        "other_ref": routes["sequence_differences"]["options"]["other_ref"],
        "residue_map": None,
    }


def test_saved_walkthrough_refuses_a_different_recorded_result(walkthrough, tmp_path):
    script, output = walkthrough
    changed = tmp_path / "changed"
    shutil.copytree(output, changed)
    path = changed / "review.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["sessions"]["comparisons"]["routes"][0]["result_ref"] = (
        "not-the-observed-result"
    )
    path.write_text(json.dumps(manifest), encoding="utf-8")
    result = invoke(script, "read", changed)
    assert result.returncode != 0
    assert "Original route changed: related_proteins" in result.stderr


def test_walkthrough_protects_existing_output(walkthrough):
    script, output = walkthrough
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    result = invoke(script, "produce", output)
    assert result.returncode != 0
    assert "Choose an empty output directory" in result.stderr
    assert before == {path.name: path.read_bytes() for path in output.iterdir()}
