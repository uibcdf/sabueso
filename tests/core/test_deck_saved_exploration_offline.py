"""Original Deck reopening preserves occurrences and refuses rebound context."""

import json
import socket
import subprocess
import sys

import pytest

from sabueso import read_deck_exploration
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json, digest


@pytest.fixture(autouse=True)
def no_acquisition(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Original Deck reading cannot acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def deck():
    first = Card(meta={"card_id": "sabueso:protein:test:z", "entity_type": "protein"})
    first.unknown_stored["original"] = {"value": [1, None], "unit": "nanometer"}
    other = Card(meta={"card_id": "sabueso:disease:test:a", "entity_type": "disease"})
    revision = Card.from_dict(first.to_dict())
    revision.unknown_stored["revision"] = 2
    return Deck(
        [first, other, first, revision, Card()],
        {
            "membership": {first.id: {"query": "Synthetic", "support": ["original"]}},
            "excluded": [{"candidate": "outside", "reason": "Synthetic"}],
            "operations": [{"rule": "synthetic@1", "options": {"x": None}}],
            "extension": {"retained": [True, "🧬"]},
        },
    )


def forbidden(*args, **kwargs):
    pytest.fail(
        "Original Deck reopening must not construct Cards or run current readers"
    )


@pytest.mark.parametrize("compression", ["none", "gzip", "zstd"])
def test_independent_original_selection_and_back_without_current_readers(
    tmp_path, monkeypatch, compression
):
    live = deck()
    root = live.access()
    ordered = root.sort("label", descending=True)
    selected = ordered.select(
        [ordered.items()[2].member_ref, ordered.items()[0].member_ref]
    )
    expected = selected.page()
    path = tmp_path / "deck.original"
    receipt = selected.save(path, compression=compression)
    original_bytes = path.read_bytes()
    live.meta.clear()
    live.cards[0].unknown_stored.clear()
    live.cards.reverse()
    for target in (
        "sabueso.core.card.Card.__init__",
        "sabueso.core.card_capture._capture_cards",
        "sabueso.core.deck_exploration._capture_cards",
        "sabueso.core.card_access.CardAccess.__init__",
        "sabueso.core.card_exploration.CardExplorer.__init__",
        "sabueso.core.deck_exploration.DeckView.sort",
        "sabueso.core.deck_exploration.DeckView.select",
    ):
        monkeypatch.setattr(target, forbidden)
    saved = read_deck_exploration(path, expected_digest=receipt["bundle_digest"])
    assert saved.page() == expected
    assert saved.inspect() == root.inspect()
    assert saved.back().view_ref == ordered.view_ref
    assert saved.back().back().view_ref == root.view_ref
    assert len(saved.back().back().items()) == 5
    assert saved.mode == "saved"
    assert all(item.open().explorer.mode == "saved" for item in saved.items())
    second = tmp_path / "second.json"
    saved.save(second)
    assert read_deck_exploration(second).page() == expected
    assert path.read_bytes() == original_bytes


def test_every_original_occurrence_and_literal_member_content_survives(tmp_path):
    root = deck().access()
    path = tmp_path / "deck.json"
    root.save(path)
    saved = read_deck_exploration(path)
    assert [i.context for i in saved.items()] == [i.context for i in root.items()]
    assert [i.inspect() for i in saved.items()] == [i.inspect() for i in root.items()]
    assert len({i.member_ref for i in saved.items()}) == 5
    assert saved.items()[0].context["card_ref"] == saved.items()[2].context["card_ref"]
    assert saved.items()[0].open().explorer is saved.items()[2].open().explorer
    assert saved.items()[3].context["card_ref"] != saved.items()[0].context["card_ref"]
    assert saved.items()[4].context["card_ref"] is None
    assert saved.context["deck_snapshot_id"] is None
    assert saved.items()[0].open().back() is saved


@pytest.mark.parametrize("empty", [True, False])
def test_empty_deck_or_empty_selection_can_reopen_and_resave(tmp_path, empty):
    root = (
        Deck([], {"excluded": ["Synthetic"]}).access()
        if empty
        else deck().access().filter("not-present")
    )
    path = tmp_path / "empty.json"
    root.save(path)
    saved = read_deck_exploration(path)
    assert saved.page()["complete"] and saved.page()["items"] == []
    assert saved.inspect() == root.inspect()
    assert saved.back().view_ref == root.back().view_ref


def reseal(bundle):
    bundle["bundle_digest"] = digest(
        canonical_json({k: v for k, v in bundle.items() if k != "bundle_digest"})
    )
    return canonical_json(bundle)


@pytest.mark.parametrize(
    "change",
    [
        "unknown_format",
        "extra",
        "metadata",
        "input_order",
        "positions",
        "request",
        "origin",
        "component",
        "root",
        "application",
    ],
)
def test_resealed_context_substitutions_are_refused(tmp_path, change):
    path = tmp_path / "deck.json"
    deck().access().filter("protein").save(path)
    bundle = json.loads(path.read_bytes())
    if change == "unknown_format":
        bundle["format"] = "sabueso.deck_exploration@999"
    elif change == "extra":
        bundle["extra"] = "foreign"
    elif change == "metadata":
        bundle["metadata"]["extension"] = {"different": True}
    elif change == "input_order":
        bundle["inputs"].reverse()
    elif change == "positions":
        bundle["views"][-1]["positions"] = [True]
    elif change == "request":
        bundle["views"][-1]["request"]["text"] = "disease"
    elif change == "origin":
        bundle["views"][-1]["origin"] = bundle["views"][-1]["view_ref"]
    elif change == "component":
        bundle["cards"][bundle["inputs"][0]] = bundle["cards"][bundle["inputs"][1]]
    elif change == "root":
        bundle["root_view_ref"] = "DV_missing"
    else:
        bundle["application"] = {"format": "foreign"}
    path.write_text(reseal(bundle))
    before = path.read_bytes()
    with pytest.raises(StorageError):
        read_deck_exploration(path)
    assert path.read_bytes() == before


def test_digest_duplicate_json_transport_limits_and_atomic_failures(tmp_path):
    root = deck().access()
    path = tmp_path / "original.json"
    receipt = root.save(path)
    raw = path.read_bytes()
    with pytest.raises(StorageError):
        read_deck_exploration(path, expected_digest="sha256:" + "0" * 64)
    with pytest.raises(ArgumentError):
        read_deck_exploration(path, max_decoded_bytes=32)
    with pytest.raises(ArgumentError):
        read_deck_exploration(path, max_logical_bytes=32)
    with pytest.raises(StorageError):
        root.save(path)
    with pytest.raises(ArgumentError):
        root.save(path, overwrite=True, max_encoded_bytes=32)
    assert path.read_bytes() == raw
    assert not list(tmp_path.glob(".sabueso-deck-reading-*"))
    path.write_bytes(raw.replace(b'"format":', b'"format":"foreign","format":', 1))
    with pytest.raises(StorageError):
        read_deck_exploration(path)
    assert receipt["root_view_ref"] == root.view_ref


def test_fresh_headless_process_is_inert_outside_checkout(tmp_path):
    path = tmp_path / "original.json.gz"
    receipt = deck().access().sort("kind").save(path, compression="gzip")
    code = """
import sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a, **k): raise AssertionError('current Card construction')
Card.__init__=forbidden
view=sabueso.read_deck_exploration(sys.argv[1], expected_digest=sys.argv[2])
assert len(view.items())==5
assert view.items()[0].open().explorer.mode=='saved'
assert not any(n in sys.modules for n in ('PySide6','aiohttp','molsysviewer','molsysmt'))
print('inert original Deck received')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(path), receipt["bundle_digest"]],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "inert original Deck received" in result.stdout


@pytest.mark.parametrize("skip", [False, True])
def test_shared_argument_guards_apply_before_work_even_without_digestion(
    tmp_path, skip
):
    root = Deck([]).access()
    path = tmp_path / "unused.json"
    for options in (
        {"compression": "unknown"},
        {"overwrite": 1},
        {"max_encoded_bytes": True},
        {"max_decoded_bytes": 0},
        {"max_logical_bytes": -1},
    ):
        with pytest.raises(ArgumentError):
            root.save(path, skip_digestion=skip, **options)
    for options in (
        {"expected_digest": "latest"},
        {"max_window_bytes": 1234},
        {"max_encoded_bytes": True},
        {"max_logical_bytes": 0},
    ):
        with pytest.raises(ArgumentError):
            read_deck_exploration(path, skip_digestion=skip, **options)
    assert not path.exists()
