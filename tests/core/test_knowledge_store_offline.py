"""Versioned cards in the knowledge store (uibcdf/sabueso#7, #27).

A pinned reference resolves to the exact state that was saved, or fails; it never
returns another state of the card. SourceAssertions and relationships are rows shared
by the snapshots that hold them, and relationships can be searched from their object.
"""

import copy
import json
import sqlite3
import zlib
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


@pytest.mark.parametrize("source", ["RCSB PDB", "AlphaFold DB", "NCBI Gene"])
def test_assertion_references_preserve_spaces_in_source_names(source):
    item_id = f"SA_{source}_record_0123456789abcdef"
    ref = f"sabueso:protein:uniprot:P52270@sha256:{'a' * 64}#{item_id}"
    parsed = parse_ref(ref)
    assert parsed.item_id == item_id
    assert str(parsed) == ref


@pytest.mark.parametrize(
    "item_id",
    [
        "SA_RCSB\tPDB_record",
        "SA_RCSB\nPDB_record",
        "SA_RCSB\rPDB_record",
        "SA_RCSB@PDB_record",
        "SA_RCSB#PDB_record",
        "SA_ RCSB PDB_record",
        "REL_RCSB PDB_record",
    ],
)
def test_item_references_refuse_control_whitespace_and_delimiters(item_id):
    with pytest.raises(StorageError):
        parse_ref(f"sabueso:protein:uniprot:P52270@sha256:{'a' * 64}#{item_id}")


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
    assertions = tctim.source_assertion_store.to_list()
    assertion = assertions[0]
    relationship = tctim.relationship_store.to_list()[0]
    # One real statement from each source covers names with spaces without repeating
    # whole-snapshot verification for every statement of the same source (#104).
    by_source = {record["source"]["name"]: record for record in assertions}
    for record in by_source.values():
        assert store.source_assertion(f"{ref}#{record['id']}") == record
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
    assertions = _count(path, "sa_rows")
    relationships = _count(path, "rel_rows")
    assert assertions == len(tctim.source_assertion_store.to_list())
    # A second state of the card adds only what changed: here, nothing in its rows.
    store.save(_variant(tctim, "new"))
    assert _count(path, "sa_rows") == assertions
    assert _count(path, "rel_rows") == relationships
    assert _count(path, "snapshots") == 2
    # Rows are keyed by content: another card states its own subject, so it shares none
    # of TcTIM's relationships, even the TIM domain both are classified in.
    store.save(hstim)
    hs = len(hstim.relationship_store.to_list())
    assert _count(path, "rel_rows") == relationships + hs


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
    ref = store.save_deck(deck, "tims")
    assert ref == f"sabueso:deck:tims@{deck.snapshot_id()}"
    loaded = store.load_deck("tims")
    assert loaded.meta == deck.meta
    assert [c.pinned_ref() for c in loaded.cards] == [
        tctim.pinned_ref(),
        hstim.pinned_ref(),
    ]
    # Saving the same content again adds nothing; new content is a new revision, and
    # the earlier one keeps resolving (#58).
    assert store.save_deck(deck, "tims") == ref
    newer = store.save_deck(Deck([_variant(tctim, "new")]), "tims", note="one card")
    assert [h["ref"] for h in store.deck_history("tims")] == [ref, newer]
    assert len(store.load_deck("tims").cards) == 1
    assert len(store.load_deck(ref).cards) == 2
    assert store.load_deck("sabueso:deck:tims").meta == {}
    assert store.deck_names() == ["tims"]
    with pytest.raises(StorageError, match="No deck"):
        store.load_deck("absent")
    with pytest.raises(StorageError, match="No revision"):
        store.load_deck(f"tims@sha256:{'0' * 64}")
    with pytest.raises(StorageError, match="not under a pin"):
        store.save_deck(deck, ref)
    with pytest.raises(ArgumentError):
        store.save_deck(deck, "two words")


# --- integrity, format and migration ----------------------------------------------------------


def test_a_store_changed_outside_sabueso_is_refused(tmp_path, tctim):
    path = tmp_path / "knowledge.db"
    store = sabueso.KnowledgeStore(path)
    ref = store.save(tctim)
    with sqlite3.connect(path) as conn:
        body_hash, body = conn.execute(
            "SELECT body_hash, body FROM sa_rows LIMIT 1"
        ).fetchone()
        changed = json.loads(_text(body))
        changed["asserted_value"] = "tampered"
        conn.execute(
            "UPDATE sa_rows SET body = ? WHERE body_hash = ?",
            (_stored(json.dumps(changed)), body_hash),
        )
    with pytest.raises(StorageError, match="changed outside Sabueso"):
        store.load(ref)


def _text(value):
    """A stored row's text (format 2 stores it compressed)."""
    return zlib.decompress(value).decode() if isinstance(value, bytes) else value


def _stored(text):
    return zlib.compress(text.encode())


def _tamper(path, table, id_column):
    """Change one row's body outside Sabueso, keeping its hash and the snapshot id."""
    with sqlite3.connect(path) as conn:
        item_id, body_hash, body = conn.execute(
            f"SELECT {id_column}, body_hash, body FROM {table} LIMIT 1"
        ).fetchone()
        changed = json.loads(_text(body))
        changed["tampered"] = True
        conn.execute(
            f"UPDATE {table} SET body = ? WHERE body_hash = ?",
            (_stored(json.dumps(changed)), body_hash),
        )
    return item_id


def test_a_pinned_item_read_is_verified_like_a_card_read(tmp_path, tctim):
    # A pinned item returns the item as the verified snapshot holds it, or fails; it
    # never returns changed content under the original pin (#79, uibcdf/moli#3).
    for table, id_column, read in (
        ("sa_rows", "sa_id", "source_assertion"),
        ("rel_rows", "rel_id", "relationship"),
    ):
        path = tmp_path / f"{table}.db"
        store = sabueso.KnowledgeStore(path)
        ref = store.save(tctim)
        item_id = _tamper(path, table, id_column)
        with pytest.raises(StorageError, match="changed outside Sabueso"):
            getattr(store, read)(f"{ref}#{item_id}")
        # A spaced assertion id still verifies the entire snapshot (#104).
        rcsb = next(
            sa
            for sa in tctim.source_assertion_store.to_list()
            if sa["source"]["name"] == "RCSB PDB"
        )
        with pytest.raises(StorageError, match="changed outside Sabueso"):
            store.source_assertion(f"{ref}#{rcsb['id']}")
        with pytest.raises(StorageError, match="changed outside Sabueso"):
            store.load(ref)


def test_a_relationship_search_never_cites_a_changed_state(tmp_path, tctim):
    path = tmp_path / "k.db"
    store = sabueso.KnowledgeStore(path)
    store.save(tctim)
    assert store.relationships(predicate="has_structure")  # untouched: found
    _tamper(path, "rel_rows", "rel_id")
    with pytest.raises(StorageError, match="changed outside Sabueso"):
        store.relationships(predicate="has_structure")


def test_the_store_states_its_format(tmp_path):
    path = tmp_path / "knowledge.db"
    sabueso.KnowledgeStore(path)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE store_meta SET value = '3' WHERE key = 'format'")
    with pytest.raises(StorageError, match="format 3"):
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


# --- format 2: unchanged knowledge stored once, compressed (#99) -------------------------


def _read_again(card, when="2027-01-01T00:00:00+00:00"):
    """The same card as if every source were read again, with nothing changed."""
    data = copy.deepcopy(card.to_dict())
    for assertion in data["source_assertion_store"]:
        assertion["retrieved_at"] = when
    data.pop("quantities", None)
    from sabueso.core.quantities import seal

    data["quantities"] = seal(data)
    return Card.from_dict(data)


def test_unchanged_knowledge_read_again_adds_no_rows(tmp_path, tctim):
    path = tmp_path / "k.db"
    store = sabueso.KnowledgeStore(path)
    first = store.save(tctim)
    count = "SELECT count(*) FROM sa_rows"
    with sqlite3.connect(path) as conn:
        rows = conn.execute(count).fetchone()[0]
    again = store.save(_read_again(tctim))
    assert again != first  # another state: the retrieval times differ
    with sqlite3.connect(path) as conn:
        assert conn.execute(count).fetchone()[0] == rows
    # Each revision still knows when each statement was read.
    old, new = store.load(first), store.load(again)
    assert {sa["retrieved_at"] for sa in new.source_assertion_store.to_list()} == {
        "2027-01-01T00:00:00+00:00"
    }
    assert old.to_dict() == tctim.to_dict()


def test_what_is_stored_is_compressed(tmp_path, tctim):
    path = tmp_path / "k.db"
    sabueso.KnowledgeStore(path).save(tctim)
    with sqlite3.connect(path) as conn:
        (document,) = conn.execute("SELECT document FROM snapshots").fetchone()
        (body,) = conn.execute("SELECT body FROM sa_rows LIMIT 1").fetchone()
    assert isinstance(document, bytes) and isinstance(body, bytes)
    assert "retrieved_at" not in json.loads(zlib.decompress(body))


FORMAT_1 = """
CREATE TABLE store_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE snapshots (snapshot_id TEXT PRIMARY KEY, card_id TEXT NOT NULL,
    entity_type TEXT, schema_version TEXT NOT NULL, document TEXT NOT NULL,
    quantities TEXT NOT NULL);
CREATE TABLE revisions (revision INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL, snapshot_id TEXT NOT NULL REFERENCES snapshots (snapshot_id),
    stored_at TEXT NOT NULL, note TEXT);
CREATE TABLE source_assertions (body_hash TEXT PRIMARY KEY, sa_id TEXT NOT NULL,
    subject_ref TEXT, field_path TEXT, source_name TEXT, source_version TEXT,
    body TEXT NOT NULL);
CREATE TABLE snapshot_source_assertions (snapshot_id TEXT NOT NULL, position INTEGER
    NOT NULL, body_hash TEXT NOT NULL, PRIMARY KEY (snapshot_id, position));
CREATE TABLE relationships (body_hash TEXT PRIMARY KEY, rel_id TEXT NOT NULL,
    subject_ref TEXT, predicate TEXT, object_ref TEXT, body TEXT NOT NULL);
CREATE TABLE snapshot_relationships (snapshot_id TEXT NOT NULL, position INTEGER
    NOT NULL, body_hash TEXT NOT NULL, PRIMARY KEY (snapshot_id, position));
"""


def _format_1_store(path, card):
    """A store as Sabueso wrote format 1: text rows with retrieved_at inside."""
    from sabueso.core.knowledge_store import _columns
    from sabueso.core.snapshot import canonical_json, digest, pinned_ref

    stored = card.to_dict()
    sid = snapshot_id(stored)
    with sqlite3.connect(path) as conn:
        conn.executescript(FORMAT_1)
        conn.execute("INSERT INTO store_meta VALUES ('format', '1')")
        document = {
            k: v
            for k, v in stored.items()
            if k not in ("source_assertion_store", "relationship_store", "quantities")
        }
        conn.execute(
            "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?)",
            (
                sid,
                card.id,
                card.meta.get("entity_type"),
                card.meta["schema_version"],
                canonical_json(document),
                canonical_json(stored["quantities"]),
            ),
        )
        for key, rows, members, id_column, columns in (
            (
                "source_assertion_store",
                "source_assertions",
                "snapshot_source_assertions",
                "sa_id",
                "subject_ref, field_path, source_name, source_version",
            ),
            (
                "relationship_store",
                "relationships",
                "snapshot_relationships",
                "rel_id",
                "subject_ref, predicate, object_ref",
            ),
        ):
            for position, row in enumerate(stored[key]):
                body = canonical_json(row)
                values = (digest(body), row["id"], *_columns(key, row), body)
                conn.execute(
                    f"INSERT OR IGNORE INTO {rows} (body_hash, {id_column}, "
                    f"{columns}, body) VALUES ({', '.join('?' for _ in values)})",
                    values,
                )
                conn.execute(
                    f"INSERT INTO {members} VALUES (?, ?, ?)",
                    (sid, position, digest(body)),
                )
        conn.execute(
            "INSERT INTO revisions (card_id, snapshot_id, stored_at) VALUES (?, ?, ?)",
            (card.id, sid, "2026-09-29T00:00:00+00:00"),
        )
    return pinned_ref(card.id, sid)


def test_a_format_1_store_is_upgraded_in_place_and_still_read(tmp_path, tctim):
    path = tmp_path / "k.db"
    old_ref = _format_1_store(path, tctim)
    store = sabueso.KnowledgeStore(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT value FROM store_meta").fetchone() == ("2",)
        tables = {n for (n,) in conn.execute("SELECT name FROM sqlite_master")}
    assert "source_assertions" not in tables and "sa_rows" in tables
    assert store.load(old_ref).to_dict() == tctim.to_dict()
    assert store.relationships(predicate="has_structure")
    new_ref = store.save(_read_again(tctim))
    assert store.load(new_ref).id == tctim.id
    assert [h["ref"] for h in store.history(tctim.id)] == [old_ref, new_ref]
