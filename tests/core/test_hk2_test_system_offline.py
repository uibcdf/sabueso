"""HK2's public native declarations survive the current saved-card journey."""

import json
import subprocess
import sys

import pytest
import pyunitwizard as puw

import sabueso
from sabueso.core.card import Card
from sabueso.tools.db import _http
from tools.build_hk2_test_system import FIXTURE, ROOT, build


@pytest.fixture(scope="module")
def hk2(tmp_path_factory):
    output = tmp_path_factory.mktemp("hk2_current")
    card, receipt = build(output)
    return card, receipt, output


def test_native_subject_sequence_and_quantity_are_supported(hk2):
    card, receipt, _ = hk2
    original = json.loads(FIXTURE.read_text())
    assert card.id == "sabueso:protein:uniprot:P52789"
    assert receipt["resolution_status"] == "resolved"
    assert card.get("names.canonical_name")["value"] == "Hexokinase-2"
    assert len(card.get("sequence.primary")["value"]) == 917
    assert puw.get_value(
        card.quantity("sequence.molecular_weight"), to_unit="dalton"
    ) == pytest.approx(original["sequence"]["molWeight"])
    for field in ["sequence.primary", "sequence.molecular_weight"]:
        node = card.get(field)
        for support in node["source_assertion_ids"]:
            assertion = card.source_assertion_store.get(support)
            assert assertion["subject_ref"] == "uniprot:P52789"
            assert assertion["source"]["version"] == str(
                original["entryAudit"]["entryVersion"]
            )
            assert assertion["retrieved_at"] == "2026-09-23"


def test_two_atp_site_groups_keep_their_positions_and_exact_support(hk2):
    card, _, _ = hk2
    sites = card.ligand_sites()
    groups = {}
    for site in sites["annotated_sites"]:
        if (site.get("ligand") or {}).get("name") != "ATP":
            continue
        groups.setdefault(site["ligand"]["label"], set()).update(site["positions"])
        assertion = card.source_assertion_store.get(site["source_assertion_id"])
        assert assertion["asserted_value"]["ligand"] == site["ligand"]
        assert assertion["subject_ref"] == "uniprot:P52789"
    assert set(groups) == {"1", "2"}
    assert max(groups["1"]) < min(groups["2"])
    assert sites["items"] == []  # No structural ligand-contact query was requested.
    assert card.relationships("has_ligand_site") == []


def test_unqueried_scopes_stay_unqueried_after_exact_storage(hk2, tmp_path):
    card, _, _ = hk2
    store = sabueso.KnowledgeStore(tmp_path / "hk2.db")
    pin = store.save(card)
    restored = store.load(pin)
    assert restored.to_dict() == card.to_dict()
    assert restored.pinned_ref() == card.pinned_ref()
    state = {
        (r["area"], r["source"]): r["state"] for r in restored.knowledge_state()["rows"]
    }
    assert (
        state[("relationships.functionally_associated_with", "STRING")] == "not_queried"
    )
    assert all(
        a["source"]["name"] == "UniProt"
        for a in restored.source_assertion_store.to_list()
    )


def test_current_hk2_report_regenerates_without_acquisition(hk2, tmp_path, monkeypatch):
    card, receipt, output = hk2
    stored = Card.from_json(output / receipt["card_file"])
    assert stored.to_dict() == card.to_dict()

    def forbidden(*args, **kwargs):
        pytest.fail("Offline HK2 rebuilding or rendering contacted a source")

    monkeypatch.setattr(_http, "urlopen", forbidden)
    rebuilt, new_receipt = build(tmp_path / "rebuilt")
    assert rebuilt.to_dict() == card.to_dict()
    assert new_receipt == receipt
    monkeypatch.setattr(sabueso, "resolve", forbidden)
    regenerated = stored.to_notebook(
        tmp_path / "regenerated.ipynb", include_card_snapshot=True
    )
    report = json.loads(regenerated.read_text())
    assert report["metadata"]["sabueso"]["card_ref"] == card.pinned_ref()
    assert report["metadata"]["sabueso"]["missing_source_assertion_ids"] == []
    assert (
        Card.from_json(regenerated.with_suffix(".card.json")).to_dict()
        == card.to_dict()
    )


def test_cli_relative_output_is_resolved_from_the_callers_directory(tmp_path):
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/build_hk2_test_system.py"),
            "--output",
            "nested/current_HK2",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    output = tmp_path / "nested/current_HK2"
    assert {p.name for p in output.iterdir()} == {
        "HK2_human.card.json",
        "HK2_human.ipynb",
        "receipt.json",
    }
    receipt = json.loads((output / "receipt.json").read_text())
    card = Card.from_json(output / receipt["card_file"])
    report = json.loads((output / receipt["notebook_file"]).read_text())
    assert receipt["card_ref"] == card.pinned_ref()
    assert report["metadata"]["sabueso"]["card_ref"] == card.pinned_ref()
