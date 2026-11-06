"""Original chemical producer receiving, independent reading and hostile edits."""

import gzip
import hashlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from sabueso import read_exploration
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _restore, _seal
from sabueso.core.errors import StorageError

DATA = Path(__file__).parent / "data/chemical_live_v1.json.gz"


@pytest.mark.parametrize(
    "context",
    [
        {"adapter": "chemical_classification_exploration@1"},
        {"adapter": "structure_exploration@1"},
        {"adapter": "ligand_site_exploration@1"},
        {"adapter": "quaternary_exploration@1"},
        {"adapter": "assembly_generation_exploration@1"},
        {"adapter": "assembly_generation_exploration@2"},
        {"adapter": "literal"},
        False,
        None,
        [],
    ],
    ids=[
        "chemical",
        "structure",
        "ligand-site",
        "quaternary",
        "assembly-v1",
        "assembly-v2",
        "literal",
        "false",
        "null",
        "array",
    ],
)
def test_literal_scientific_lookalikes_keep_their_original_values(tmp_path, context):
    explorer = Card(meta={"entity_type": "small_molecule"}).explore()
    explorer.answer("classification")
    opaque = {
        "context": context,
        "native_payload": {"literal": True},
        "explanations": {"original": {"flag": False, "count": 0}},
    }
    literal = explorer._metadata(opaque, "Literal metadata control")
    explanations = next(
        item for item in literal.items() if item.label == "explanations"
    ).open()
    original = explanations.items()[0].open()
    path = tmp_path / "literal-lookalike.json"
    original.save(path)
    saved = read_exploration(path)
    assert saved.native_payload == {"flag": False, "count": 0}
    assert saved.back().back().native_payload == opaque
    assert saved.context["adapter"] == "literal_human@1"


@pytest.mark.parametrize("context", [False, None, []], ids=["false", "null", "array"])
def test_literal_metadata_items_preserve_related_navigation(tmp_path, context):
    explorer = Card(meta={"entity_type": "small_molecule"}).explore()
    explorer.answer("classification")
    opaque = {
        "context": context,
        "items": {"original": {"flag": False, "count": 0}},
    }
    literal = explorer._metadata(opaque, "Literal item metadata control")
    items = next(item for item in literal.items() if item.label == "items").open()
    links = items.items()[0].related()
    path = tmp_path / "literal-item-links.json"
    links.save(path)
    saved = read_exploration(path)
    assert saved.native_payload == links.native_payload
    assert saved.back().native_payload == {"flag": False, "count": 0}
    assert saved.back().back().native_payload == items.native_payload
    assert saved.back().back().back().native_payload == opaque
    assert saved.native_payload["source_location"]["kind"] == "result"
    assert saved.native_payload["links"] == []


def test_literal_metadata_cannot_claim_a_scientific_manifest(tmp_path):
    explorer = Card(meta={"entity_type": "small_molecule"}).explore()
    explorer.answer("classification")
    opaque = {
        "context": {"adapter": "chemical_classification_exploration@1"},
        "native_payload": {"literal": True},
    }
    path = tmp_path / "metadata-manifest.json"
    explorer._metadata(opaque, "Literal metadata control").save(path)
    bundle = json.loads(path.read_text())
    ref = next(key for key, value in bundle["objects"].items() if value == opaque)
    bundle["scientific_results"][ref] = deepcopy(
        next(iter(bundle["scientific_results"].values()))
    )
    with pytest.raises(StorageError, match="literal metadata object cannot"):
        _restore(_seal(bundle), None)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        pytest.fail("Saved receiving cannot query sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def originals():
    raw = DATA.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "1e0a9a01da5c1d1118a115b12b3393dd886a3e447cda4a49e58cd8c514ff9ac1"
    )
    return json.loads(gzip.decompress(raw))


@pytest.fixture
def card(originals):
    return Card.from_dict(deepcopy(originals["cases"]["pga"]["card"]))


@pytest.mark.parametrize("name", ["pga", "vincristine"])
def test_original_producer_wire_rows_and_sources_survive_saving(
    originals, name, tmp_path
):
    original = originals["cases"][name]
    card = Card.from_dict(deepcopy(original["card"]))
    explorer = card.explore()
    human = explorer.answer("classification")
    assert explorer.access._objects[human.result_ref] == original["wire"]
    machine = explorer.access.select(
        "chemical_classification", fields=["term_ref", "assignment"]
    )
    before = card.to_dict()
    path = tmp_path / "chemical.json"
    receipt = human.save(path)
    saved = read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert saved.native_payload == original["native"]
    assert [item.item_ref for item in saved.items()] == [
        item.item_ref for item in human.items()
    ]
    assert saved.rows() == human.rows()
    assert human.exclusions == saved.exclusions == []
    assert (
        saved.validation["chemical_classification"]
        == "original_frozen_v1_consistency_verified"
    )
    for item, live in zip(saved.items(), human.items()):
        assert item.open().native_payload == live.open().native_payload
        assert item.explain().native_payload == live.explain().native_payload
        links = item.related()
        assert links.native_payload == live.related().native_payload
        assert links.back().view_ref == saved.view_ref
        for source in links.items():
            assert source.open().back().view_ref == links.view_ref
    selected = saved.explorer.access.select(
        "chemical_classification", fields=["term_ref", "assignment"]
    )
    assert selected.selection_ref == machine.selection_ref
    assert [item["cells"] for item in selected.page()["items"]] != []
    assert saved.explorer.answer("classification").native_payload == original["native"]
    assert saved.explorer.view("classification").native_payload == original["native"]
    assert card.to_dict() == before


@pytest.mark.parametrize("compression", ["none", "gzip", "zstd"])
def test_filtered_unknown_scope_and_repeat_saving(card, tmp_path, compression):
    card.get("annotations.chemical_roles")["value"][0]["direct"] = (
        "synthetic-unrecognized"
    )
    explorer = card.explore()
    original = explorer.answer("classification")
    filtered = original.filter("assignment", equals="unknown").sort("label").table()
    path = tmp_path / "filtered"
    filtered.save(path, compression=compression)
    saved = read_exploration(path)
    assert saved.outcome == filtered.outcome and saved.outcome["status"] == "partial"
    assert saved.native_payload == original.native_payload
    assert [i.label for i in saved.items()] == [i.label for i in filtered.items()]
    assert "Partly supported" in str(saved)
    saved.save(tmp_path / "again", compression=compression)
    again = read_exploration(tmp_path / "again")
    assert again.native_payload == saved.native_payload
    assert again.rows() == saved.rows()


@pytest.mark.parametrize(
    "where", [{"application": None}, {"application": False}, {"assignment": "direct"}]
)
def test_exact_machine_membership_projection_and_not_saved_query(card, tmp_path, where):
    access = card.access()
    selection = access.select(
        "chemical_classification",
        fields=[],
        where=where,
        order_by={"column": "label", "descending": True},
    )
    path = tmp_path / "machine.json"
    selection.save(path)
    saved = read_exploration(path)
    actual = saved.explorer.access.select(
        "chemical_classification",
        fields=[],
        where=where,
        order_by={"column": "label", "descending": True},
    )
    assert actual.selection_ref == selection.selection_ref
    assert actual.count == selection.count
    assert [x["item_ref"] for x in actual.page()["items"]] == [
        x["item_ref"] for x in selection.page()["items"]
    ]
    assert all(
        frame["cells"] == {} and frame["interpretation"]["scope"]
        for frame in actual.page()["items"]
    )
    missing = saved.explorer.access.select(
        "chemical_classification", fields=["label"], where=where
    )
    assert missing.page()["outcome"]["status"] == "not_saved"


def test_fresh_reader_forbids_card_current_science_and_current_profiles(card, tmp_path):
    explorer = card.explore()
    root = explorer.answer("classification")
    explorer.access.select("chemical_classification", fields=["term_ref"])
    path = tmp_path / "saved.json"
    root.save(path)
    script = """
import sys, socket
import sabueso
from sabueso.core.card import Card
import sabueso.core.card_chemical_access as live
import sabueso.core.card_chemical_exploration as human
import sabueso.core.card_exploration_profiles as profiles
import sabueso.core.chemical_classification as native

def forbidden(*a, **k): raise AssertionError("No live scientific reading, Card construction, catalogue or source query")
Card.__init__ = Card.chemical_classification = forbidden
live.interpret = live.materialize = human.view = human.opening = human.display_row = forbidden
native.chemical_classification = forbidden
profiles.NATURE_TOPICS = profiles.QUESTIONS = {}
socket.socket.connect = socket.create_connection = forbidden
view = sabueso.read_exploration(sys.argv[1])
assert view.native_payload["rule"] == "chemical_classification_context@1"
assert "carboxyalkyl phosphate" in str(view)
for item in view.items():
 assert item.explain().native_payload
 for source in item.related().items(): source.open()
selection = view.explorer.access.select("chemical_classification", fields=["term_ref"])
assert selection.count == 4
view.save(sys.argv[2])
print("independent original chemical reading passed")
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(path), str(tmp_path / "resaved.json")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "independent original chemical reading passed" in result.stdout


@pytest.mark.parametrize(
    "change",
    [
        "native",
        "flag",
        "source",
        "order",
        "rule",
        "membership",
        "support",
        "scope",
        "manifest",
    ],
)
def test_resealed_changes_do_not_substitute_science_or_selection(
    card, tmp_path, change
):
    root = card.explore().answer("classification")
    path = tmp_path / "original.json"
    root.save(path)
    bundle = json.loads(path.read_text())
    assert bundle["format"] == "sabueso.card_exploration@15"
    record = bundle["views"][bundle["root_navigation_ref"]]
    ref = record["selection"]["scientific_result_ref"]
    wire = bundle["objects"][ref]
    if change == "native":
        wire["native_payload"]["status"] = "empty"
    elif change == "flag":
        next(value for value in wire["rows"].values() if value["application"] is False)[
            "application"
        ] = 0
    elif change == "source":
        next(iter(wire["native_payload"]["input_source_assertions"].values()))[
            "source"
        ]["name"] = "synthetic"
    elif change == "order":
        record["selection"]["entries"].reverse()
    elif change == "rule":
        wire["native_payload"]["rule"] = "chemical_classification_context@99"
    elif change == "membership":
        record["selected"].pop()
    elif change == "support":
        wire["support"][next(iter(wire["support"]))]["source_memberships"].clear()
    elif change == "scope":
        record["flags"]["_request"] = {
            "question": "classification",
            "topic": "classification",
            "options": {"infer_activity": True},
        }
    elif change == "manifest":
        bundle["scientific_results"].clear()
    _seal(bundle)
    with pytest.raises(StorageError):
        _restore(bundle, None)


def test_explicit_shared_representation_keeps_the_complete_new_semantics(
    card, tmp_path, monkeypatch
):
    import sabueso.core.card_exploration_shared_values_v2 as codec

    original = codec.pack
    monkeypatch.setattr(
        codec,
        "pack",
        lambda bundle, limit: original(bundle, limit, threshold=0, min_saving=0),
    )
    root = card.explore().answer("classification")
    path = tmp_path / "shared.json"
    root.save(path)
    payload = json.loads(path.read_text())
    assert payload["format"] == "sabueso.card_exploration@16"
    saved = read_exploration(path)
    assert saved.native_payload == root.native_payload
    assert saved.rows() == root.rows()


@pytest.mark.parametrize(
    "value,status", [(None, "unknown"), ([], "empty"), (False, "unknown")]
)
def test_original_empty_null_and_malformed_fields_do_not_become_source_absence(
    card, tmp_path, value, status
):
    for path in ("annotations.chemical_roles", "annotations.chemical_classes"):
        card.get(path)["value"] = value
    root = card.explore().view("classification")
    root.save(tmp_path / "unknown.json")
    saved = read_exploration(tmp_path / "unknown.json")
    assert saved.outcome["status"] == status
    assert saved.native_payload == root.native_payload
    assert "source-wide absence" in str(saved)


def test_mixed_supplied_natures_keep_their_original_scope_and_sources(card, tmp_path):
    from sabueso.core.relationship_store import make_relationship
    from sabueso.core.source_assertion_store import make_source_assertion

    # Deliberately synthetic target/association declarations test navigation,
    # not a claim about this molecule or either real-world biological entity.
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:P52270"}
    )
    disease = Card(
        meta={"entity_type": "disease", "card_id": "sabueso:disease:mondo:0000001"}
    )
    anchor = card.id.removeprefix("sabueso:small_molecule:")
    for subject, predicate, obj in (
        ("uniprot:P52270", "engages", anchor),
        (anchor, "investigated_for", "mondo:0000001"),
    ):
        value = {"subject_ref": subject, "object_ref": obj, "qualifiers": {}}
        source = make_source_assertion(
            "relationships." + predicate,
            value,
            "synthetic",
            "receiving-only",
            "synthetic",
            subject_ref=subject,
        )
        card.source_assertion_store.add(source)
        card.relationship_store.add(
            make_relationship(subject, predicate, obj, {}, [source["id"]])
        )
    explorer = card.explore(related_cards=[protein, disease])
    chemical = explorer.answer("classification")
    relationships = explorer.inspect(
        locator=explorer.access._card_location(
            segments=[{"type": "Key", "value": "relationship_store"}]
        )
    )
    entered = []
    for item in relationships.items():
        if item._entry.value["predicate"] not in ("engages", "investigated_for"):
            continue
        links = item.related()
        role = "subject" if item._entry.value["predicate"] == "engages" else "object"
        target = next(
            link for link in links.items() if link._entry.value["role"] == role
        )
        destination = target.open()
        entered.append(
            destination.explorer.view(
                "function"
                if destination.explorer.profile == "protein"
                else "definition"
            )
        )
    assert {view.explorer.profile for view in entered} == {"protein", "disease"}
    chemical.save(tmp_path / "mixed.json")
    saved = read_exploration(tmp_path / "mixed.json")
    assert saved.native_payload == chemical.native_payload
    natures = {
        view.explorer.profile
        for view in saved.explorer._session["views"].values()
        if view.explorer is not None
    }
    assert natures >= {"protein", "disease", "small_molecule"}
    assert saved.explorer.profile == "small_molecule"


def test_focused_presentation_keeps_original_member_payload(card, tmp_path):
    root = card.explore().answer("classification")
    detail = root.items()[1].open()
    shown = (
        detail.summary()
        .table()
        .sort("label")
        .filter("label", equals="no matching label")
    )
    shown.save(tmp_path / "focused.json")
    saved = read_exploration(tmp_path / "focused.json")
    assert not saved.items()
    assert saved.native_payload == detail.native_payload
    assert saved.back().back().back().back().native_payload == detail.native_payload
