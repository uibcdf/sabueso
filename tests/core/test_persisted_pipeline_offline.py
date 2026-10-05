"""Fresh application processes retain attribution, historical support and failures."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path("examples/persisted_pipeline/run.py").resolve()
DATA = Path("temp_data").resolve()


def invoke(action, output, *, reader_guards=False):
    command = [sys.executable, str(SCRIPT)]
    if reader_guards:
        # A genuinely fresh reader with a different version and forbidden writers.
        command = [
            sys.executable,
            "-c",
            """
import runpy, sys
import ackredit, sabueso
from sabueso.tools.db import europepmc
def forbidden(*args, **kwargs):
    raise RuntimeError('Saved readers must not write credit or acquire knowledge')
ackredit.register_item = ackredit.track_item = forbidden
europepmc.get_article = sabueso.extract_literature_mentions = forbidden
sabueso.__version__ = '999.reader'
script = sys.argv.pop(1)
runpy.run_path(script, run_name='__main__')
""",
            str(SCRIPT),
        ]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [*command, action, "--output", str(output), "--fixtures", str(DATA)],
        cwd=output.parent,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


def read_json(path):
    return json.loads(path.read_text("utf-8"))


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    output = tmp_path_factory.mktemp("persisted-consumer") / "bundle"
    for action in ("produce", "read", "reuse", "read"):
        result = invoke(action, output, reader_guards=action == "read")
        assert result.returncode == 0, result.stdout + result.stderr
    return output


def test_fresh_reuse_advances_heads_but_keeps_original_item_and_bibliography(bundle):
    original = read_json(bundle / "original.manifest.json")
    reused = read_json(bundle / "reused.manifest.json")
    assert original["card_ref"] != reused["card_ref"]
    assert original["item_id"] == reused["item_id"]
    assert original["item_sha256"] == reused["item_sha256"]
    assert original["item_ref"] != reused["item_ref"]
    for stage in ("original", "reused"):
        reader = read_json(bundle / f"{stage}.reader.json")
        assert reader["observed_acquisitions"] == 0
        assert (
            reader["item_ref"]
            == read_json(bundle / f"{stage}.manifest.json")["item_ref"]
        )
        for detail in ("full", "index"):
            papers = read_json(bundle / f"{stage}.{detail}.references.csl.json")
            paper = next(
                p for p in papers if p.get("DOI") == "10.1107/s2053230x25006454"
            )
            assert len(paper["author"]) == 6 and paper["page"] == "381-387"
            attribution = read_json(bundle / f"{stage}.{detail}.attribution.json")
            assert attribution["producer"]["version"] != "999.reader"
    acquisition = read_json(bundle / "original.observations.json")["acquisitions"]
    (unavailable,) = [r for r in acquisition if r["outcome"] == "unavailable"]
    assert unavailable["network_attempts"] == 0
    assert unavailable["provider"]["status"] == "not_attempted"
    observations = read_json(bundle / "reused.observations.json")
    assert all(r["source"] != "Europe PMC" for r in observations["acquisitions"])
    (intake,) = observations["literature"]
    original_extraction = next(
        r
        for r in read_json(bundle / "original.observations.json")["literature"]
        if r["format"] == "sabueso.literature_extraction@1"
    )
    assert intake["original_extraction"] == original_extraction
    assert any(
        u["roles"] == ["reused_reference"]
        for u in intake["provider"]["attribution"]["uses"]
    )


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "changed",
        "packet_pin",
        "card_pin",
        "item_pin",
        "workflow",
        "workflow_uses",
        "missing_database",
        "scope",
        "format",
        "path",
    ],
)
def test_saved_reader_refuses_incomplete_or_misbound_records(bundle, tmp_path, defect):
    output = tmp_path / "copy"
    shutil.copytree(bundle, output)
    manifest_path = output / "original.manifest.json"
    manifest = read_json(manifest_path)
    filename = "original.full.attribution.json"
    path = output / filename
    if defect == "missing":
        path.unlink()
    elif defect == "missing_database":
        (output / "knowledge.db").unlink()
    elif defect == "changed":
        path.write_text("{}", encoding="utf-8")
    elif defect in ("packet_pin", "card_pin", "scope"):
        record = read_json(path)
        if defect == "packet_pin":
            record["packet_snapshot_id"] = "sha256:" + "0" * 64
        elif defect == "card_pin":
            record["scope"]["subject"]["card_ref"] = "another card"
        else:
            record["scope"]["subject"]["items"] = []
        path.write_text(json.dumps(record), encoding="utf-8")
        # Even a valid file digest cannot substitute for semantic result binding.
        manifest["files"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif defect == "item_pin":
        manifest["item_ref"] = "another item"
    elif defect in ("workflow", "workflow_uses"):
        filename = "original.workflow.json"
        path = output / filename
        workflow = read_json(path)
        if defect == "workflow":
            workflow.update(items=[], uses=[], usage_tree={})
        else:
            workflow["uses"] = []
        path.write_text(json.dumps(workflow), encoding="utf-8")
        manifest["files"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif defect == "format":
        manifest["format"] = "unknown@99"
    else:
        manifest["files"]["../outside.json"] = manifest["files"].pop(filename)
        manifest["packets"]["full"]["attribution_file"] = "../outside.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    # Remove old derived exports: rejection must not create replacement reports.
    report = output / "original.full.references.csl.json"
    report.unlink()
    result = invoke("read", output, reader_guards=True)
    assert result.returncode != 0 and "FAIL:" in result.stderr, (
        result.stdout + result.stderr
    )
    assert not report.exists()


def test_producer_and_reuser_refuse_to_overwrite_existing_runs(bundle):
    before = (bundle / "original.manifest.json").read_bytes()
    for action, expected in (("produce", "empty"), ("reuse", "already exists")):
        result = invoke(action, bundle)
        assert result.returncode == 2 and expected in result.stderr
    assert (bundle / "original.manifest.json").read_bytes() == before
