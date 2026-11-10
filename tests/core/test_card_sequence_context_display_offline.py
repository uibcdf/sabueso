"""Current saved receiving distinguishes source-context displays from link clicks."""

import json

import pytest
from test_card_sequence_changes_offline import synthetic

import sabueso
from sabueso.core import card_exploration_storage as storage
from sabueso.core.errors import StorageError


def display(operation):
    explorer = synthetic().explore()
    context = explorer.answer("sequence_changes").items()[0].related()
    if operation == "filter":
        return context.filter("role", equals="source")
    if operation == "sort":
        return context.sort("label", descending=True)
    if operation == "presentation":
        return context.summary()
    if operation == "chained":
        return context.filter("role", equals="source").sort("label")
    return context.filter("label", equals="Unmatched synthetic display filter")


@pytest.mark.parametrize(
    "operation", ["filter", "sort", "presentation", "chained", "empty"]
)
def test_original_sequence_source_context_display_saves_without_a_question_menu(
    operation, tmp_path, monkeypatch
):
    root = display(operation)
    original = root.rows()
    path = tmp_path / "context.json"
    root.save(path)
    assert (
        json.loads(path.read_text(encoding="utf-8"))["format"]
        == "sabueso.card_exploration@35"
    )
    from sabueso.core import card_sequence_change_access as live

    monkeypatch.setattr(
        live, "materialize", lambda *a, **k: pytest.fail("Used current science")
    )
    saved = sabueso.read_exploration(path)
    assert saved.rows() == original
    assert saved.native_payload == root.native_payload
    assert saved.request == root.request
    assert saved.back().view_ref == root.back().view_ref
    if len(saved.items()) and operation != "presentation":
        source = saved.items()[0].open()
        assert source.back() is saved
        assert source.native_payload == root.items()[0].open().native_payload


@pytest.mark.parametrize("defect", ["unchanged", "operand", "selected", "source-cell"])
def test_resealed_source_context_display_cannot_change_its_original_operation(
    defect, tmp_path
):
    bundle = storage._prepare(display("filter"))
    record = bundle["views"][bundle["root_navigation_ref"]]
    if defect == "operand":
        record["flags"]["_display_request"]["equals"] = "question"
    elif defect == "selected":
        record["selected"] = []
    elif defect == "source-cell":
        item = next(iter(record["state"]["items"].values()))
        item["cells"]["label"]["value"] = "Changed original source"
    storage._seal(bundle)
    path = tmp_path / "resealed.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    if defect == "unchanged":
        assert sabueso.read_exploration(path).rows()
    else:
        with pytest.raises(StorageError):
            sabueso.read_exploration(path)


def test_shared_context_display_retains_its_actual_ancestry_without_a_menu(tmp_path):
    from sabueso.core.card_exploration_shared_values_v12 import pack

    root = display("chained")
    packet = storage._seal(
        pack(storage._prepare(root), threshold=0, min_saving=-(1024**2))
    )
    assert packet["format"] == "sabueso.card_exploration@36"
    path = tmp_path / "shared.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    saved = sabueso.read_exploration(path)
    assert saved.rows() == root.rows()
    assert saved.native_payload == root.native_payload
    again = tmp_path / "resaved.json.gz"
    saved.save(again, compression="gzip")
    assert sabueso.read_exploration(again).rows() == root.rows()
