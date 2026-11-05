"""Public structural journey, explicit modeling scope and inert original reading."""

import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "temp_data"
SCRIPT = ROOT / "examples/user_journeys/structural_context.py"
INPUTS = DATA / "rcsb_structural_context"
spec = importlib.util.spec_from_file_location("public_structural_context", SCRIPT)
journey = importlib.util.module_from_spec(spec)
spec.loader.exec_module(journey)


def forbidden(*args, **kwargs):
    raise AssertionError("No source request or unrequested calculation")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr("socket.socket.connect", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)


@pytest.fixture(scope="module")
def card():
    result, _ = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient(DATA), rcsb_client=FixtureRCSBClient(INPUTS)
        ),
        structures=["1TCD"],
    )
    return result


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    output = tmp_path_factory.mktemp("public-structural-context") / "bundle"
    journey.produce(DATA, output)
    return output


@pytest.fixture(scope="module")
def provider():
    return pytest.importorskip(
        "molsysmt",
        reason="Optional modeling-consumer receiving requires MolSysMT; knowledge reading does not.",
    )


@pytest.fixture(scope="module")
def container(provider):
    return provider.convert(
        str(INPUTS / "coordinates/1tcd.bcif.gz"),
        to_form="mmcif.PdbxContainers.DataContainer",
    )


def test_focused_structure_labels_inventory_wide_unknowns(card):
    before = card.to_dict()
    view = (
        card.explore()
        .view("structures")
        .filter("structure_ref", equals="pdb:1TCD")
        .items()[0]
        .open()
    )
    row = next(
        r
        for r in card.structures(region=[96])["items"]
        if r["structure_ref"] == "pdb:1TCD"
    )
    assert row["coordinate_scope"]["status"] == "comparable"
    for rendered in [str(view), view._repr_html_()]:
        assert "Full captured inventory: 6 declarations" in rendered
        assert "their regional completeness" in rendered
    assert card.to_dict() == before


def test_original_public_wire_query_revision_and_file_hashes():
    capture = journey._load(INPUTS / "capture.json")
    for name, record in capture["files"].items():
        path = INPUTS / name
        assert path.stat().st_size == record["bytes"]
        assert journey._hash(path) == record["sha256"]
    wire = journey._load(INPUTS / "wire/1TCD.graphql.json")
    request = journey._load(INPUTS / "wire/1TCD.request.json")
    assert not wire.get("errors") and request["variables"] == {"id": "1TCD"}
    assert (
        hashlib.sha256(request["query"].encode()).hexdigest() == capture["query_sha256"]
    )
    assert wire["data"]["entry"] == journey._load(INPUTS / "rcsb/1TCD.json")
    revision = wire["data"]["entry"]["rcsb_accession_info"]
    assert (
        revision["major_revision"],
        revision["minor_revision"],
        revision["revision_date"],
    ) == (1, 4, "2024-05-22T00:00:00Z")
    assert capture["acquisition_scope"]["new_network_attempts"] == 2
    assert capture["acquisition_scope"]["complete_responses_retained"] == 1


def test_original_knowledge_keeps_region_axes_components_and_unknowns(bundle):
    views = journey.read(bundle)
    native = views["assembly"].native_payload
    assert native["physical_membership"] == "not_computed"
    assert native["sources"][0]["entry_revision"]["minor_revision"] == 4
    bindings = native["sources"][0]["assemblies"][0]["generators"][0][
        "component_bindings"
    ]
    assert [(row["asym_id"], row["state"]) for row in bindings] == [
        ("A", "resolved"),
        ("B", "resolved"),
        ("C", "unresolved"),
        ("D", "unresolved"),
    ]
    assert views["region"].request["options"]["region"] == [96]
    assert views["agent"].result_ref == views["assembly"].result_ref
    assert views["components"].filter("role", equals="component").items()


def _fresh_read(bundle):
    code = r"""
import runpy, socket, sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a, **k):
    raise AssertionError("Original reading cannot fetch, rebuild or calculate")
socket.socket.connect = forbidden
socket.create_connection = forbidden
Card.__init__ = forbidden
Card.from_dict = forbidden
def audit(event, args):
    if event == "open" and isinstance(args[0], str) and "temp_data" in args[0].replace(chr(92), "/").split("/"):
        forbidden()
sys.addaudithook(audit)
script = sys.argv.pop(1)
runpy.run_path(script, run_name="__main__")
assert "molsysmt" not in sys.modules
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            code,
            str(SCRIPT),
            "read",
            "--output",
            str(bundle),
        ],
        cwd=bundle.parent,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_fresh_reader_needs_no_card_builder_fixtures_or_modeling(bundle):
    _fresh_read(bundle)


def test_example_refuses_changed_inputs_and_foreign_receipt_paths(bundle, tmp_path):
    changed = tmp_path / "changed"
    shutil.copytree(bundle, changed)
    (changed / "card.json").write_text("{}")
    with pytest.raises(ValueError, match="Changed original"):
        journey.read(changed)
    manifest = journey._load(bundle / "manifest.json")
    manifest["files"]["../../foreign"] = manifest["files"].pop("card.json")
    journey._write(changed / "manifest.json", manifest)
    with pytest.raises(ValueError, match="Incomplete original"):
        journey.read(changed)


def test_public_coordinate_correspondence_retains_distinct_source_roles(
    card, container
):
    original = card.to_dict()
    native = card.assembly_generation(
        structure_ref="pdb:1TCD", generation_rule="rcsb_assembly_generation@5"
    )
    admitted = journey._correspondence(card, container, native)
    assert admitted["criteria"] == journey.CRITERIA
    assert admitted["entry_revision"] == {
        "major_revision": 1,
        "minor_revision": 4,
        "revision_date": "2024-05-22",
    }
    rows = admitted["component_correspondence"]
    assert [r["coordinate_entity_type"] for r in rows] == [
        "polymer",
        "polymer",
        "water",
        "water",
    ]
    assert [r["card_component_state"] for r in rows] == [
        "resolved",
        "resolved",
        "unresolved",
        "unresolved",
    ]
    assert admitted["coordinate_scope"]["structure_reference_revision"] == "not_stated"
    assert card.to_dict() == original


@pytest.mark.parametrize(
    "category,attribute,value,row,reason",
    [
        ("entry", "id", "1BRS", 0, "entry identity"),
        ("pdbx_audit_revision_history", "minor_revision", 5, 4, "revisions differ"),
        ("pdbx_struct_assembly_gen", "oper_expression", "1,2", 0, "ordered generator"),
        ("pdbx_struct_oper_list", "vector[1]", 10, 0, "numeric transform"),
        ("struct_asym", "id", "Z", 0, "component identities"),
        ("struct_ref", "pdbx_db_accession", "P60174", 0, "database reference"),
        ("struct_ref_seq", "db_align_beg", 1, 0, "numbering declarations"),
        (
            "entity_poly",
            "pdbx_seq_one_letter_code_can",
            "A" * 249,
            0,
            "sequence declarations",
        ),
        ("atom_site", "label_comp_id", "SYNTHETIC", 0, "position/type pointers"),
        ("atom_site", "pdbx_PDB_model_num", 2, 0, "Multiple coordinate models"),
        ("atom_site", "label_alt_id", "A", 0, "Alternate locations"),
        ("atom_site", "label_alt_id", "?", 0, "Alternate locations"),
        ("atom_site", "auth_asym_id", "Z", 0, "author numbering"),
        ("atom_site", "auth_seq_id", 999, 0, "author numbering"),
        ("atom_site", "id", 2, 0, "Ambiguous coordinate"),
    ],
)
def test_synthetic_input_changes_never_authorize_geometry(
    card, container, category, attribute, value, row, reason
):
    changed = deepcopy(container)
    changed.getObj(category).setValue(value, attribute, row)
    native = card.assembly_generation(
        structure_ref="pdb:1TCD", generation_rule="rcsb_assembly_generation@5"
    )
    with pytest.raises(ValueError, match=reason):
        journey._correspondence(card, changed, native)


def test_historical_revision_gap_stays_unknown(container):
    legacy, _ = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient(DATA), rcsb_client=FixtureRCSBClient(DATA)
        ),
        structures=["1TCD"],
    )
    before = legacy.to_dict()
    native = legacy.assembly_generation(
        structure_ref="pdb:1TCD", generation_rule="rcsb_assembly_generation@5"
    )
    with pytest.raises(ValueError, match="revision is unavailable"):
        journey._correspondence(legacy, container, native)
    assert legacy.to_dict() == before


@pytest.mark.parametrize("same_size", [False, True])
def test_foreign_coordinate_bytes_fail_before_optional_engine(
    bundle, tmp_path, monkeypatch, same_size
):
    import builtins

    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "molsysmt":
            raise AssertionError("Foreign input reached the optional engine")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    path = tmp_path / "foreign.bcif.gz"
    size = (
        journey._load(bundle / "manifest.json")["coordinate_input"]["bytes"]
        if same_size
        else 1
    )
    path.write_bytes(b"x" * size)
    with pytest.raises(ValueError, match="retained original coordinate input"):
        journey.model(bundle, path)


@pytest.fixture(scope="module")
def model_bundle(bundle, provider, tmp_path_factory):
    output = tmp_path_factory.mktemp("public-calculation") / "bundle"
    shutil.copytree(bundle, output)
    journey.model(output, INPUTS / "coordinates/1tcd.bcif.gz")
    return output


@pytest.mark.parametrize("change", ["format", "threshold", "criteria"])
def test_coherently_rehashed_calculation_scope_cannot_change_labels(
    model_bundle, tmp_path, change
):
    output = tmp_path / "changed"
    shutil.copytree(model_bundle, output)
    report = journey._load(output / "modeling.json")
    if change == "format":
        report["format"] = "unknown_calculation@99"
    elif change == "threshold":
        report["contact_criterion"]["threshold"]["value"] = 0.4
    else:
        report["correspondence"]["criteria"] = "unknown_correspondence@99"
    journey._write(output / "modeling.json", report)
    manifest = journey._load(output / "manifest.json")
    manifest["modeling"]["modeling.json"] = journey._hash(output / "modeling.json")
    journey._write(output / "manifest.json", manifest)
    with pytest.raises(ValueError, match="calculation (format|criterion)"):
        journey.read(output)


def test_explicit_modeling_calculation_keeps_original_knowledge_and_units(
    bundle, model_bundle
):
    output = model_bundle
    original_files = journey._load(bundle / "manifest.json")["files"]
    report = journey._load(output / "modeling.json")
    assert report["generated_atom_count"] == 3983
    assert report["contact_shape"] == [1, 248, 249] and report["contact_count"] == 276
    assert report["contact_criterion"]["threshold"] == {"value": 1.0, "unit": "nm"}
    assert report["new_source_assertions"] == 0
    pairs = journey._load(output / "calculated-pairs.json")
    assert len(pairs) == 276 and len({tuple(pair) for pair in pairs}) == 276
    correspondence = journey._load(output / "atom-correspondence.json")
    assert {
        r["source_asym_id"] for r in correspondence if r["reference_position"] == 96
    } == {"A", "B"}
    assert all(
        journey._hash(output / name) == digest
        for name, digest in original_files.items()
    )
    journey.read(output)
    _fresh_read(output)
    with pytest.raises(ValueError, match="overwritten"):
        journey.model(output, INPUTS / "coordinates/1tcd.bcif.gz")
