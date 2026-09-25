"""Versioned cards in the knowledge store (uibcdf/sabueso#7, #27).

A pinned reference resolves to the exact state that was saved, or fails; it never
returns another state of the card. SourceAssertions and relationships are rows shared
by the snapshots that hold them, and relationships can be searched from their object.
"""

import copy
import json
import sqlite3
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import parse_ref, snapshot_id
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.interpro import FixtureInterProClient
from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient

TIM_DOMAIN = "interpro:IPR000652"


def _build(accession):
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        profile="structural_baseline@1",
        chembl_client=FixtureChEMBLClient("temp_data"),
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        interpro_client=FixtureInterProClient("temp_data"),
    )
    return card


@pytest.fixture(scope="module")
def tctim():
    return _build("P52270")


@pytest.fixture(scope="module")
def hstim():
    return _build("P60174")


@pytest.fixture(scope="module")
def molecule():
    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    return single_molecule_card(
        chembl={
            "retrieved_at": "2026-02-01",
            "molecules": {"CHEMBL90555": load("temp_data/CHEMBL90555.json")},
        },
        pubchem={
            "retrieved_at": "2026-02-02",
            "compounds": {"5978": load("temp_data/5978.json")},
        },
    )


def _variant(card, outcome):
    """The same card after a rebuild in which a curated assertion's outcome changed.

    How the outcome changed (a source that started to state the same value) is covered
    in test_curation_store_offline.py; here only the stored state matters.
    """
    data = card.to_dict()
    data["quality"] = copy.deepcopy(data["quality"])
    data["quality"]["curation"] = [
        {"source_assertion_id": "SA_literature_example", "outcome": outcome}
    ]
    data.pop("quantities")
    from sabueso.core.quantities import seal

    data["quantities"] = seal(data)
    return Card.from_dict(data)


# --- snapshot identity ----------------------------------------------------------------------


def test_the_snapshot_id_is_the_content_address_of_the_stored_card(tctim):
    sid = tctim.snapshot_id()
    assert sid.startswith("sha256:") and len(sid) == len("sha256:") + 64
    # Rebuilt from the same sources, through JSON, or with its rows in another order.
    assert _build("P52270").snapshot_id() == sid
    data = json.loads(json.dumps(tctim.to_dict()))
    assert Card.from_dict(data).snapshot_id() == sid
    data["source_assertion_store"].reverse()
    data["relationship_store"].reverse()
    assert snapshot_id(data) == sid
    # Any change to what the card states is another snapshot.
    assert _variant(tctim, "new").snapshot_id() != sid


def test_references_are_parsed_strictly():
    sid = "sha256:" + "a" * 64
    assert parse_ref(f"sabueso:protein:uniprot:P52270@{sid}#SA_UniProt_x") == (
        "sabueso:protein:uniprot:P52270",
        sid,
        "SA_UniProt_x",
    )
    for bad in (
        "uniprot:P52270",
        "sabueso:protein:uniprot:P52270@sha256:abc",
        "sabueso:protein:uniprot:P52270@",
        "sabueso:protein:uniprot:P52270#SA_UniProt_x",  # an item needs a pin
        f"sabueso:protein:uniprot:P52270@{sid}#nothing",
    ):
        with pytest.raises(StorageError):
            parse_ref(bad)


# --- pinned reads ---------------------------------------------------------------------------


def test_a_card_comes_back_exactly_as_it_was_saved(tmp_path, tctim, molecule):
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    for card in (tctim, molecule):
        ref = store.save(card)
        assert ref == card.pinned_ref()
        assert store.load(ref).to_dict() == card.to_dict()
        assert store.load(card.id).to_dict() == card.to_dict()


def test_an_older_pin_keeps_its_state_after_a_newer_one_is_saved(tmp_path, tctim):
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    before = _variant(tctim, "new")
    after = _variant(tctim, "corroborates")
    first = store.save(before, note="first build")
    second = store.save(after, note="rebuilt against a newer release")
    assert first != second

    assert store.load(first).quality["curation"][0]["outcome"] == "new"
    assert store.load(second).quality["curation"][0]["outcome"] == "corroborates"
    assert store.load(tctim.id).to_dict() == after.to_dict()  # unpinned: the latest

    history = store.history(tctim.id)
    assert [h["ref"] for h in history] == [first, second]
    assert [h["note"] for h in history] == [
        "first build",
        "rebuilt against a newer release",
    ]
    # Saving the latest state again adds nothing; going back to an older one is a
    # new revision pointing at the stored snapshot.
    assert store.save(after) == second
    assert len(store.history(tctim.id)) == 2
    assert store.save(before) == first
    assert [h["ref"] for h in store.history(tctim.id)] == [first, second, first]


def test_a_missing_pin_fails_and_never_returns_the_latest(tmp_path, tctim, hstim):
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(tctim)
    hs = store.save(hstim)
    absent = f"{tctim.id}@sha256:{'0' * 64}"
    with pytest.raises(StorageError, match="never returned"):
        store.load(absent)
    # The snapshot exists, but of another card.
    with pytest.raises(StorageError, match="No snapshot"):
        store.load(f"{tctim.id}@{parse_ref(hs).snapshot_id}")
    with pytest.raises(StorageError, match="No card"):
        store.load("sabueso:protein:uniprot:Q00001")
    with pytest.raises(StorageError, match="malformed pin"):
        store.load(f"{tctim.id}@sha256:1234")
    assert absent not in store and tctim.id in store and hs in store


def test_items_are_cited_in_a_pinned_state(tmp_path, tctim):
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    ref = store.save(tctim)
    assertion = tctim.source_assertion_store.to_list()[0]
    relationship = tctim.relationship_store.to_list()[0]
    assert store.source_assertion(f"{ref}#{assertion['id']}") == assertion
    assert store.relationship(f"{ref}#{relationship['id']}") == relationship
    with pytest.raises(StorageError, match="holds no"):
        store.source_assertion(f"{ref}#SA_UniProt_absent")
    with pytest.raises(StorageError, match="unpinned"):
        store.source_assertion(f"{tctim.id}#{assertion['id']}")
    with pytest.raises(StorageError, match="names an item"):
        store.load(f"{ref}#{assertion['id']}")


# --- normalized rows ------------------------------------------------------------------------


def _count(path, table):
    with sqlite3.connect(path) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_rows_are_stored_once_and_shared(tmp_path, tctim, hstim):
    path = tmp_path / "knowledge.db"
    store = sabueso.KnowledgeStore(path)
    store.save(tctim)
    assertions = _count(path, "source_assertions")
    relationships = _count(path, "relationships")
    assert assertions == len(tctim.source_assertion_store.to_list())
    # A second state of the card adds only what changed: here, nothing in its rows.
    store.save(_variant(tctim, "new"))
    assert _count(path, "source_assertions") == assertions
    assert _count(path, "relationships") == relationships
    assert _count(path, "snapshots") == 2
    # Rows are keyed by content: another card states its own subject, so it shares none
    # of TcTIM's relationships, even the TIM domain both are classified in.
    store.save(hstim)
    hs = len(hstim.relationship_store.to_list())
    assert _count(path, "relationships") == relationships + hs


def test_the_same_assertion_in_another_release_is_another_row(tmp_path, tctim):
    path = tmp_path / "knowledge.db"
    store = sabueso.KnowledgeStore(path)
    first = store.save(tctim)
    data = tctim.to_dict()
    data["source_assertion_store"][0]["source"]["version"] = "121"
    data.pop("quantities")
    from sabueso.core.quantities import seal

    data["quantities"] = seal(data)
    second = store.save(Card.from_dict(data))
    sa_id = data["source_assertion_store"][0]["id"]
    assert store.source_assertion(f"{first}#{sa_id}")["source"]["version"] == "120"
    assert store.source_assertion(f"{second}#{sa_id}")["source"]["version"] == "121"


def test_cards_are_found_from_what_they_point_at(tmp_path, tctim, hstim):
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    tc, hs = store.save(tctim), store.save(hstim)
    found = store.relationships(object_ref=TIM_DOMAIN, predicate="classified_in")
    assert sorted(r["card"] for r in found) == sorted([tc, hs])
    assert all(r["relationship"]["object_ref"] == TIM_DOMAIN for r in found)
    molecule = next(
        r["object_ref"]
        for r in tctim.relationship_store.to_list()
        if r["predicate"] == "has_bioactivity"
    )
    # Which proteins was this molecule measured on? Both TIMs, as their cards state.
    measured = store.relationships(object_ref=molecule, predicate="has_bioactivity")
    expected = {
        ref
        for ref, card in ((tc, tctim), (hs, hstim))
        if card.relationships("has_bioactivity", object_ref=molecule)
    }
    assert {r["card"] for r in measured} == expected == {tc, hs}
    # Only the latest state is searched unless every revision is asked for.
    store.save(_variant(tctim, "new"))
    assert len(store.relationships(object_ref=TIM_DOMAIN)) == 2
    assert len(store.relationships(object_ref=TIM_DOMAIN, all_revisions=True)) == 3


def test_queries_are_checked(tmp_path):
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    with pytest.raises(StorageError, match="Name an object_ref"):
        store.relationships()
    with pytest.raises(ArgumentError):
        store.relationships(predicate="binds_to_something")
    with pytest.raises(ArgumentError):
        store.relationships(object_ref="no namespace")
    with pytest.raises(ArgumentError):
        store.load(42)


# --- decks ----------------------------------------------------------------------------------


def test_a_deck_is_stored_as_its_meta_and_pinned_cards(tmp_path, tctim, hstim):
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    deck = Deck([tctim, hstim], meta={"kind": "orthologs", "decision": {"by": "test"}})
    refs = store.save_deck(deck, "tims")
    loaded = store.load_deck("tims")
    assert loaded.meta == deck.meta
    assert [c.pinned_ref() for c in loaded.cards] == refs
    # Replacing the deck keeps the snapshots it pointed to.
    store.save_deck(Deck([_variant(tctim, "new")]), "tims")
    assert len(store.load_deck("tims").cards) == 1
    assert store.load(refs[0]).to_dict() == tctim.to_dict()
    assert store.deck_names() == ["tims"]
    with pytest.raises(StorageError, match="No deck"):
        store.load_deck("absent")


# --- integrity, format and migration ----------------------------------------------------------


def test_a_store_changed_outside_sabueso_is_refused(tmp_path, tctim):
    path = tmp_path / "knowledge.db"
    store = sabueso.KnowledgeStore(path)
    ref = store.save(tctim)
    with sqlite3.connect(path) as conn:
        body_hash, body = conn.execute(
            "SELECT body_hash, body FROM source_assertions LIMIT 1"
        ).fetchone()
        changed = json.loads(body)
        changed["asserted_value"] = "tampered"
        conn.execute(
            "UPDATE source_assertions SET body = ? WHERE body_hash = ?",
            (json.dumps(changed), body_hash),
        )
    with pytest.raises(StorageError, match="changed outside Sabueso"):
        store.load(ref)


def test_the_store_states_its_format(tmp_path):
    path = tmp_path / "knowledge.db"
    sabueso.KnowledgeStore(path)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE store_meta SET value = '2' WHERE key = 'format'")
    with pytest.raises(StorageError, match="format 2"):
        sabueso.KnowledgeStore(path)
    other = tmp_path / "not_a_database.db"
    other.write_text("plain text", encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.KnowledgeStore(other)


def test_a_card_table_is_imported_as_history(tmp_path, tctim):
    legacy = tmp_path / "cards.db"
    before, after = _variant(tctim, "new"), _variant(tctim, "corroborates")
    for card in (before, before, after):
        sabueso.save_card_sqlite(card, legacy)
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    refs = store.import_card_table(legacy)
    assert refs == [before.pinned_ref(), before.pinned_ref(), after.pinned_ref()]
    history = store.history(tctim.id)
    assert [h["ref"] for h in history] == [before.pinned_ref(), after.pinned_ref()]
    assert history[0]["note"] == "imported from cards.db, table cards, row 1"
    assert store.load(tctim.id).to_dict() == after.to_dict()
    with pytest.raises(StorageError, match="no card table"):
        store.import_card_table(legacy, table="absent")
