"""Receiving budgets never clip science or require allocating enormous regions."""

import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core import region_requests as receiving
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError


def forbidden(*args, **kwargs):
    raise AssertionError("No expansion, current science or network was permitted")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def card():
    return Card.from_dict(
        json.loads(Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text())
    )


@pytest.mark.parametrize("limit", [6, 7, None])
def test_union_duplicates_overlap_and_exact_boundary(limit):
    request = [[2, 5], [4, 7], 2]
    before = deepcopy(request)
    positions, receipt = receiving.normalize(request, region_budget=limit, record=True)
    assert positions == list(range(2, 8))
    assert receipt["positions"] == 6 and receipt["terms"] == 3
    assert receipt["request"] == request == before


@pytest.mark.parametrize(
    "region_input,limit", [([[1, 6]], 5), ([2] * 6, 5), ([[1, 10**12]], 100_000)]
)
def test_refuse_before_expansion_with_recovery_metadata(
    monkeypatch, region_input, limit
):
    monkeypatch.setattr(receiving, "_expand", forbidden)
    with pytest.raises(ArgumentError, match="region_budget=None") as error:
        receiving.normalize(region_input, region_budget=limit)
    assert error.value.extra["region_workload"]["expanded"] is False
    assert error.value.extra["region_workload"]["region_budget"] == limit


@pytest.mark.parametrize("limit", [False, True, 0, -1, 1.5, "100", {}])
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_budget_is_never_an_argument_digestion_bypass(card, limit, skip):
    with pytest.raises(ArgumentError, match="region_budget"):
        card.structures(region=[96], region_budget=limit, skip_digestion=skip)


@pytest.mark.parametrize(
    "route", ["card", "deck", "explain", "human", "question", "agent", "table"]
)
@pytest.mark.parametrize("skip", [False, True])
def test_public_refusal_and_deliberate_override_preserve_results(card, route, skip):
    region = [[95, 100]]
    original = card.to_dict()
    explorer = card.explore()
    access = card.access()
    deck = Deck([card])

    def invoke(limit):
        kwargs = {"region_budget": limit, "skip_digestion": skip}
        if route == "card":
            return card.structures(region=region, **kwargs)
        if route == "deck":
            return deck.structure_inventory(regions={card.id: region}, **kwargs)
        if route == "explain":
            return deck.explain(
                card.id, structure_ref="pdb:1SUX", regions=region, **kwargs
            )
        if route == "table":
            return card.table("structures", region=region, **kwargs)
        if route == "human":
            return explorer.view("structures", options={"region": region}, **kwargs)
        if route == "question":
            return explorer.answer(
                "region_coverage",
                options={"sequence_ref": "uniprot:P52270", "region": region},
                **kwargs,
            )
        return access.select("structures", options={"region": region}, **kwargs)

    with pytest.raises(ArgumentError, match="region_budget=None"):
        invoke(5)
    raised = invoke(6)
    raised_receipt = (
        access.last_workload if route == "agent" else getattr(raised, "workload", None)
    )
    unlimited = invoke(None)
    unlimited_receipt = (
        access.last_workload
        if route == "agent"
        else getattr(unlimited, "workload", None)
    )
    if route in ("card", "deck", "explain", "table"):
        assert raised == unlimited
    else:
        assert raised.result_ref == unlimited.result_ref
    if route != "table":
        assert raised_receipt["region_budget"] == 6
        assert unlimited_receipt["region_budget"] is None
        assert unlimited_receipt["request"] == (
            {card.id: region} if route == "deck" else region
        )
        receipt = deepcopy(unlimited_receipt)
        receipt["request"] = "changed"
        assert (access.last_workload if route == "agent" else unlimited.workload)[
            "request"
        ] != "changed"
    assert card.to_dict() == original and region == [[95, 100]]
    assert receiving.current_budget() == receiving.DEFAULT_REGION_BUDGET


@pytest.mark.parametrize("skip", [False, True])
def test_unlimited_still_refuses_outside_original_reference_before_expansion(
    card, monkeypatch, skip
):
    monkeypatch.setattr(receiving, "_expand", forbidden)
    with pytest.raises(ArgumentError, match="outside.*reference"):
        card.structures(region=[[1, 10**12]], region_budget=None, skip_digestion=skip)
    with pytest.raises(ArgumentError, match="outside.*reference"):
        Deck([card]).structure_inventory(
            regions=[[1, 10**12]], region_budget=None, skip_digestion=skip
        )
    with pytest.raises(ArgumentError, match="outside.*reference"):
        card.explore().view(
            "structures",
            options={"region": [[1, 10**12]]},
            region_budget=None,
            skip_digestion=skip,
        )


def test_aggregate_budget_precedes_any_recipient_expansion(card, monkeypatch):
    second = Card.from_dict(card.to_dict())
    second.meta["card_id"] = "synthetic:second"
    monkeypatch.setattr(receiving, "_expand", forbidden)
    with pytest.raises(ArgumentError, match="12 distinct positions"):
        receiving.normalize([[95, 100]], [card, second], region_budget=11)
    with pytest.raises(ArgumentError, match="input terms"):
        receiving.normalize(
            {card.id: [96] * 3, second.id: [96] * 3},
            [card, second],
            region_budget=5,
            allow_mapping=True,
        )


def test_unknown_reference_is_budgeted_and_override_does_not_invent_support(card):
    card.sections["sequence"].pop("primary")
    with pytest.raises(ArgumentError, match="region_budget"):
        card.structures(region=[[1, 6]], region_budget=5)
    result = card.structures(region=[[1, 6]], region_budget=None)
    assert all(
        row["coordinate_scope"]["status"] != "comparable" for row in result["items"]
    )


def test_saved_lookup_receiving_is_separate_from_original_science(
    card, tmp_path, monkeypatch
):
    original = card.explore().view(
        "structures", options={"region": [[95, 100]]}, region_budget=None
    )
    path = tmp_path / "original.json"
    original.save(path)
    packed = path.read_bytes()
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr("sabueso.core.structures.structure_inventory", forbidden)
    saved = sabueso.read_exploration(path)
    assert saved.workload is None  # never invent an original receiving policy
    # Reading an original artifact never reapplies today's live receiving limit.
    assert saved.native_payload == original.native_payload
    with pytest.raises(ArgumentError, match="region_budget"):
        saved.explorer.view(
            "structures", options={"region": [[95, 100]]}, region_budget=5
        )
    selected = saved.explorer.view(
        "structures", options={"region": [[95, 100]]}, region_budget=None
    )
    assert selected.native_payload == saved.native_payload
    assert selected.workload["region_budget"] is None
    assert path.read_bytes() == packed


def test_capabilities_disclose_default_and_override(card):
    human = card.explore().capabilities["region_workload"]
    agent = card.access().capabilities["region_workload"]
    assert human == agent
    assert human["default"] == 100_000
    assert "region_budget=None" in human["override"]
    assert human["silent_truncation"] is False


def test_cached_selection_identity_and_receiving_requests_are_separate(card):
    access = card.access()
    first = access.select(
        "structures", options={"region": [[95, 100]]}, region_budget=6
    )
    first_receipt = access.last_workload
    second = access.select(
        "structures", options={"region": list(range(95, 101))}, region_budget=None
    )
    assert first is second
    assert first_receipt["request"] == [[95, 100]]
    assert first_receipt["region_budget"] == 6
    assert access.last_workload["request"] == list(range(95, 101))
    assert access.last_workload["region_budget"] is None


def test_cached_preflight_does_not_reconstruct_card(card, monkeypatch):
    explorer = card.explore()
    first = explorer.view("structures", options={"region": [96]})
    before = len(explorer._session["views"])
    monkeypatch.setattr(Card, "from_dict", forbidden)
    second = explorer.view("structures", options={"region": [96]}, region_budget=None)
    assert second.result_ref == first.result_ref
    assert len(explorer._session["views"]) == before + 1


def test_foreign_question_axis_stays_unsupported_instead_of_using_focal_bounds(card):
    answer = card.explore().answer(
        "region_coverage",
        options={"sequence_ref": "uniprot:FOREIGN", "region": [500]},
        region_budget=None,
    )
    assert answer.outcome["status"] == "unsupported"


@pytest.mark.parametrize("route", ["human", "agent"])
@pytest.mark.parametrize("limit", [100_001, None])
def test_deliberate_requests_above_default_have_no_hidden_nested_ceiling(route, limit):
    # Moderate allocation, not an exhaustion test. An anonymous Card makes the
    # scientific prerequisite explicitly unavailable; no result is invented.
    explorer = Card(meta={"entity_type": "protein"}).explore()
    options = {"region": [[1, 100_001]]}
    with pytest.raises(ArgumentError, match="region_budget"):
        explorer.view("structures", options=options)
    if route == "human":
        result = explorer.view("structures", options=options, region_budget=limit)
        assert result.outcome["status"] == "missing_prerequisite"
        assert result.workload["region_budget"] == limit
    else:
        result = explorer.access.select(
            "structures", options=options, region_budget=limit
        )
        assert result.count == 0
        assert explorer.access.last_workload["region_budget"] == limit
    assert (
        len(
            result._selection._scientific.options["region"]
            if route == "human"
            else result._scientific.options["region"]
        )
        == 100_001
    )


def test_mixed_deck_explanation_counts_only_protein_recipients(card):
    molecule = Card(
        meta={
            "entity_type": "small_molecule",
            "card_id": "sabueso:small_molecule:pubchem:2244",
        }
    )
    result = Deck([card, molecule]).explain(
        card.id, structure_ref="pdb:1SUX", regions=[[95, 100]], region_budget=6
    )
    expected = Deck([card]).explain(
        card.id, structure_ref="pdb:1SUX", regions=[[95, 100]], region_budget=6
    )
    assert result == expected


@pytest.mark.parametrize("region,limit", [([[1, 12345]], 11), ([1] * 123, 11)])
def test_restricted_diagnostics_preserve_refusal_without_request_facts(region, limit):
    import smonitor

    with smonitor.diagnostic_scope():
        with pytest.raises(ArgumentError) as error:
            receiving.normalize(region, region_budget=limit)
    assert error.value.code == "SABUESO-E-ARG-001"
    assert "123" not in str(error.value)
    assert "region_budget=11" not in str(error.value)
    assert "region_workload" not in error.value.extra
    assert error.value.extra["reason"] == "region_budget_exceeded"
