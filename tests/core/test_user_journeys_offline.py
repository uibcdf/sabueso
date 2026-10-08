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
from sabueso.core.card import Card
def forbidden(*args, **kwargs):
    raise RuntimeError('An independent reader cannot acquire or generate credit')
ackredit.register_item = ackredit.track_item = forbidden
sabueso.resolve = sabueso.ligand_deck = sabueso.compose_packet = forbidden
for name in ('get_residues', 'get_residue', 'residue_composition', 'residue_knowledge'):
    setattr(Card, name, forbidden)
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


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "changed",
        "role",
        "report",
        "item",
        "residue_role",
        "residue_item",
        "residue_position",
        "residue_literal",
        "residue_selection",
    ],
)
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
    elif defect.startswith("residue_"):
        filename = "original.report.json"
        target = output / filename
        report = load(target)
        context = report["proteins"]["subject"]["residue_context"]
        if defect == "residue_role":
            context["card_ref"] = manifest["cards"]["comparator"]
        elif defect == "residue_item":
            context["support_refs"][0] = load(output / "original.report.json")[
                "proteins"
            ]["comparator"]["residue_context"]["support_refs"][0]
            manifest["residue_items"]["subject"] = context["support_refs"]
        elif defect == "residue_position":
            context["residues"][0]["amino_acid"] = "X"
        elif defect == "residue_literal":
            context["residues"][0]["annotations"][0]["annotation"]["description"] = (
                "forged statement"
            )
        else:
            context["selection"]["positions"] = [1]
        target.write_text(json.dumps(report), encoding="utf-8")
        manifest["files"][filename] = hashlib.sha256(target.read_bytes()).hexdigest()
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


def test_source_residue_context_retains_independent_axes_original_support_and_rules(
    bundle,
):
    manifest = load(bundle / "original.manifest.json")
    assert manifest["format"] == "sabueso.protein_comparison_example@2"
    report = load(bundle / "original.report.json")
    for role, positions in (("subject", [96, 168]), ("comparator", [96, 166])):
        context = report["proteins"][role]["residue_context"]
        assert context["selection"]["positions"] == positions
        assert context["selection"]["rule"] == "source_active_site_selection@1"
        assert context["composition"]["rule"] == "residue_set_composition@1"
        assert context["composition"]["total"] == 2
        assert context["composition"]["counts"] == {"E": 1, "H": 1}
        assert context["comparison"]["status"] == "not_compared"
        assert context["execution_observation"]["status"] == "not_observed"
        assert context["support_refs"] == manifest["residue_items"][role]
        assert all(
            pin.startswith(manifest["cards"][role] + "#")
            for pin in context["support_refs"]
        )
    assert load(bundle / "original.reader.json")["original_report"] == report
    assert (
        load(bundle / "later.report.json")["proteins"]["subject"]["residue_context"][
            "card_ref"
        ]
        != report["proteins"]["subject"]["residue_context"]["card_ref"]
    )


def test_legacy_manifest_does_not_require_or_recompute_new_residue_context(
    bundle, tmp_path
):
    output = tmp_path / "legacy"
    shutil.copytree(bundle, output)
    (output / "later.manifest.json").unlink()
    manifest_path = output / "original.manifest.json"
    manifest = load(manifest_path)
    manifest["format"] = "sabueso.protein_comparison_example@1"
    manifest.pop("residue_items")
    report_path = output / "original.report.json"
    report = load(report_path)
    for row in report["proteins"].values():
        row.pop("residue_context")
    report_path.write_text(json.dumps(report), encoding="utf-8")
    manifest["files"][report_path.name] = hashlib.sha256(
        report_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = invoke("read", output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert load(output / "original.reader.json")["original_report"] == report
