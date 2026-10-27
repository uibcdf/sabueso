"""Original quaternary findings, inputs and requests survive independent reading."""

import gzip
import hashlib
import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from test_card_quaternary_interpretation_offline import (
    TOPIC,
    field,
    forbidden,
    relation,
    sample,
)

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_access import _handle
from sabueso.core.card_exploration_history import _require_matches
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.errors import StorageError


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def inert(monkeypatch):
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for name, methods in {
        "oligomer": ["oligomer_view", "declaration_scope", "interface_scope"],
        "oligomer_explanation": ["explain_oligomer", "_explain_oligomer"],
        "ligand_site_scope": ["reference", "annotation"],
        "card_quaternary_exploration": ["_materialize", "_rows", "links", "support"],
        "card_quaternary_access": ["materialize", "descriptor"],
        "card_scientific_access": ["descriptor"],
    }.items():
        module = importlib.import_module("sabueso.core." + name)
        for method in methods:
            monkeypatch.setattr(module, method, forbidden)


def test_genuine_original_live_capsule_binds_frozen_rules_and_presentation():
    from sabueso.core.card_quaternary_history_v1 import expected_result

    zipped = (Path(__file__).parent / "data/quaternary_live_v1.json.gz").read_bytes()
    assert (
        hashlib.sha256(zipped).hexdigest()
        == "af8e80552aa1509a3c36800bd585204a57e1aec1477fe730a5c650113c2ce3f5"
    )
    raw = gzip.decompress(zipped)
    assert (
        hashlib.sha256(raw).hexdigest()
        == "4e5564a842550108de808becce428539599509e8263ea365e6eae2b1a03611ca"
    )
    original = json.loads(raw)
    assert original["producer"]["head"] == "0830de57dd1d027268c98066b130fe42b36a3c39"
    for case in original["cases"].values():
        access = Card.from_dict(case["card"]).access()
        expected = expected_result(access)
        assert expected.result_ref == case["result_ref"]
        _require_matches(case["wire"], expected.wire, "original live quaternary output")


@pytest.mark.parametrize(
    "root_kind", ["question", "topic", "detail", "filter", "sort", "machine"]
)
def test_roundtrip_keeps_original_values_links_order_and_exact_requests(
    root_kind, tmp_path, monkeypatch
):
    explorer = sample().explore()
    view = explorer.answer(TOPIC) if root_kind != "topic" else explorer.view(TOPIC)
    native = view.native_payload
    if root_kind == "detail":
        root = view.items()[0].open()
    elif root_kind == "filter":
        root = view.filter("kind", equals="interface_family_comparison")
    elif root_kind == "sort":
        root = view.sort("kind", descending=True)
    elif root_kind == "machine":
        root = explorer.access.select(
            TOPIC,
            fields=["finding"],
            where={"kind": "interface_family_comparison"},
            order_by={"column": "label"},
        )
    else:
        root = view
    path = tmp_path / "original.json"
    receipt = root.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["format"] == "sabueso.card_exploration@4"
    inert(monkeypatch)
    restored = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert restored.validation["verifier"] == "quaternary_exploration_binding@1"
    assert (
        "interface_site_agreement@3" in restored.validation["verified_scientific_rules"]
    )
    assert restored.native_payload == (
        view.items()[0].open().native_payload if root_kind == "detail" else native
    )
    expected = list(root._entries) if root_kind == "machine" else list(root._selected)
    assert [item._entry.key for item in restored.items()] == [
        entry.key for entry in expected
    ]
    assert [item.item_ref for item in restored.items()] == [
        _handle("XI_", {"result_ref": view.result_ref, "location": entry.location})
        for entry in expected
    ]
    for item in restored.items():
        original_item = view.item(item.item_ref)
        assert item.open().native_payload == original_item._entry.value["item"]
        assert (
            item.explain().native_payload
            == explorer.access._objects[view.result_ref]["explanations"][
                item._entry.key
            ]
        )
        assert item.related().items()
        assert restored.explorer.access.explain(item.item_ref).count
    if root_kind == "machine":
        retained = restored.explorer.access.select(
            TOPIC,
            fields=["finding"],
            where={"kind": "interface_family_comparison"},
            order_by={"column": "label"},
        )
        assert retained.count == 1 and retained.page()["items"][0]["interpretation"]
        assert (
            restored.explorer.access.select(TOPIC).page()["outcome"]["status"]
            == "not_saved"
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"modifier": "LESS_THAN"},
        {"coverage": None, "partner": "uniprot:P60174"},
        {"numbering": "author"},
    ],
)
def test_saved_unknowns_are_original_not_negative_or_newly_admitted(
    kwargs, tmp_path, monkeypatch
):
    view = sample(**kwargs).explore().answer(TOPIC)
    path = tmp_path / "unknown.json"
    view.save(path)
    expected = view.native_payload
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert restored.native_payload == expected
    assert any(
        item.cells["status"].value == "not_computed"
        or item.cells["coordinate_status"].value == "not_computed"
        for item in restored.items()
    )


def test_duplicate_declarations_and_annotation_ordinals_keep_original_order(
    tmp_path, monkeypatch
):
    card = sample()
    row = card.relationships("has_interface_with")[0]
    relation(
        card, "has_interface_with", "uniprot:P52270", row["qualifiers"], suffix="SECOND"
    )
    annotation = deepcopy(card.get("features_positional.family_site")["value"][0])
    field(card, "features_positional.family_site", [annotation, annotation], "InterPro")
    view = card.explore().answer(TOPIC)
    expected = [i.item_ref for i in view.items()]
    path = tmp_path / "duplicate.json"
    view.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert [i.item_ref for i in restored.items()] == expected and len(expected) == 6


@pytest.mark.parametrize(
    "change",
    [
        "classification",
        "positions",
        "reason",
        "rule",
        "source_membership",
        "subject",
        "native_input_pointer",
        "family_ordinal",
    ],
)
def test_resealed_output_changes_cannot_become_original_science(change, tmp_path):
    view = sample().explore().answer(TOPIC)
    path = tmp_path / "altered.json"
    view.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    wire = bundle["objects"][view.result_ref]
    interface = next(k for k in wire["rows"] if k.startswith("interface:"))
    pair = next(k for k in wire["rows"] if k.startswith("comparison:"))
    if change == "classification":
        wire["rows"][interface]["item"]["class"] = "heteromeric"
    elif change == "positions":
        wire["native_payload"]["agreement"][0]["both"] = []
    elif change == "reason":
        wire["rows"][pair]["reason"] = "No uncertainty exists"
    elif change == "rule":
        wire["native_payload"]["rules"][0]["rule"] = "interface_partner_class@99"
    elif change == "source_membership":
        wire["support"][pair]["source_assertions"] = []
    elif change == "subject":
        wire["context"]["card_ref"] = (
            "sabueso:protein:uniprot:P60174@" + wire["context"]["snapshot_id"]
        )
    elif change == "native_input_pointer":
        wire["explanations"][pair]["reference_inputs_location"] = wire["explanations"][
            pair
        ]["source_request_context_location"]
    elif change == "family_ordinal":
        wire["rows"][pair]["item"]["family_site_index"] = 999
    _seal(bundle)
    path.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_historical_source_bundle_does_not_execute_new_interpretation(
    tmp_path, monkeypatch
):
    explorer = sample().explore()
    source = explorer.view("quaternary_structure")
    path = tmp_path / "old-source.json"
    source.save(path)
    assert (
        json.loads(path.read_text(encoding="utf-8"))["format"]
        != "sabueso.card_exploration@4"
    )
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert restored.explorer.answer(TOPIC).outcome["status"] == "not_saved"
    assert (
        restored.explorer.access.select(TOPIC).page()["outcome"]["status"]
        == "not_saved"
    )


@pytest.mark.parametrize("kind", ["links", "explanations"])
def test_resealed_related_operation_cannot_be_swapped_between_original_items(
    kind, tmp_path
):
    view = sample().explore().answer(TOPIC)
    path = tmp_path / "swapped.json"
    view.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    mapping = bundle["navigation"][kind]
    names = [
        key
        for key in mapping
        if json.loads(key)[1] in {i.item_ref for i in view.items()}
    ]
    assert len(names) == 2
    mapping[names[0]], mapping[names[1]] = mapping[names[1]], mapping[names[0]]
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


@pytest.mark.parametrize(
    "mutation",
    [
        "downgrade",
        "manifest",
        "adapter",
        "options",
        "cell_type",
        "policy",
        "schema",
        "members",
    ],
)
def test_new_format_request_and_typed_presentation_cannot_be_resealed_as_original(
    mutation, tmp_path
):
    explorer = sample().explore()
    explorer.answer(TOPIC)
    selection = explorer.access.select(
        TOPIC, where={"kind": "interface_family_comparison"}
    )
    path = tmp_path / "typed.json"
    selection.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    root = bundle["views"][bundle["root_navigation_ref"]]
    ref = selection.result_ref
    if mutation == "downgrade":
        bundle["format"] = "sabueso.card_exploration@3"
        bundle["producer"]["verifier"] = "site_exploration_binding@1"
        bundle["capabilities"]["scientific_saved_adapters"].pop()
    elif mutation == "manifest":
        bundle["scientific_results"].pop(ref)
    elif mutation == "adapter":
        bundle["objects"][ref]["context"]["adapter"] = "quaternary_exploration@99"
    elif mutation == "options":
        bundle["objects"][ref]["context"]["options"] = {"assume_same_axis": True}
    elif mutation == "cell_type":
        next(iter(root["state"]["items"].values()))["cells"]["status"]["value"] = True
    elif mutation == "policy":
        loc = bundle["locations"][root["selection"]["context_location"]["location_ref"]]
        bundle["objects"][loc["result_ref"]]["request"]["selection"]["format"] = (
            "quaternary_access_selection@99"
        )
    elif mutation == "schema":
        root["state"]["schema"]["grain"] = "validated biological assemblies"
    elif mutation == "members":
        root["selected"] = []
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_reidentified_consistent_output_still_requires_original_source_calculation(
    tmp_path,
):
    view = sample().explore().answer(TOPIC)
    path = tmp_path / "consistent.json"
    view.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    old = view.result_ref
    wire = bundle["objects"][old]

    def forge(value):
        if isinstance(value, dict):
            return {
                key: [] if key == "both" and val == [13, 14] else forge(val)
                for key, val in value.items()
            }
        if isinstance(value, list):
            return [forge(v) for v in value]
        if value == "2 shared positions; 1 family-only; 1 interface-only":
            return "0 shared positions; 1 family-only; 1 interface-only"
        return value

    def replace_refs(value, replacements):
        if isinstance(value, dict):
            return {
                replacements.get(key, key): replace_refs(val, replacements)
                for key, val in value.items()
            }
        if isinstance(value, list):
            return [replace_refs(val, replacements) for val in value]
        return replacements.get(value, value) if isinstance(value, str) else value

    bundle = forge(bundle)
    native = deepcopy(bundle["objects"][old]["native_payload"])
    native["rules"] = [
        {k: v for k, v in rule.items() if k != "sabueso_version"}
        for rule in native["rules"]
    ]
    new = _handle(
        "XR_",
        {
            "adapter": "quaternary_exploration@1",
            "focal": wire["context"]["card_ref"],
            "native": native,
        },
    )
    assert new != old
    bundle = replace_refs(bundle, {old: new})
    for _ in range(20):
        repairs = {
            key: _handle("XR_", {"adapter": "literal_metadata@1", "value": val})
            for key, val in bundle["objects"].items()
            if key not in bundle["scientific_results"]
        }
        repairs = {old: new for old, new in repairs.items() if old != new}
        if not repairs:
            break
        bundle = replace_refs(bundle, repairs)
    assert not repairs
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(
        StorageError, match="Original comparison result identity differs"
    ):
        sabueso.read_exploration(path)


def test_mixed_topics_use_their_original_verifiers_and_repeated_save_stays_bounded(
    tmp_path, monkeypatch
):
    explorer = sample().explore()
    source = explorer.view("quaternary_structure")
    structures = explorer.view("structures")
    coverage = explorer.view("coverage")
    contacts = explorer.answer("ligand_site_comparisons")
    view = explorer.answer(TOPIC)
    explorer.access.select(
        TOPIC, fields=["finding"], item_refs=[view.items()[0].item_ref]
    ).save(tmp_path / "mixed.json")
    inert(monkeypatch)
    saved = sabueso.read_exploration(tmp_path / "mixed.json")
    x = saved.explorer
    for topic, original in [
        ("quaternary_structure", source),
        ("structures", structures),
        ("coverage", coverage),
        ("ligand_site_comparisons", contacts),
    ]:
        assert x.view(topic).native_payload == original.native_payload
    previous = None
    for index in range(3):
        p = tmp_path / f"again{index}.json"
        saved.save(p)
        data = json.loads(p.read_text(encoding="utf-8"))
        count = (len(data["views"]), len(data["objects"]))
        if previous is not None:
            assert count == previous
        previous = count
        saved = sabueso.read_exploration(p)


@pytest.mark.parametrize("empty_kind", ["no_interfaces", "filtered", "machine"])
def test_saved_empty_scopes_retain_underlying_context_and_exact_requests(
    empty_kind, tmp_path, monkeypatch
):
    card = sample()
    if empty_kind == "no_interfaces":
        card.relationship_store.store.clear()
    explorer = card.explore()
    view = explorer.answer(TOPIC)
    if empty_kind == "filtered":
        root = view.filter("status", equals="absent_display_value")
    elif empty_kind == "machine":
        root = explorer.access.select(TOPIC, where={"status": "absent_display_value"})
    else:
        root = view
    path = tmp_path / "empty.json"
    root.save(path)
    inert(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert not saved.items()
    assert saved.native_payload == view.native_payload
    if empty_kind == "machine":
        selection = saved.explorer.access.select(
            TOPIC, where={"status": "absent_display_value"}
        )
        assert selection.count == 0
        assert selection.page()["outcome"]["status"] == "ok"
        assert saved.explorer.access.explain(view.items()[0].item_ref).count


def test_original_quantities_and_unit_bindings_are_retained_and_tampering_rejected(
    tmp_path,
):
    card = sample()
    original = card.relationships("has_structure")[0]
    q = deepcopy(original["qualifiers"])
    q["resolution"] = {"value": 2.4, "unit": "angstrom"}
    card.relationship_store.store.pop(original["id"])
    relation(card, "has_structure", "pdb:SYNTHETIC", q)
    view = card.explore().answer(TOPIC)
    path = tmp_path / "quantity.json"
    view.save(path)
    restored = sabueso.read_exploration(path)
    actual = (
        restored.items()[0]
        .open()
        .native_payload["basis"]["pdb:SYNTHETIC"][0]["qualifiers"]["resolution"]
    )
    assert actual == {"value": 2.4, "unit": "angstrom"}
    bundle = json.loads(path.read_text(encoding="utf-8"))
    item = next(
        v
        for v in bundle["objects"][view.result_ref]["rows"].values()
        if v["kind"] == "interface_classification"
    )
    item["item"]["basis"]["pdb:SYNTHETIC"][0]["qualifiers"]["resolution"]["unit"] = (
        "nanometer"
    )
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_saving_uses_the_original_capture_and_does_not_repeat_live_science(
    tmp_path, monkeypatch
):
    module = importlib.import_module("sabueso.core.oligomer")
    original = module.oligomer_view
    calls = []

    def spy(*a, **k):
        calls.append(1)
        return original(*a, **k)

    monkeypatch.setattr(module, "oligomer_view", spy)
    card = sample()
    explorer = card.explore()
    view = explorer.answer(TOPIC)
    expected = deepcopy(view.native_payload)
    card.relationships("has_interface_with")[0]["qualifiers"]["numbering"] = "author"
    path = tmp_path / "original-capture.json"
    view.save(path)
    assert len(calls) == 1
    inert(monkeypatch)
    assert sabueso.read_exploration(path).native_payload == expected


def test_clean_process_reads_original_without_current_science_or_fixture_access(
    tmp_path,
):
    view = sample().explore().answer(TOPIC)
    view.explorer.access.select(TOPIC).save(tmp_path / "independent.json")
    path = (tmp_path / "independent.json").resolve()
    code = """
import importlib,json,socket,sys
from pathlib import Path
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No current science, Card constructor, producer catalog or source inputs')
Card.from_dict=forbidden;socket.socket.connect=forbidden;socket.create_connection=forbidden
for name,methods in {'oligomer':['oligomer_view','interface_scope'],'oligomer_explanation':['explain_oligomer','_explain_oligomer'],'ligand_site_scope':['reference','annotation'],'card_quaternary_exploration':['_materialize','_rows','links','support'],'card_quaternary_access':['materialize','descriptor']}.items():
 m=importlib.import_module('sabueso.core.'+name)
 for method in methods:setattr(m,method,forbidden)
def audit(event,args):
 if event=='open' and isinstance(args[0],str) and 'temp_data' in args[0].replace(chr(92),'/').split('/'):forbidden()
sys.addaudithook(audit)
r=sabueso.read_exploration(sys.argv[1]);x=r.explorer;v=x.answer('quaternary_interpretation')
assert v.native_payload['agreement'][0]['both']==[13,14]
for item in v.items():
 assert item.explain().native_payload['original_interpretation']
 for link in item.related().items():link.open()
page=x.access.select('quaternary_interpretation').page(max_bytes=8192)
assert page['items'] and page['items'][0]['support']
assert x.access.catalog('topics').count
assert 'Original' in str(v.items()[0].explain())
print('PASS independent original quaternary reading')
"""
    with TemporaryDirectory(prefix="sabueso-original-quaternary-") as directory:
        result = subprocess.run(
            [sys.executable, "-c", code, str(path)],
            cwd=directory,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS independent original quaternary reading" in result.stdout


@pytest.mark.parametrize("root_kind", ["human", "machine"])
def test_visited_link_details_remain_saveable_with_original_origin(
    root_kind, tmp_path, monkeypatch
):
    explorer = sample().explore()
    view = explorer.answer(TOPIC)
    finding = view.items()[0]
    finding.open()
    finding.explain()
    links = finding.related()
    # Related navigation creates an empty terminal detail for each original link.
    # Those visited details need their actual quaternary parent on independent read.
    assert links.items()
    for item in links.items():
        item.open()
    root = view if root_kind == "human" else explorer.access.select(TOPIC)
    path = tmp_path / "visited-links.json"
    receipt = root.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert restored.result_ref == view.result_ref
    assert restored.items()
