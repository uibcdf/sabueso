"""Original variant transports, finite request scope and resealed semantic refusals."""

import json
from copy import deepcopy

import pytest
from test_card_variant_history_offline import (
    assert_saved_original,
    block_current,
    hydrate_original,
    original_navigation_ids,
)
from test_card_variant_original_offline import original as original

import sabueso
from sabueso.core import card_exploration_storage as storage
from sabueso.core.card_exploration_shared_values_v9 import pack, unpack
from sabueso.core.errors import StorageError


@pytest.fixture(scope="module")
def variant_file(original, tmp_path_factory):
    name = "variants-support-missing"
    original.cache.clear()
    nodes, _ = hydrate_original(original, name)
    root = nodes[original.case(name)["named_views"]["root"]]
    ids = original_navigation_ids(nodes)
    path = tmp_path_factory.mktemp("variant-original-file") / "original.json"
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        root.save(
            path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    logical = (
        unpack(raw, limit=None, component_limit=None)[0]
        if raw["format"] == "sabueso.card_exploration@30"
        else {
            key: value
            for key, value in raw.items()
            if key not in ("digests", "bundle_digest")
        }
    )
    return path, logical, ids


def test_unchanged_resealed_variant_control_is_accepted(variant_file, monkeypatch):
    packet = storage._seal(pack(variant_file[1], None, threshold=0, min_saving=0))
    block_current(monkeypatch)
    received = storage._restore(
        packet, packet["bundle_digest"], max_logical_bytes=None, component_limit=None
    )
    assert (
        received.validation["verifier"]
        == "variant_tissue_context_exploration_binding@1"
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "native",
        "coordinate",
        "threshold",
        "source_role",
        "input_location",
        "cell",
        "question",
        "request",
        "origin",
    ),
)
def test_resealed_variant_semantic_changes_are_refused(
    variant_file, monkeypatch, mutation
):
    logical = deepcopy(variant_file[1])
    ref = next(
        ref
        for ref in logical["scientific_results"]
        if logical["objects"][ref]["context"]["adapter"]
        == "variant_tissue_context_exploration@1"
        and logical["objects"][ref]["context"]["options"]["mode"] == "variants"
    )
    wire = logical["objects"][ref]
    key = next(iter(wire["rows"]))
    root = logical["views"][logical["root_navigation_ref"]]
    if mutation == "native":
        wire["native_payload"]["items"][0]["pext"]["basis"] = (
            "synthetic zero expression"
        )
    elif mutation == "coordinate":
        wire["rows"][key]["assembly"] = "GRCh37"
    elif mutation == "threshold":
        wire["context"]["options"]["threshold"] = 0.37
    elif mutation == "source_role":
        wire["support"][key]["source_assertions"][0]["role"] = (
            "synthetic substituted role"
        )
    elif mutation == "input_location":
        wire["support"][key]["inputs"][0]["location"]["segments"][-1]["value"] = 999
    elif mutation == "cell":
        next(iter(root["state"]["items"].values()))["cells"]["support_state"][
            "value"
        ] = "synthetic replaced state"
    elif mutation == "question":
        root["flags"]["_request"] = {
            "question": "isoform_tissue_context",
            "topic": "variants",
            "options": {"mode": "variants", "threshold": 0.1},
        }
    elif mutation == "request":
        machine = next(
            view for view in logical["views"].values() if view["flags"]["_machine_ref"]
        )
        machine["selection"]["fields"] = ["label", "label"]
    else:
        child = next(
            view
            for view in logical["views"].values()
            if (view["flags"].get("_context_override") or {}).get("variant_context")
            == "original_item"
        )
        child["origin"] = next(
            key
            for key, view in logical["views"].items()
            if view["flags"]["_record_panel"] == "variants"
            and view["flags"]["_machine_ref"] is not None
        )
    packet = storage._seal(pack(logical, None, threshold=0, min_saving=0))
    block_current(monkeypatch)
    with pytest.raises(StorageError):
        storage._restore(
            packet,
            packet["bundle_digest"],
            max_logical_bytes=None,
            component_limit=None,
        )


@pytest.mark.parametrize("compression", ("none", "gzip", "zstd"))
def test_variant_transport_resave_keeps_every_actual_origin(
    variant_file, original, monkeypatch, tmp_path, compression
):
    block_current(monkeypatch)
    received = sabueso.read_exploration(
        variant_file[0],
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
    )
    target = tmp_path / (compression + ".json")
    received.save(
        target,
        compression=compression,
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
    )
    saved = sabueso.read_exploration(
        target, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
    )
    assert_saved_original(saved, original, "variants-support-missing", variant_file[2])


def test_saved_variant_catalogs_and_finite_requests_use_frozen_typed_options(
    variant_file, monkeypatch
):
    from sabueso.core import card_exploration as human
    from sabueso.core import card_exploration_profiles as profiles
    from sabueso.core import card_variant_presentation_v1 as presentation

    block_current(monkeypatch)
    saved = sabueso.read_exploration(
        variant_file[0],
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
    )
    monkeypatch.setattr(human, "_TOPICS", {})
    for name in ("NATURE_TOPICS", "QUESTIONS", "COMMON_QUESTIONS"):
        monkeypatch.setattr(profiles, name, {})

    def forbidden(*args, **kwargs):
        raise AssertionError("Saved reading used current presentation")

    for name in ("opening", "display_row", "context_opening"):
        monkeypatch.setattr(presentation, name, forbidden)
    assert "variants" in saved.explorer.topics().native_payload
    assert {
        "variant_tissue_context",
        "isoform_tissue_context",
    } <= saved.explorer.questions().native_payload.keys()
    assert (
        saved.explorer.answer("variant_tissue_context").native_payload
        == saved.native_payload
    )
    assert str(saved) and saved._repr_html_()
    absent = saved.explorer.access.select(
        "variants", options={"threshold": 0.37}, skip_digestion=True
    )
    assert absent.page()["outcome"]["status"] == "not_saved"
    missing = saved.explorer.access.select(
        "variants", where={"label": "a never executed filter"}, skip_digestion=True
    )
    assert missing.count == 0 and missing.page()["outcome"]["status"] == "not_saved"
    parent = saved.explorer.answer("variant_tissue_context").filter(
        "kind", equals="population_variant"
    )
    item = parent.items()[0]
    assert item.open().back() is parent and item.explain().back() is parent
    links = item.related()
    assert links.back() is parent
    for link in links.items():
        destination = link.open()
        assert destination.back() is links and destination.request == parent.request
        if not link._entry.value["candidates"]:
            assert (
                destination.outcome["status"] == "missing_prerequisite"
                and destination.explorer is None
            )


@pytest.mark.parametrize("first", ("human", "machine"))
def test_one_route_does_not_invent_an_unexecuted_other_route(original, tmp_path, first):
    from sabueso.core.card import Card

    data = original.ref(original.case("synthetic-variants")["input"])
    explorer = Card.from_dict(deepcopy(data["focal"])).explore()
    root = (
        explorer.answer("variant_tissue_context")
        if first == "human"
        else explorer.access.select("variants")
    )
    path = tmp_path / "single-route.json"
    root.save(path)
    saved = sabueso.read_exploration(path)
    if first == "human":
        assert (
            saved.explorer.answer("variant_tissue_context").native_payload
            == root.native_payload
        )
        assert (
            saved.explorer.access.select("variants").page()["outcome"]["status"]
            == "not_saved"
        )
    else:
        assert (
            saved.explorer.access.select("variants").selection_ref == root.selection_ref
        )
        assert (
            saved.explorer.answer("variant_tissue_context").outcome["status"]
            == "not_saved"
        )
