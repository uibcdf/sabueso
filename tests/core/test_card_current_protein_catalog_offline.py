"""Current complete protein menus preserve earlier catalog and scientific meanings."""

import json
import socket

import pytest
from test_card_molecule_activity_exploration_offline import pair as pair
from test_card_molecule_activity_exploration_offline import (
    public_originals as public_originals,
)
from test_card_sequence_changes_offline import synthetic

import sabueso
from sabueso.core import card_exploration_storage as storage
from sabueso.core.card import Card
from sabueso.core.errors import StorageError


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("A captured catalog must not acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.mark.parametrize("opening", ["overview", "topics"])
def test_current_protein_menu_saves_without_executing_science(
    opening, tmp_path, monkeypatch
):
    root = getattr(synthetic().explore(), opening)()
    expected = root.rows()
    monkeypatch.setattr(
        Card, "__init__", lambda *a, **k: pytest.fail("Reconstructed a Card")
    )
    path = tmp_path / "menu.json"
    root.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.explorer._session["format"] == "sabueso.card_exploration@35"
    assert saved.rows() == expected
    assert saved.native_payload == root.native_payload
    assert {
        "variants",
        "sequence_changes",
        "comparative_context",
        "associations",
    } <= set(saved.native_payload)
    assert saved.validation["verified_scientific_adapters"] == []
    assert saved.explorer.view("sequence_changes").outcome["status"] == "not_saved"


def test_shared_current_menu_has_an_original_catalog_witness(tmp_path):
    from sabueso.core.card_exploration_shared_values_v12 import pack

    root = synthetic().explore().topics()
    packet = storage._seal(
        pack(storage._prepare(root), threshold=0, min_saving=-(1024**2))
    )
    assert packet["format"] == "sabueso.card_exploration@36"
    path = tmp_path / "shared.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    saved = sabueso.read_exploration(path)
    assert saved.rows() == root.rows()
    again = tmp_path / "again.json.gz"
    saved.save(again, compression="gzip")
    assert sabueso.read_exploration(again).rows() == root.rows()


@pytest.mark.parametrize("defect", ["label", "selection", "context"])
def test_resealed_current_menu_cannot_change_original_presentation_or_capture(
    defect, tmp_path
):
    wire = storage._prepare(synthetic().explore().topics())
    record = wire["views"][wire["root_navigation_ref"]]
    if defect == "label":
        next(iter(record["state"]["items"].values()))["label"] = "Foreign label"
    elif defect == "selection":
        record["selected"] = []
    else:
        record["state"]["context"]["card_ref"] = "uniprot:foreign"
    storage._seal(wire)
    path = tmp_path / "resealed.json"
    path.write_text(json.dumps(wire), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_molecule_target_keeps_current_menu_and_unexecuted_routes(pair, tmp_path):
    molecule, target = pair
    root = molecule.explore(related_cards=[target]).answer("measured_targets")
    endpoint = next(
        link
        for link in root.items()[0].related().items()
        if link._entry.value["role"] == "target_card"
    ).open()
    path = tmp_path / "target.json.gz"
    endpoint.save(path, compression="gzip")
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == endpoint.native_payload
    assert saved.rows() == endpoint.rows()
    assert saved.back().view_ref == endpoint.back().view_ref
    assert saved.explorer.context["card_ref"] == target.pinned_ref()
    assert saved.context["molecule_card_ref"] == molecule.pinned_ref()
    assert saved.explorer.view("variants").outcome["status"] == "not_saved"


def test_source_owned_catalog_lookalike_is_only_literal_content(tmp_path):
    from sabueso.core.card_exploration_knowledge_comparison import frozen_protein_topics

    card = synthetic()
    card.unknown_stored["catalog_lookalike"] = frozen_protein_topics()
    root = next(
        item
        for item in card.explore().inspect().items()
        if item.label == "catalog_lookalike"
    ).open()
    path = tmp_path / "literal.json"
    root.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == frozen_protein_topics()
    assert saved.explorer._session["format"] != "sabueso.card_exploration@35"
