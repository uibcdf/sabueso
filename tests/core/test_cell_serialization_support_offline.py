"""Private support reuse preserves original bytes and public isolation (#167)."""

import json
import socket
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.errors import StorageError
from sabueso.tools.card.disease import resolve_disease_card
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.mondo import FixtureMONDOClient


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No source acquisition")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def workload(nature):
    if nature == "protein":
        card = Card.from_dict(
            json.loads(
                Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text()
            )
        )
        topic = "function"
    elif nature == "small_molecule":
        card = single_molecule_card(
            chembl=FixtureChEMBLClient("temp_data").molecules(["CHEMBL110"])
        )
        topic = "properties"
    elif nature == "disease":
        card = resolve_disease_card(
            "MONDO:0014221", mondo_client=FixtureMONDOClient("temp_data")
        )[0]
        topic = "definition"
    else:
        card = Card()
        card.unknown_stored["synthetic"] = {
            "typed": [False, 0, 0.0, -0.0, None, "", "α🧬"],
            "literal_quantity_lookalike": {"value": 7, "unit": "dalton"},
        }
        topic = None
    explorer = card.explore()
    view = explorer.view(topic) if topic else explorer.inspect()
    return card, view


@pytest.mark.parametrize("nature", ["protein", "small_molecule", "disease", "generic"])
def test_owned_support_and_defensive_reference_produce_identical_original_bytes(
    nature, tmp_path, monkeypatch
):
    import sabueso.core.card_exploration_storage as storage

    card, view = workload(nature)
    before = card.to_dict()
    operation = storage._cell_record

    class DefensiveReference:
        def __init__(self, cell):
            self.cell = cell

        def to_dict(self):
            return self.cell.to_dict()

    def reference(item, column, cell):
        # Exercise the original public defensive-copy boundary, including
        # quantities, without duplicating its conversion/verification logic.
        return operation(item, column, DefensiveReference(cell))

    control, candidate = tmp_path / "control.json", tmp_path / "candidate.json"
    with monkeypatch.context() as patch:
        patch.setattr(storage, "_cell_record", reference)
        first = view.save(control)
    second = view.save(candidate)
    assert control.read_bytes() == candidate.read_bytes()
    assert first["bundle_digest"] == second["bundle_digest"]
    assert card.to_dict() == before
    restored = sabueso.read_exploration(
        candidate, expected_digest=first["bundle_digest"]
    )
    assert restored.native_payload == view.native_payload
    third = tmp_path / "restored.json"
    restored.save(third)
    assert sabueso.read_exploration(third).native_payload == view.native_payload

    for item in (view.items()[0], restored.items()[0]):
        cells = item.cells
        original = {name: cell.to_dict() for name, cell in cells.items()}
        for cell in cells.values():
            support = cell.support
            if support:
                support[0].clear()
            support.append({"synthetic": "caller mutation"})
            value = cell.value
            if isinstance(value, (dict, list)):
                value.clear()
        assert {name: cell.to_dict() for name, cell in cells.items()} == original


def test_resealed_support_edit_still_fails_independent_original_verification(tmp_path):
    _, view = workload("protein")
    path = tmp_path / "original.json"
    view.save(path)
    bundle = json.loads(path.read_text())
    node = bundle["views"][bundle["root_navigation_ref"]]
    cell = next(
        cell
        for item in node["state"]["items"].values()
        for cell in item["cells"].values()
        if cell["support"]
    )
    cell["support"] = [{"synthetic": "unsupported source basis"}]
    _seal(bundle)
    path.write_text(json.dumps(bundle))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_direct_internal_restore_keeps_caller_state_isolated(tmp_path):
    from sabueso.core.card_exploration_storage import _restore

    _, view = workload("protein")
    path = tmp_path / "original.json"
    receipt = view.save(path)
    bundle = json.loads(path.read_text())
    restored = _restore(bundle, receipt["bundle_digest"])
    expected = restored.rows()
    root = bundle["views"][bundle["root_navigation_ref"]]
    root["state"]["items"].clear()
    root["state"]["context"].clear()
    assert restored.rows() == expected
