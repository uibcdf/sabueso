"""Scientific routes remain visible without changing retained navigation order."""

import gzip
import hashlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.card_navigation_preview_v1 import KEY, RULE
from sabueso.core.errors import StorageError


def forbidden(*args, **kwargs):
    raise AssertionError("Preview must not acquire data or evaluate science")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(Card, "assembly_generation", forbidden)


def navigation(*, nature="protein", missing=12):
    identities = {
        "protein": "sabueso:protein:uniprot:P52270",
        "small_molecule": "sabueso:small_molecule:chembl:CHEMBL110",
        "disease": "sabueso:disease:mondo:MONDO:0014221",
        "unrecognized": "sabueso:unrecognized:synthetic:example",
    }
    card = Card(meta={"card_id": identities[nature], "entity_type": nature})
    if nature == "protein":
        card.sections.setdefault("identifiers", {})["uniprot"] = {
            "value": "P52270",
            "source_assertion_ids": [],
        }
    card.relationship_store.add(
        {
            "id": "RL_SYNTHETIC_PREVIEW",
            "subject_ref": identities[nature].split(":", 2)[2],
            "predicate": "has_structure",
            "object_ref": "pdb:1SUX",
            "qualifiers": {
                "ligands": [],
                "assemblies": [],
                "chains": ["SYNTHETIC_CHAIN"],
                "author_numbering": {},
            },
            "source_assertion_ids": [
                f"SA_SYNTHETIC_MISSING_{i}" for i in range(missing)
            ],
        }
    )
    explorer = card.explore()
    return (
        explorer.inspect(locator=explorer._location("relationship_store"))
        .items()[0]
        .related()
    )


def displayed_indices(view):
    return [
        int(line.split(" | ")[0])
        for line in str(view.table()).splitlines()
        if line.split(" | ")[0].isdecimal()
    ]


@pytest.mark.parametrize("missing", [0, 2, 12, 60])
def test_question_and_destinations_visible_with_original_indices(missing):
    links = navigation(missing=missing)
    original = [i.item_ref for i in links.items()]
    payload = deepcopy(links.native_payload)
    text, html = str(links.table()), links.table()._repr_html_()
    question = links.filter("role", equals="question").items()[0]
    index = next(
        i for i, item in enumerate(links.items()) if item.item_ref == question.item_ref
    )
    indices = displayed_indices(links)
    assert indices[0] == index
    assert question.label in text and question.label in html
    assert len(indices) == min(10, len(links.items()))
    assert len(set(indices)) == len(indices)
    assert "Questions: 1/1 shown" in text
    assert f"Source links: {min(missing, 2)}/{missing} shown" in text
    assert "Indices refer to items()[i]" in text
    assert [i.item_ref for i in links.items()] == original
    assert links.native_payload == payload
    assert not links._explorer.access._scientific_cache
    # Display index refers to the actual original item, including unavailable links.
    assert links.items()[indices[0]].item_ref == question.item_ref
    assert (
        question.open().request["options"]["relationship_id"] == "RL_SYNTHETIC_PREVIEW"
    )


@pytest.mark.parametrize("nature", ["small_molecule", "disease", "unrecognized"])
def test_generic_destinations_are_visible_for_other_card_natures(nature):
    links = navigation(nature=nature)
    indices = displayed_indices(links)
    assert [links.items()[i].cells["role"].value for i in indices[:2]] == [
        "subject",
        "object",
    ]
    assert "Questions: 0/0 shown" in str(links)
    assert len(links.items()) == 14


def test_source_filter_sort_and_full_literal_access_keep_their_semantics():
    links = navigation()
    sources = links.filter("role", equals="source").sort("label", descending=True)
    refs = [i.item_ref for i in sources.items()]
    assert displayed_indices(sources) == list(range(10))
    assert "Source links: 10/12 shown" in str(sources)
    assert [i.item_ref for i in sources.items()] == refs
    question = links.filter("role", equals="question")
    assert displayed_indices(question) == [0]
    literal = links.explorer.access.read(question.items()[0].payload_location)
    page = literal.page(max_bytes=8192)
    assert page["page"]["returned"] > 0


def test_many_questions_have_an_explicit_complete_access_route():
    from sabueso.core.card_context_navigation import _link_view

    explorer = Card().explore()
    original = explorer.inspect()
    questions = [
        {
            "role": "question",
            "label": f"Synthetic question {i}",
            "target_ref": "region_coverage",
            "rule": "retained_context_links@3",
            "support": [],
            "candidates": [],
            "paths": [],
            "blocked_paths": [],
            "availability": "missing_prerequisite",
            "annotation_context": {"reason": "Synthetic unavailable question"},
        }
        for i in range(14)
    ]
    links = _link_view(explorer, questions, original, "Synthetic questions")
    assert "Questions: 10/14 shown" in str(links)
    assert "showing 10, 4 more" in str(links)
    assert len(links.filter("role", equals="question").items()) == 14
    assert displayed_indices(links) == list(range(10))


def test_current_saved_policy_preserves_preview_and_repeat_save(tmp_path, monkeypatch):
    links = navigation()
    indices = displayed_indices(links)
    native = links.native_payload
    refs = [i.item_ref for i in links.items()]
    path, second = tmp_path / "current.json", tmp_path / "same.json"
    receipt = links.save(path)
    links.save(second)
    assert path.read_bytes() == second.read_bytes()
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["presentation_metadata"][KEY] == RULE
    monkeypatch.setattr(Card, "__init__", forbidden)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert displayed_indices(saved) == indices
    assert saved.native_payload == native
    assert [i.item_ref for i in saved.items()] == refs
    assert (
        saved.filter("role", equals="question").items()[0].open().outcome["status"]
        == "not_saved"
    )


def test_genuine_old_v6_keeps_prefix_without_backfill(tmp_path):
    packed = (
        Path(__file__).parent / "data/card_navigation_prefix_v6.json.gz"
    ).read_bytes()
    assert (
        hashlib.sha256(packed).hexdigest()
        == "27626edb623e9a7c3bb63ffb95db21f943f4e47d75504e43a36350720380d1a1"
    )
    raw = gzip.decompress(packed)
    assert (
        hashlib.sha256(raw).hexdigest()
        == "5f7f31068654ac8900a0b34a8020079a6938dafb516e1b3501c140bb0f344611"
    )
    path = tmp_path / "original.json"
    path.write_bytes(raw)
    saved = sabueso.read_exploration(path)
    assert displayed_indices(saved) == list(range(10))
    label = saved.filter("role", equals="question").items()[0].label
    assert label not in str(saved)
    assert "Navigation preview" not in str(saved)
    again = tmp_path / "again.json"
    saved.save(again)
    assert (
        KEY
        not in json.loads(again.read_text(encoding="utf-8"))["presentation_metadata"]
    )
    assert path.read_bytes() == raw
    fresh = saved.explorer.start_new()
    assert fresh._session["presentation_metadata"][KEY] == RULE


@pytest.mark.parametrize(
    "value", ["question_destination_preview@99", None, True, {}, []]
)
def test_unknown_named_policy_is_refused_even_after_resealing(tmp_path, value):
    path = tmp_path / "changed.json"
    navigation(missing=0).save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bundle["presentation_metadata"][KEY] = value
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError, match="navigation preview policy"):
        sabueso.read_exploration(path)
