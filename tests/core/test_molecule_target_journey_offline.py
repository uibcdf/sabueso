"""Saved molecular/assay/clinical statements stay scoped, supported and attributed."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path("examples/user_journeys/molecule_target.py").resolve()
DATA = Path("temp_data").resolve()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def invoke(action, output):
    command = [sys.executable, str(SCRIPT)]
    if action == "read":
        command = [sys.executable, "-c", """
import runpy, sys
from pathlib import Path
import ackredit, sabueso
from sabueso.core.card import Card
def forbidden(*args, **kwargs):
    raise RuntimeError('A historical reader cannot acquire, derive or generate credit')
ackredit.register_item = ackredit.track_item = forbidden
sabueso.resolve = sabueso.ligand_deck = sabueso.compose_packet = forbidden
Card.explain_ligand = Card.explain_bioactivity = Card.explain_measurement = forbidden
Card.ligands = Card.bioactivities = Card.clinical = forbidden
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


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    output = tmp_path_factory.mktemp("molecule-target") / "bundle"
    for action in ("produce", "read", "reacquire", "read"):
        result = invoke(action, output)
        assert result.returncode == 0, result.stdout + result.stderr
    return output


def test_original_target_molecule_assays_clinical_scope_and_citations_survive(bundle):
    original = load(bundle / "original.manifest.json")
    later = load(bundle / "later.manifest.json")
    assert all(original["cards"][r] != later["cards"][r] for r in original["cards"])
    assert original["deck"] != later["deck"]
    assert original["packet"] != later["packet"]
    report = load(bundle / "original.report.json")
    reader = load(bundle / "original.reader.json")
    assert reader["original_report"] == report
    assert reader["cards"] == original["cards"] and reader["observed_acquisitions"] == 0
    assert (
        report["scope"]["other_targets"] == report["scope"]["trials"] == "not_queried"
    )
    bts = report["molecules"]["bts"]
    activity = bts["activity"]["item"]
    assert activity["class"] == "weak"
    measurement = activity["measurements"][0]
    assert (measurement["type"], measurement["relation"]) == ("IC50", "=")
    assert measurement["normalized"] == {"value": 33000, "unit": "nanomolar"}
    assay = bts["activity"]["records"][0]["relationship"]["qualifiers"]["assay"]
    assert assay["relationship_type"] == "D" and assay["confidence_score"] == 9
    assert "glyceraldehyde 3-phosphate" in assay["description"]
    assert bts["mass"]["unit"] == "dalton"
    assert bts["crossing"]["rule"]["rule"] == "ligand_deck_explanation@2"
    assert bts["crossing"]["items"][0]["item"]["records"] == [
        "chembl:CHEMBL1161789",
        "pdb.ligand:BTS",
    ]
    assert bts["crossing"]["items"][0]["item"]["structures"] == ["pdb:1SUX"]
    assert all(
        sa["version"] == "ChEMBL_37"
        for sa in bts["activity"]["records"][0]["source_assertions"]
    )
    benz = report["molecules"]["benznidazole"]
    measured, unstated = benz["activity"]["item"]["measurements"]
    assert measured["type"] == "Inhibition" and measured["class"] == "inactive"
    assert measured["normalized"] == {"value": 18, "unit": "percent"}
    assert measured["test_concentration"] == {"value": 400, "unit": "micromolar"}
    assert unstated["value"] is None and unstated["class"] == "not_determined"
    clinical = benz["clinical"]
    assert clinical["max_phase"] == 4.0 and len(clinical["indications"]) == 4
    assert not clinical["trials"] and len(clinical["not_fetched"]) == 16
    assert {i["disease"] for i in clinical["indications"]} >= {
        "efo:EFO:0008559",
        "mondo:MONDO:0001444",
    }
    for molecule in report["molecules"].values():
        assert all(
            m["rule"]["rule"] == "measurement_group_explanation@1"
            for m in molecule["measurements"]
        )
    assert len(report["crossing"]["items"]) == 2 and report["crossing"]["unmatched"]
    observations = load(bundle / "original.observations.json")
    assert all(r["network_attempts"] == 0 for r in observations["acquisitions"])
    assert not any(
        r["source"] in {"BindingDB", "ClinicalTrials.gov", "DrugBank", "PubChem"}
        for r in observations["acquisitions"]
    )
    assert any(
        r["source"] == "UniChem" and r["outcome"] == "unavailable"
        for r in observations["acquisitions"]
    )
    record = load(bundle / "original.packet-attribution.json")
    assert record["producer"]["version"] != "999.reader"
    citations = load(bundle / "original.references.csl.json")
    assert any(row.get("DOI") == "10.1016/j.bmc.2021.116577" for row in citations)
    assert (bundle / "original.references.bib").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "defect", ["missing", "trace", "molecule", "statement", "packet", "item"]
)
def test_reader_refuses_misbound_originals_before_export(bundle, tmp_path, defect):
    output = tmp_path / "copy"
    shutil.copytree(bundle, output)
    manifest_path = output / "original.manifest.json"
    manifest = load(manifest_path)
    if defect == "missing":
        (output / "original.workflow.json").unlink()
    elif defect == "item":
        manifest["assertions"]["bts"] = manifest["assertions"]["benznidazole"]
    else:
        filename = {
            "trace": "original.traces.json",
            "packet": "original.packet-attribution.json",
        }.get(defect, "original.report.json")
        path = output / filename
        value = load(path)
        if defect == "trace":
            value["bts"]["card_ref"] = manifest["cards"]["benznidazole"]
        elif defect == "packet":
            value["scope"]["subject"]["card_ref"] = manifest["cards"]["bts"]
        elif defect == "molecule":
            value["molecules"]["bts"]["crossing"]["items"][0]["molecule_card_ref"] = (
                manifest["cards"]["benznidazole"]
            )
        else:
            value["molecules"]["bts"]["activity"]["records"][0]["source_assertions"][0][
                "asserted_value"
            ] = {"different": "assay context"}
        path.write_text(json.dumps(value), encoding="utf-8")
        # Updating a checksum does not repair mismatched scientific support.
        manifest["files"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
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
        assert invoke(action, bundle).returncode == 2
    assert (bundle / "original.manifest.json").read_bytes() == before
