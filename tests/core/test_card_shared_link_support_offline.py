"""Complete shared support, original destinations and inert format11 reading."""

import gzip
import hashlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_context_navigation import _link_view
from sabueso.core.card_context_support_v1 import RULE, SUPPORT_RULE, verify_links
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion


def forbidden(*args, **kwargs):
    raise AssertionError("No acquisition, Card rebuilding or live navigation producer")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def workload(nature="protein", *, count=3, missing=True):
    card = Card(
        meta={"card_id": f"sabueso:{nature}:custom:synthetic", "entity_type": nature}
    )
    refs = []
    for index in range(count):
        record = make_source_assertion(
            "names.canonical_name",
            "Synthetic",
            "Synthetic",
            f"record-{index}",
            "2026-11-05",
        )
        refs.append(record["id"])
        if not missing or index != count - 1:
            card.source_assertion_store.add(record)
    card.sections["names"] = {
        "canonical_name": {"value": "Synthetic", "source_assertion_ids": refs}
    }
    view = card.explore().inspect("names")
    return card, view, view.items()[0]


@pytest.mark.parametrize("nature", ["protein", "small_molecule", "disease", "other"])
def test_all_natures_keep_complete_support_destinations_and_missing_scope(nature):
    card, view, item = workload(nature)
    before, support = card.to_dict(), item.support
    links = item.related()
    assert links.native_payload["rule"] == RULE
    assert len(links.items()) == 3
    assert links.back().back() is view
    for source in links.items():
        member = source.support[0]
        assert member["rule"] == SUPPORT_RULE
        assert member["statement_id"] == source._entry.value["target_ref"]
        original = links.explorer.inspect(
            locator=member["support_location"]
        ).native_payload
        assert original["source_location"] == item.payload_location
        assert original["support"] == support
        if source.cells["availability"].value == "available":
            assert source.open().native_payload == card.source_assertion_store.get(
                member["statement_id"]
            )
        else:
            assert source.cells["availability"].value == "missing_prerequisite"
        member["statement_id"] = "caller mutation"
        assert source.support[0]["statement_id"] != "caller mutation"
    assert item.support == support
    assert card.to_dict() == before


def test_one_reference_keeps_its_original_policy():
    _, _, item = workload(count=1, missing=False)
    assert item.related().native_payload["rule"] == "retained_context_links@2"


def test_saved_history_and_agent_original_support_remain_inert(tmp_path, monkeypatch):
    card, view, item = workload()
    before = card.to_dict()
    links = item.related()
    first = links.items()[0]
    source = first.open()
    path = tmp_path / "shared.json"
    receipt = source.save(path)
    bundle = json.loads(path.read_text("utf-8"))
    assert bundle["format"] == "sabueso.card_exploration@11"
    expected = source.native_payload
    import sabueso.core.card_context_navigation as navigation
    import sabueso.core.card_context_support_v1 as shared

    monkeypatch.setattr(navigation, "related", forbidden)
    monkeypatch.setattr(shared, "compact_related", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert saved.native_payload == expected
    assert saved.validation["verifier"] == "shared_link_support_binding@1"
    retained = saved.back()
    assert retained.native_payload == links.native_payload
    assert retained.back().back().native_payload == view.native_payload
    member = retained.items()[0].support[0]
    accessed = saved.explorer.access.read(member["support_location"])
    frame = accessed.page(limit=8, max_bytes=16384)
    assert any(row["key"] == "support" for row in frame["items"])
    assert (
        saved.explorer.inspect(locator=member["support_location"]).native_payload[
            "support"
        ]
        == item.support
    )
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "change", ["membership", "order", "basis", "availability", "destination"]
)
def test_reidentified_semantic_forgeries_fail_original_support_validation(change):
    _, _, item = workload()
    links = item.related()
    payload = links.native_payload
    rows = deepcopy(payload["links"])
    location = payload["support_location"]
    if change == "membership":
        rows[0]["support"][0]["statement_id"] = rows[1]["target_ref"]
    elif change == "order":
        rows.reverse()
    elif change == "basis":
        original = deepcopy(links.explorer.access._resolve(location)[0])
        original["support"][0]["statements"].pop()
        lookup = links.explorer.access._object_location(original)
        _, location = links.explorer.access._resolve(lookup)
        for row in rows:
            row["support"][0]["support_location"] = location
    elif change == "availability":
        rows[-1]["availability"] = "available"
    else:
        rows[0]["candidates"][0]["location"] = rows[1]["candidates"][0]["location"]
    forged = _link_view(
        links.explorer,
        rows,
        links.back(),
        "Forged shared support",
        source_location=payload["source_location"],
        support_location=location,
        rule=RULE,
    )
    assert forged.result_ref != links.result_ref
    with pytest.raises(StorageError):
        verify_links(forged)


def test_resealed_presentation_support_edit_is_still_refused(tmp_path):
    _, _, item = workload()
    path = tmp_path / "forged.json"
    item.related().save(path)
    bundle = json.loads(path.read_text("utf-8"))
    root = bundle["views"][bundle["root_navigation_ref"]]
    next(iter(root["state"]["items"].values()))["support"][0]["statement_id"] = (
        "foreign"
    )
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError, match="support"):
        sabueso.read_exploration(path)


def test_literal_adapter_lookalike_cannot_supply_native_source_support():
    card, _, _ = workload(count=2, missing=False)
    relationship = make_relationship(
        "custom:synthetic",
        "associated_with",
        "custom:target",
        source_assertion_ids=[
            source["id"] for source in card.source_assertion_store.to_list()
        ],
    )
    card.relationship_store.add(relationship)
    explorer = card.explore()
    location = {
        **explorer._location("relationship_store"),
        "segments": [
            {"type": "Key", "value": "relationship_store"},
            {"type": "Record", "value": relationship["id"]},
        ],
    }
    record = explorer.inspect(locator=location)
    item = next(row for row in record.items() if row.label == "predicate")
    valid = item.related()
    support = item.support
    fake = explorer._metadata(
        {
            "context": {
                "adapter": "structure_exploration@1",
                "card_ref": explorer.context["card_ref"],
            },
            "items": {relationship["id"]: {"opaque": True}},
            "support": {relationship["id"]: support[0]},
        },
        "Synthetic literal adapter lookalike",
    )
    fake_item = (
        next(row for row in fake.items() if row.label == "items").open().items()[0]
    )
    assert fake_item.support[0]["basis"] == "navigation_metadata"
    source = fake_item.payload_location
    lookup = explorer.access._object_location(
        {"rule": SUPPORT_RULE, "source_location": source, "support": support}
    )
    _, shared = explorer.access._resolve(lookup)
    rows = deepcopy(valid.native_payload["links"])
    for row in rows:
        row["support"][0]["support_location"] = shared
    forged = _link_view(
        explorer,
        rows,
        fake_item.open(),
        "Reidentified literal lookalike",
        source_location=source,
        support_location=shared,
        rule=RULE,
    )
    with pytest.raises(StorageError, match="complete original"):
        verify_links(forged)


def test_shared_support_and_original_range_question_share_one_saved_session(
    tmp_path, monkeypatch
):
    original = json.loads(
        gzip.decompress(
            (
                Path(__file__).parent
                / "data/model_range_alias_navigation_original_v1.json.gz"
            ).read_bytes()
        )
    )
    card = Card.from_dict(next(iter(original["cards"].values()))["data"])
    synthetic, _, _ = workload()
    card.sections["names"] = synthetic.sections["names"]
    for source in synthetic.source_assertion_store.to_list():
        card.source_assertion_store.add(source)
    explorer = card.explore()
    shared = explorer.inspect("names").items()[0].related()
    assert shared.native_payload["rule"] == RULE
    model = explorer.answer("predicted_models").items()[0].related()
    question = model.filter("role", equals="question").items()[0]
    assert question._entry.value["rule"] == "retained_context_links@6"
    expected = question._entry.value
    path = tmp_path / "mixed.json"
    model.save(path)
    assert (
        json.loads(path.read_text("utf-8"))["format"] == "sabueso.card_exploration@11"
    )
    import sabueso.core.card_context_support_v1 as shared_support

    monkeypatch.setattr(shared_support, "compact_related", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    saved = sabueso.read_exploration(path)
    assert saved.filter("role", equals="question").items()[0]._entry.value == expected


def test_multiple_source_endpoint_preserves_ambiguous_captured_revisions(tmp_path):
    owner, _, _ = workload(missing=False, count=2)
    refs = []
    for index in range(2):
        source = make_source_assertion(
            "relationships.associated_with",
            "custom:target",
            "Synthetic",
            f"edge-{index}",
            "2026-11-05",
        )
        owner.source_assertion_store.add(source)
        refs.append(source["id"])
    relationship = make_relationship(
        "custom:synthetic",
        "associated_with",
        "custom:target",
        source_assertion_ids=refs,
    )
    owner.relationship_store.add(relationship)
    targets = [
        Card(
            meta={"card_id": "sabueso:protein:custom:target", "entity_type": "protein"},
            sections={
                "names": {"canonical_name": {"value": name, "source_assertion_ids": []}}
            },
        )
        for name in ("First", "Second")
    ]
    explorer = owner.explore(related_cards=targets)
    location = {
        **explorer._location("relationship_store"),
        "segments": [
            {"type": "Key", "value": "relationship_store"},
            {"type": "Record", "value": relationship["id"]},
        ],
    }
    record = explorer.inspect(locator=location)
    links = next(item for item in record.items() if item.label == "predicate").related()
    assert links.native_payload["rule"] == RULE
    endpoint = links.filter("role", equals="object").items()[0]
    assert endpoint.cells["availability"].value == "ambiguous"
    choices = endpoint.open()
    assert len(choices.items()) == 2
    path = tmp_path / "ambiguous.json"
    choices.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == choices.native_payload
    assert (
        len(
            {
                row._entry.value["candidates"][0]["location"]["snapshot_id"]
                for row in saved.items()
            }
        )
        == 2
    )

    from sabueso.core.card_exploration_verification_v11 import _verify_links

    forged = deepcopy(choices.native_payload["links"])
    forged[0]["support"][0]["statement_id"] = "foreign"
    forged_view = _link_view(explorer, forged, links, "Forged ambiguous support")
    with pytest.raises(StorageError, match="Candidate shared support"):
        _verify_links(forged_view)


def test_original_candidate_capsule_reads_in_a_fresh_inert_process():
    original = Path(__file__).parent / "data/shared_link_support_original_v1.json.gz"
    raw = original.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "2f0aa6493cb020407e077fb0ece2992eb0057b5da7a317fcfc4e88a0ce609668"
    )
    assert (
        hashlib.sha256(gzip.decompress(raw)).hexdigest()
        == "b6986684fe7918b2686e1fb0869b6c1921fc63e5f89977abf2ac09e6ad52bdb8"
    )
    script = r"""
import socket,sys
import sabueso
from sabueso.core.card import Card
import sabueso.core.card_context_navigation as navigation
import sabueso.core.card_context_support_v1 as shared
def forbidden(*a,**k):raise AssertionError('No acquisition, Card rebuilding or current producer')
socket.socket.connect=forbidden;socket.create_connection=forbidden
Card.__init__=forbidden;Card.from_dict=forbidden
navigation.related=forbidden;shared.compact_related=forbidden
saved=sabueso.read_exploration(sys.argv[1],expected_digest='sha256:bc753609fb982ec4e3f23746628a8680f0d7c38b5325d6f9cad4b980d8254573')
assert saved.validation['verifier']=='shared_link_support_binding@1'
assert len(saved.items())==3
assert sum(i.cells['availability'].value=='available' for i in saved.items())==2
member=saved.items()[0].support[0]
full=saved.explorer.inspect(locator=member['support_location']).native_payload
assert len(full['support'][0]['statements'])==3
assert saved.items()[0].open().native_payload['field_path']=='names.canonical_name'
print('PASS original format11 complete support, missing member and source destination')
"""
    with TemporaryDirectory() as directory:
        result = subprocess.run(
            [sys.executable, "-c", script, str(original.resolve())],
            cwd=directory,
            capture_output=True,
            text=True,
            check=True,
        )
    assert "PASS original format11" in result.stdout


def test_visible_size_refusal_and_conscious_override_preserve_destination(tmp_path):
    _, _, item = workload()
    path = tmp_path / "existing.json"
    path.write_bytes(b"caller-owned")
    with pytest.raises(ArgumentError, match="max_decoded_bytes"):
        item.related().save(path, overwrite=True, max_decoded_bytes=1024)
    assert path.read_bytes() == b"caller-owned"
    item.related().save(path, overwrite=True, max_decoded_bytes=None)
    assert (
        sabueso.read_exploration(path, max_decoded_bytes=None).validation["integrity"]
        == "verified"
    )
    assert (
        json.loads(path.read_text("utf-8"))["format"] == "sabueso.card_exploration@11"
    )
