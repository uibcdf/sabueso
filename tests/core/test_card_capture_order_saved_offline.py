"""Canonical object ordering never reorders original captured input provenance."""

import json

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import StorageError
from sabueso.core.snapshot import canonical_json


def original_pool():
    # Deliberately differs from canonical Card-key order; no identity is inferred.
    cards = [
        Card(meta={"card_id": f"sabueso:{kind}:test:{name}", "entity_type": kind})
        for kind, name in (
            ("protein", "P"),
            ("small_molecule", "Z"),
            ("small_molecule", "A"),
            ("disease", "D"),
        )
    ]
    return Deck(cards + [cards[0]]).explore()


def test_canonical_roundtrip_retains_mixed_pool_order_and_repeated_inputs(
    tmp_path, monkeypatch
):
    pool = original_pool()
    explorer = pool.overview().items()[1].open().explorer
    view = explorer.view("activity_context")
    expected = view.native_payload
    assert [r["profile"] for r in expected["unsupported_inputs"]] == [
        "small_molecule",
        "disease",
    ]
    path = tmp_path / "mixed.json"
    receipt = view.save(path)
    inputs = tuple(explorer.access._inputs)
    before = path.read_bytes()
    monkeypatch.setattr(
        Card, "__init__", lambda *a, **k: pytest.fail("No current Card construction")
    )
    restored = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert restored.native_payload == expected
    assert restored.outcome == view.outcome
    assert restored.explorer.access._inputs == inputs
    assert list(restored.explorer.access._captures) == list(dict.fromkeys(inputs))
    assert inputs[0] == inputs[-1] and len(inputs) == 5
    assert path.read_bytes() == before


def test_resealed_input_permutation_cannot_rebind_retained_science(tmp_path):
    pool = original_pool()
    view = pool.overview().items()[1].open().explorer.view("activity_context")
    path = tmp_path / "original.json"
    view.save(path)
    bundle = json.loads(path.read_bytes())
    bundle["inputs"][0], bundle["inputs"][3] = (
        bundle["inputs"][3],
        bundle["inputs"][0],
    )
    # Refresh the outer integrity seal only. Scientific and exact-origin
    # predicates must still reject the altered original occurrence order.
    from sabueso.core.card_exploration_storage import _seal

    bundle = _seal({k: v for k, v in bundle.items() if k != "bundle_digest"})
    path.write_text(canonical_json(bundle))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_native_deck_original_reopens_after_mixed_molecule_reading(tmp_path):
    pool = original_pool()
    pool.overview().items()[1].open().explorer.view("activity_context")
    path = tmp_path / "deck.json.gz"
    receipt = pool.overview().save(path, compression="gzip")
    restored = sabueso.read_deck_exploration(
        path, expected_digest=receipt["bundle_digest"]
    )
    native = restored.items()[1].open().explorer.view("activity_context")
    assert native.explorer.mode == "saved"
    assert native.outcome["status"] == "missing_prerequisite"
    assert restored.context["input_count"] == 5
