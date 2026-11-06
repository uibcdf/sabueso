"""Exact shared JSON representation, logical budgets and hostile packet refusal."""

import gzip
import hashlib
import json
import math
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core import card_exploration_shared_values_v1 as shared
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _prepare, _restore, _seal
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion


def original(value):
    return {
        "format": "sabueso.card_exploration@1",
        "producer": {
            "sabueso_version": "synthetic-codec-control",
            "verifier": "literal_exploration_binding@1",
            "scope": "Synthetic representation control; no scientific assertions.",
        },
        "root_view_ref": "synthetic",
        "root_navigation_ref": "synthetic",
        "cards": {},
        "inputs": [],
        "objects": {"example": value},
        "locations": {},
        "views": {},
        "navigation": {"links": {}, "explanations": {}},
        "capabilities": {},
        "presentation_metadata": {},
    }


def encoded(value):
    return _seal(shared.pack(original(value), threshold=0, min_saving=-1000000))


@pytest.mark.parametrize(
    "value",
    [
        None,
        False,
        0,
        1,
        -0.0,
        [0.0, -0.0, True, 1, False, 0, 1.0],
        {"utf8": "αβγ🧪", "escapes": '\\"\n\t\r'},
        {"long": "α" * 400},
        {"value_ref": "SV_this_is_literal_data"},
        [[], {}, None, []],
    ],
)
def test_exact_original_values_and_canonical_byte_count(value):
    source = original(value)
    packet = _seal(shared.pack(source, threshold=0, min_saving=-1000000))
    received, report = shared.unpack(packet, packet["bundle_digest"])
    assert canonical_json(received) == canonical_json(source)
    assert report["logical_bytes"] == len(canonical_json(source).encode("utf-8"))
    assert report["logical_format"] == source["format"]


def test_equal_storage_keeps_distinct_entities_list_occurrences_and_quantities():
    common = {"name": "same name", "quantity": {"value": 2.0, "unit": "nanometer"}}
    source = original(
        {
            "entities": [{"id": "entry:one", **common}, {"id": "entry:two", **common}],
            "occurrences": [common, deepcopy(common), common],
        }
    )
    packet = _seal(shared.pack(source, threshold=0, min_saving=-1000000))
    received, _ = shared.unpack(packet)
    assert received == source
    assert [r["id"] for r in received["objects"]["example"]["entities"]] == [
        "entry:one",
        "entry:two",
    ]
    assert len(received["objects"]["example"]["occurrences"]) == 3
    assert received["objects"]["example"]["occurrences"][0]["quantity"] == {
        "value": 2.0,
        "unit": "nanometer",
    }


def test_repeated_component_is_physically_stored_once_without_expanded_json():
    part = {"source": "frozen-public-control", "content": "ACGT" * 1000}
    source = original([deepcopy(part) for _ in range(100)])
    packet = _seal(shared.pack(source, threshold=0, min_saving=-1000000))
    raw = canonical_json(packet).encode("utf-8")
    assert len(raw) < len(canonical_json(source)) // 10
    assert (
        sum(
            record.get("value") == part["content"]
            for record in packet["values"].values()
        )
        == 1
    )
    assert shared.unpack(packet)[0] == source


def test_small_values_keep_the_original_format_and_inputs_stay_detached():
    source = original({"a": [1, 2, 3]})
    assert shared.pack(source) is source
    before = deepcopy(source)
    packet = _seal(shared.pack(source, threshold=0, min_saving=-1000000))
    restored, _ = shared.unpack(packet)
    restored["objects"]["example"]["a"].append(4)
    assert source == before
    assert shared.unpack(packet)[0] == before


def test_logical_budget_counts_reuse_and_explicit_override():
    source = original(["A" * 1000] * 200)
    packet = _seal(shared.pack(source, threshold=0, min_saving=-1000000))
    with pytest.raises(ArgumentError, match="max_logical_bytes=None"):
        shared.pack(source, limit=1000, threshold=0, min_saving=-1000000)
    with pytest.raises(ArgumentError, match="max_logical_bytes=None"):
        shared.unpack(packet, limit=1000)
    for limit in (None, packet["logical_bytes"]):
        assert shared.unpack(packet, limit=limit)[0] == source


def test_small_valid_dag_cannot_hide_exponential_validation_work():
    value = None
    for _ in range(28):
        value = [value, value]
    packet = _seal(shared.pack(original(value), limit=None))
    assert len(canonical_json(packet)) < 20000
    assert packet["logical_bytes"] > shared.LOGICAL_LIMIT
    with pytest.raises(ArgumentError, match="max_logical_bytes"):
        shared.unpack(packet)
    # Deliberate override still reconstructs shared containers, never copies
    # the exponentially large logical document into RAM.
    received, report = shared.unpack(packet, limit=None, component_limit=None)
    value = received["objects"]["example"]
    for _ in range(28):
        assert value[0] is value[1]
        value = value[0]
    assert value is None and report["logical_bytes"] == packet["logical_bytes"]


@pytest.mark.parametrize("location", ["non_views", "one_view"])
def test_decoded_ceiling_also_bounds_logical_components(location):
    part = ["A" * 1000] * 200
    source = original(part if location == "non_views" else None)
    if location == "one_view":
        source["views"] = {"N0": {"synthetic": part}}
    packet = _seal(shared.pack(source, threshold=0, min_saving=-1000000000))
    assert len(canonical_json(packet)) < 50000
    with pytest.raises(ArgumentError, match="max_decoded_bytes"):
        shared.unpack(packet, component_limit=50000)
    assert shared.unpack(packet, component_limit=None)[0] == source


def test_default_packing_requires_large_payload_and_a_real_saving():
    source = original(["A" * 1000] * 18000)
    packet = shared.pack(source)
    assert packet["format"] == shared.FORMAT
    assert shared.unpack(_seal(packet))[0] == source
    # A large unique string has no structural redundancy to remove.
    unique = original("A" * (shared.PACK_THRESHOLD + 1))
    assert shared.pack(unique) is unique


@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), float("-inf"), {1: "invalid-key"}, {1, 2}, object()],
)
def test_unsupported_json_does_not_get_repaired(value):
    with pytest.raises(StorageError):
        shared.pack(original(value), threshold=0, min_saving=-1000000)


def test_cycles_fail_before_packing():
    value = []
    value.append(value)
    with pytest.raises(StorageError, match="Cyclic"):
        shared.pack(original(value), threshold=0, min_saving=-1000000)


@pytest.mark.parametrize(
    "change",
    [
        "value",
        "extra",
        "producer",
        "size",
        "missing",
        "orphan",
        "unknown_kind",
        "literal_ref",
        "unordered_keys",
    ],
)
def test_resealed_physical_packets_do_not_bypass_representation_contract(change):
    packet = encoded({"a": ["x" * 300], "b": True})
    root = packet["root"]["value_ref"]
    if change == "value":
        key = next(k for k, v in packet["values"].items() if v["kind"] == "text")
        packet["values"][key]["value"] = "y" * 300
    elif change == "extra":
        packet["unexpected"] = True
    elif change == "producer":
        packet["producer"]["verifier"] = "unavailable@1"
    elif change == "size":
        packet["logical_bytes"] += 1
    elif change == "missing":
        packet["values"].pop(root)
    elif change == "orphan":
        record = {"kind": "array", "items": ["not-reachable"]}
        packet["values"]["SV_" + digest(canonical_json(record))] = record
    elif change == "unknown_kind":
        packet["values"][root]["kind"] = "executable"
    elif change == "literal_ref":
        packet["root"]["unrecognized"] = root
    else:
        packet["values"][root]["items"].reverse()
    with pytest.raises(StorageError):
        shared.unpack(_seal(packet))


def test_independent_expected_digest_and_signed_zero_survive():
    packet = encoded([-0.0, 0.0])
    with pytest.raises(StorageError):
        shared.unpack(packet, "sha256:" + "0" * 64)
    restored, _ = shared.unpack(packet, packet["bundle_digest"])
    assert math.copysign(1, restored["objects"]["example"][0]) == -1
    assert math.copysign(1, restored["objects"]["example"][1]) == 1


@pytest.mark.parametrize("value", [{"a": [1, 2]}, ["αβ" * 200] * 20])
def test_sealed_size_is_exact_without_materializing_the_document(value):
    source = original(value)
    assert shared.sealed_size(source) == len(
        canonical_json(_seal(deepcopy(source))).encode("utf-8")
    )
    packed = shared.pack(source, threshold=0, min_saving=-1000000)
    assert shared.sealed_size(packed) == len(
        canonical_json(_seal(deepcopy(packed))).encode("utf-8")
    )


def small_card(nature):
    card = Card(
        meta={"entity_type": nature, "card_id": f"sabueso:{nature}:custom:synthetic"}
    )
    refs = []
    for index in range(2):
        statement = make_source_assertion(
            "names.canonical_name", "Synthetic", "Synthetic", str(index), "2026-11-06"
        )
        card.source_assertion_store.add(statement)
        refs.append(statement["id"])
    card.sections["names"] = {
        "canonical_name": {"value": "Synthetic", "source_assertion_ids": refs}
    }
    return card


def force_shared(monkeypatch):
    pack = shared.pack
    monkeypatch.setattr(
        shared,
        "pack",
        lambda bundle, limit: pack(bundle, limit, threshold=0, min_saving=-1000000),
    )


@pytest.mark.parametrize("nature", ["protein", "small_molecule", "disease", "other"])
@pytest.mark.parametrize("route", ["human", "agent"])
def test_public_read_save_resave_preserves_nature_sources_and_original_bindings(
    nature, route, tmp_path, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network, live navigation or Card reconstruction")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    card = small_card(nature)
    before = card.to_dict()
    view = card.explore().inspect("names")
    view.items()[0].related()
    force_shared(monkeypatch)
    path = tmp_path / "shared.json"
    target = view if route == "human" else view._selection
    receipt = target.save(path)
    packet = json.loads(path.read_text(encoding="utf-8"))
    assert packet["format"] == shared.FORMAT
    monkeypatch.setattr(Card, "from_dict", forbidden)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert saved.validation["representation_verifier"] == shared.VERIFIER
    assert saved.validation["verifier"] == "shared_link_support_binding@1"
    assert saved.native_payload == view.native_payload
    assert len(saved.items()[0].related().filter("role", equals="source").items()) == 2
    value = saved.native_payload
    value["canonical_name"]["value"] = "caller mutation"
    assert saved.native_payload == view.native_payload
    second = tmp_path / "resaved.json"
    saved.save(second)
    assert sabueso.read_exploration(second).native_payload == view.native_payload
    assert card.to_dict() == before


@pytest.mark.parametrize("budget", [False, 0, -1, "100", 1.5])
def test_public_logical_budget_rejects_invalid_values_before_preparation(
    budget, tmp_path
):
    view = small_card("protein").explore().inspect("names")
    with pytest.raises(ArgumentError):
        view.save(tmp_path / "invalid.json", max_logical_bytes=budget)
    assert not (tmp_path / "invalid.json").exists()


def test_public_logical_refusal_explains_override_without_partial_file(
    tmp_path, monkeypatch
):
    view = small_card("protein").explore().inspect("names")
    force_shared(monkeypatch)
    path = tmp_path / "shared.json"
    with pytest.raises(ArgumentError, match="max_logical_bytes=None"):
        view.save(path, max_logical_bytes=100)
    assert not path.exists()
    view.save(path, max_logical_bytes=None)
    with pytest.raises(ArgumentError, match="max_logical_bytes=None"):
        sabueso.read_exploration(path, max_logical_bytes=100)
    assert (
        sabueso.read_exploration(path, max_logical_bytes=None).native_payload
        == view.native_payload
    )


@pytest.mark.parametrize(
    "change", ["cell_value", "cell_support", "selected", "selection_value"]
)
def test_fresh_merkle_hashes_do_not_bypass_original_view_predicates(change):
    view = small_card("protein").explore().inspect("names")
    logical = _prepare(view)
    record = logical["views"][logical["root_navigation_ref"]]
    item = next(iter(record["state"]["items"].values()))
    if change == "cell_value":
        item["cells"]["value"]["value"] = "forged"
    elif change == "cell_support":
        item["cells"]["value"]["support"] = []
    elif change == "selected":
        record["selected"] = []
    else:
        record["selection"]["entries"][0]["value"] = "forged"
    packet = _seal(shared.pack(logical, threshold=0, min_saving=-1000000000))
    # The representation itself is valid and all object hashes are fresh.
    shared.unpack(packet, packet["bundle_digest"])
    with pytest.raises(StorageError):
        _restore(packet, packet["bundle_digest"])


def test_archived_writer_replay_keeps_native_question_and_original_sources(monkeypatch):
    # This is explicitly an archived-writer replay, not a pre-reader artifact.
    # Its five actual public statements form a reduced Card, not the64-item workload.
    path = Path(__file__).parent / "data/shared_values_v12_writer_replay.json.gz"
    raw = path.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "9ca744ad7a46ffc51cfe82ae2d031b4af032aa1230d6557b0abc21a775e3cb5b"
    )
    original = json.loads(gzip.decompress(raw))
    assert original["format"] == "sabueso.card_exploration@12"
    assert original["producer"]["sabueso_version"] == "0.14.0+184.gee782e8"

    def forbidden(*a, **k):
        raise AssertionError("No current native mapper, factory or network")

    import sabueso.mappings.alphafold_modelcif_reference_v1 as current

    monkeypatch.setattr(current, "interpret", forbidden)
    monkeypatch.setattr(current, "crc64", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    legacy = _restore(original, original["bundle_digest"])
    logical = {
        k: v for k, v in original.items() if k not in ("digests", "bundle_digest")
    }
    packet = _seal(shared.pack(logical, threshold=0, min_saving=-1000000000))
    received = _restore(packet, packet["bundle_digest"])
    assert received.native_payload == legacy.native_payload
    assert received.result_ref == legacy.result_ref
    assert received.validation["verifier"] == "native_model_navigation_binding@1"
    assert received.validation["representation_verifier"] == shared.VERIFIER
    links = received.explorer.answer("predicted_models").items()[0].related()
    question = links.filter("role", equals="question").items()[0]
    assert question._entry.value["model_context"]["request"]["options"]["region"] == [
        [201, 1600]
    ]
    assert question.open().result_ref == received.result_ref
    assert len(links.filter("role", equals="source").items()) == 5
    assert (
        hashlib.sha256(path.read_bytes()).hexdigest()
        == "9ca744ad7a46ffc51cfe82ae2d031b4af032aa1230d6557b0abc21a775e3cb5b"
    )
