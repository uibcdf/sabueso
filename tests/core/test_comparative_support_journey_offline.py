"""Independent comparative readers preserve original explanations and exact pins."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path("examples/user_journeys/comparative_support.py").resolve()
DATA = Path("temp_data").resolve()


def invoke(action, output):
    command = [sys.executable, str(SCRIPT)]
    if action == "read":
        command = [sys.executable, "-c", """
import runpy, sys
from pathlib import Path
import ackredit, sabueso
from sabueso.core.card import Card
def forbidden(*args, **kwargs):
    raise RuntimeError('Independent reader cannot acquire, derive or generate credit')
ackredit.register_item = ackredit.track_item = forbidden
sabueso.resolve = forbidden
for name in ('sequence_differences', 'variant_tissue_usage', 'isoform_tissue_usage',
             'explain_sequence_differences', 'explain_variant_tissue_usage',
             'explain_isoform_tissue_usage', 'explain', 'knowledge_state'):
    setattr(Card, name, forbidden)
sabueso.__version__ = '999.reader'
script = sys.argv.pop(1)
sys.path.insert(0, str(Path(script).parent))
runpy.run_path(script, run_name='__main__')
""", str(SCRIPT)]  # fmt: skip
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [*command, action, "--output", str(output), "--fixtures",
         str(DATA if action != "read" else output / "no-fixtures")],
        cwd=output.parent, env=env, capture_output=True, text=True,
        timeout=120, check=False,
    )  # fmt: skip


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    output = tmp_path_factory.mktemp("comparative-support") / "bundle"
    for action in ("produce", "read", "reacquire", "read"):
        result = invoke(action, output)
        assert result.returncode == 0, result.stdout + result.stderr
    return output


def test_reader_retains_original_rules_source_versions_and_history_without_recomputation(
    bundle,
):
    original = load(bundle / "original.manifest.json")
    later = load(bundle / "later.manifest.json")
    assert all(original["cards"][r] != later["cards"][r] for r in original["cards"])
    for stage in ("original", "later"):
        report = load(bundle / f"{stage}.report.json")
        reader = load(bundle / f"{stage}.reader.json")
        assert (
            reader["original_report"] == report and reader["observed_acquisitions"] == 0
        )
        assert report["sequence"]["view"]["differences"]
        assert len(report["variants"]["items"]) == 15
        assert len(report["isoforms"]["items"]) == 3
        assert report["execution_observation"]["status"] == "not_observed"
        for key in ("sequence", "variants", "isoforms"):
            assert report[key]["rule"]["sabueso_version"] != "999.reader"


@pytest.mark.parametrize(
    "defect",
    ["digest", "role", "field", "assertion", "time", "locator", "rule", "parameters"],
)
def test_reader_refuses_changed_or_misbound_original_inputs_even_with_new_report_digest(
    bundle, tmp_path, defect
):
    output = tmp_path / "copy"
    shutil.copytree(bundle, output)
    filename = "original.report.json"
    report_path = output / filename
    report = load(report_path)
    manifest_path = output / "original.manifest.json"
    manifest = load(manifest_path)
    if defect == "role":
        report["sequence"]["card_refs"][0] = manifest["cards"]["human"]
    elif defect == "field":
        report["sequence"]["fields"][0]["node"]["value"] = "forged"
    elif defect in ("assertion", "time"):
        row = report["sequence"]["fields"][0]["source_assertions"][0]
        row["asserted_value" if defect == "assertion" else "retrieved_at"] = "forged"
    elif defect == "locator":
        report["variants"]["items"][0]["variant_input"]["locator"]["index"] = 999
    elif defect == "rule":
        report["isoforms"]["view"]["rule"]["rule"] = "isoform_exon_usage@999"
    elif defect == "parameters":
        report["variants"]["rule"]["parameters"]["threshold"] = 0.9
    else:
        report["cards"]["human"] = "forged"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    if defect != "digest":
        manifest["files"][filename] = hashlib.sha256(
            report_path.read_bytes()
        ).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (output / "original.reader.json").unlink()
    result = invoke("read", output)
    assert result.returncode == 2 and "FAIL:" in result.stderr, (
        result.stdout + result.stderr
    )
    assert not (output / "original.reader.json").exists()


def test_completed_producer_stages_cannot_be_overwritten(bundle):
    original = (bundle / "original.manifest.json").read_bytes()
    for action in ("produce", "reacquire"):
        result = invoke(action, bundle)
        assert result.returncode == 2
    assert (bundle / "original.manifest.json").read_bytes() == original
