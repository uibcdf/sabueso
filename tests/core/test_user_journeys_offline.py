"""Independent protein-comparison readers retain original science and runtime use."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path("examples/user_journeys/protein_comparison.py").resolve()
DATA = Path("temp_data").resolve()


def invoke(action, output):
    command = [sys.executable, str(SCRIPT)]
    if action == "read":
        command = [
            sys.executable,
            "-c",
            """
import runpy, sys
import ackredit, sabueso
def forbidden(*args, **kwargs):
    raise RuntimeError('An independent reader cannot acquire or generate credit')
ackredit.register_item = ackredit.track_item = forbidden
sabueso.resolve = sabueso.ligand_deck = sabueso.compose_packet = forbidden
sabueso.__version__ = '999.reader'
script = sys.argv.pop(1)
runpy.run_path(script, run_name='__main__')
""",
            str(SCRIPT),
        ]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [*command, action, "--output", str(output),
         "--fixtures", str(DATA if action != "read" else output / "no-fixtures")],
        cwd=output.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )  # fmt: skip


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    output = tmp_path_factory.mktemp("user-comparison") / "bundle"
    for action in ("produce", "read", "reacquire", "read"):
        result = invoke(action, output)
        assert result.returncode == 0, result.stdout + result.stderr
    return output


def test_independent_reader_preserves_original_comparison_support_units_and_citations(
    bundle,
):
    original = load(bundle / "original.manifest.json")
    later = load(bundle / "later.manifest.json")
    for role in ("subject", "comparator"):
        assert original["cards"][role] != later["cards"][role]
        assert original["decks"][role] != later["decks"][role]
    for detail in ("full", "index"):
        assert original["packets"][detail]["ref"] != later["packets"][detail]["ref"]
        record = load(bundle / original["packets"][detail]["attribution_file"])
        assert record["producer"]["version"] != "999.reader"
    report = load(bundle / "original.report.json")
    reader = load(bundle / "original.reader.json")
    assert reader["observed_acquisitions"] == 0
    assert reader["cards"] == original["cards"]
    assert reader["items"] == original["items"]
    assert reader["original_report"] == report
    assert len(report["resolutions"]["comparator"]["alternatives"]) > 0
    assert len(report["ligand_comparison"]["shared"]) == 14
    assert report["knowledge_comparison"]["fields"][
        "features_positional.active_site"
    ] == {
        "status": "not_compared",
        "reason": "no residue mapping",
    }
    mass = report["proteins"]["subject"]["mass"]
    assert (mass["value"], mass["unit"]) == (27329, "dalton")
    assert all(row["found"] for row in report["proteins"]["subject"]["support"])
    measurements = report["proteins"]["subject"]["bioactivities"]["items"][0][
        "measurements"
    ]
    assert measurements[0]["normalized"]["unit"] == "nanomolar"
    explanation = report["proteins"]["subject"]["example_measurement_explanation"]
    assert explanation["rule"]["rule"] == "measurement_group_explanation@1"
    assert explanation["group"]["id"] == measurements[0]["group"]
    assert (
        report["proteins"]["subject"]["example_shared_ligand_explanation"]["rule"][
            "rule"
        ]
        == "ligand_deck_explanation@2"
    )
    observations = load(bundle / "original.observations.json")
    (partial,) = [
        record
        for record in observations["acquisitions"]
        if record["source"] == "RCSB PDB" and record["outcome"] == "partial"
    ]
    assert partial["network_attempts"] == 0
    assert any(
        row["source"] == "STRING" and row["state"] == "not_queried"
        for row in report["proteins"]["subject"]["knowledge_state"]["rows"]
    )
    citations = load(bundle / "original.references.csl.json")
    assert any(row.get("DOI") == "10.1093/nar/gkae1010" for row in citations)
    assert (bundle / "original.references.bib").read_text(encoding="utf-8")


@pytest.mark.parametrize("defect", ["missing", "changed", "role", "report", "item"])
def test_reader_refuses_missing_changed_or_misbound_support(bundle, tmp_path, defect):
    output = tmp_path / "copy"
    shutil.copytree(bundle, output)
    path = output / "original.manifest.json"
    manifest = load(path)
    if defect in ("missing", "changed"):
        target = output / "original.traces.json"
        if defect == "missing":
            target.unlink()
        else:
            target.write_text("{}", encoding="utf-8")
    elif defect == "item":
        manifest["items"]["subject"] = manifest["items"]["comparator"]
    else:
        filename = (
            "original.full.attribution.json"
            if defect == "role"
            else "original.report.json"
        )
        target = output / filename
        record = load(target)
        if defect == "role":
            record["scope"]["comparator"]["card_ref"] = manifest["cards"]["subject"]
        else:
            record["cards"]["comparator"] = manifest["cards"]["subject"]
        target.write_text(json.dumps(record), encoding="utf-8")
        # A fresh checksum does not establish the result's scientific binding.
        manifest["files"][filename] = hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest), encoding="utf-8")
    references = output / "original.references.csl.json"
    references.unlink()
    result = invoke("read", output)
    assert result.returncode == 2 and "FAIL:" in result.stderr, (
        result.stdout + result.stderr
    )
    assert not references.exists()


def test_completed_stages_cannot_be_overwritten(bundle):
    before = (bundle / "original.manifest.json").read_bytes()
    for action in ("produce", "reacquire"):
        result = invoke(action, bundle)
        assert result.returncode == 2
    assert (bundle / "original.manifest.json").read_bytes() == before
