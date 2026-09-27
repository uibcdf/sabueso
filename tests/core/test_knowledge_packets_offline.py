"""Knowledge packets: a declared query, a deterministic, pinned answer (#71).

HsTIM (P60174) as subject and TcTIM (P52270) as comparator, on frozen responses.
"""

import sqlite3
import warnings

import argdigest
import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, ResolverError, StorageError
from sabueso.core.packets import ASPECTS, card_content_id
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.interpro import FixtureInterProClient
from sabueso.tools.db.ncbi_taxonomy import FixtureNCBITaxonomyClient
from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient
from sabueso.tools.db.phi_base import FixturePHIBaseClient


@pytest.fixture(scope="module")
def clients():
    return dict(
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        chembl_client=FixtureChEMBLClient("temp_data"),
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        interpro_client=FixtureInterProClient("temp_data"),
        taxonomy_client=FixtureNCBITaxonomyClient("temp_data"),
        phi_base_client=FixturePHIBaseClient("temp_data"),
    )


@pytest.fixture(scope="module")
def query():
    return sabueso.KnowledgeQuery("P60174", comparator="uniprot:P52270")


def _packet(query, clients, **kwargs):
    with warnings.catch_warnings():
        # Structures without a saved RCSB response are recorded as not found.
        warnings.simplefilter("ignore")
        return sabueso.knowledge_packet(query, **kwargs, **clients)


@pytest.fixture(scope="module")
def packet(query, clients):
    return _packet(query, clients)


def test_a_query_is_declared_and_normalized(query):
    assert query.to_dict() == {
        "format": "knowledge_query@1",
        "subject": "uniprot:P60174",
        "comparator": "uniprot:P52270",
        "aspects": sorted(ASPECTS),
        "constraints": {"bioactivity_sources": ["ChEMBL"]},
    }
    assert sabueso.KnowledgeQuery.from_dict(query.to_dict()) == query
    # What the aspects ask of the sources is fixed by packet_aspects@1.
    assert query.options() == {
        "phi_base": True,
        "taxonomy": True,
        "structures": "all",
        "interfaces": True,
        "family_sites": True,
        "ligand_sites": True,
        "chembl": {},
    }
    narrow = sabueso.KnowledgeQuery(
        "P60174",
        aspects=["bioactivities"],
        constraints={"bioactivity_sources": ["BindingDB", "ChEMBL"]},
    )
    assert narrow.options() == {"chembl": {}, "bindingdb": {}}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"subject": "TIM"},
        {"subject": "P60174", "aspects": ["everything"]},
        {"subject": "P60174", "constraints": {"organism": 9606}},
        {"subject": "P60174", "constraints": {"bioactivity_sources": ["IUPHAR"]}},
    ],
)
def test_what_a_query_cannot_state_is_refused(kwargs):
    with pytest.raises(ArgumentError):
        sabueso.KnowledgeQuery(**kwargs)


def test_the_packet_holds_the_declared_aspects_for_both_proteins(packet):
    assert set(packet.facts) == set(ASPECTS)
    assert packet.entities["subject"]["card_id"] == "sabueso:protein:uniprot:P60174"
    assert packet.entities["comparator"]["card_id"] == "sabueso:protein:uniprot:P52270"
    structures = packet.facts["structures"]
    assert set(structures) == {"subject", "comparator", "together"}
    assert structures["together"]["inventory"]["rule"]["rule"].startswith(
        "structure_inventory@"
    )
    assert "identity_audit" in packet.facts["identity"]["together"]
    # Each view keeps its named rule.
    oligomer = packet.facts["oligomer"]["subject"]
    assert {r["rule"] for r in oligomer["rules"]}
    # Quantities stay quantities, with their unit.
    item = structures["subject"]["experimental"]["items"][0]
    assert set(item["resolution"]) == {"value", "unit"}
    assert item["resolution"]["unit"] == "angstrom"


def test_unknowns_follow_the_query(packet, query, clients):
    rows = {
        (r["area"], r["source"]): r["state"] for r in packet.unknowns["subject"]["rows"]
    }
    # Only ChEMBL was asked for bioactivities: the others were not queried.
    assert rows[("relationships.has_bioactivity", "BindingDB")] == "not_queried"
    assert ("relationships.has_bioactivity", "ChEMBL") not in rows
    assert rows[("features_positional.mutagenesis", "UniProt")] == "not_stated"
    assert packet.unknowns["subject"]["rule"]["rule"] == "knowledge_state@2"
    # A packet that asks only about identity reports only identity's unknowns.
    only = _packet(sabueso.KnowledgeQuery("P60174", aspects=["identity"]), clients)
    assert set(only.facts) == {"identity"}
    assert all(
        r["area"].startswith(ASPECTS["identity"]["areas"])
        for r in only.unknowns["subject"]["rows"]
    )


def test_composition_is_deterministic(packet, query, clients):
    again = _packet(query, clients)
    assert again.snapshot_id() == packet.snapshot_id()
    # From the same card states, read back from their JSON form.
    subject = Card.from_dict(
        sabueso.resolve("P60174", **query.options(), **clients)[0].to_dict()
    )
    assert card_content_id(subject) == packet.entities["subject"]["content_id"]


def test_retrieval_times_change_the_pin_but_not_the_knowledge(query, clients):
    options = {**query.options(), **clients}
    subject = sabueso.resolve("P60174", **options)[0]
    comparator = sabueso.resolve("P52270", **options)[0]
    first = sabueso.compose_packet(query, subject, comparator)
    reread = subject.to_dict()
    for assertion in reread["source_assertion_store"]:
        assertion["retrieved_at"] = "2027-01-01T00:00:00+00:00"
    later = sabueso.compose_packet(query, Card.from_dict(reread), comparator)
    assert later.snapshot_id() != first.snapshot_id()
    assert later.same_knowledge(first)
    changed = subject.to_dict()
    changed["sections"]["names"]["canonical_name"]["value"] = "Another name"
    other = sabueso.compose_packet(query, Card.from_dict(changed), comparator)
    assert not other.same_knowledge(first)


def test_a_stored_packet_is_pinned_verified_and_citable(tmp_path, query, clients):
    store = sabueso.KnowledgeStore(tmp_path / "k.db")
    packet = _packet(query, clients, store=store, packet_name="tim_pair", note="first")
    assert packet.ref.startswith("sabueso:packet:tim_pair@sha256:")
    loaded = store.load_packet(packet.ref)
    assert loaded.to_dict() == packet.to_dict()
    assert store.load_packet("tim_pair").ref == packet.ref
    # A SourceAssertion a fact names is cited in the pinned card state it was read in.
    sa_id = packet.facts["identity"]["subject"]["fields"]["names.canonical_name"][
        "source_assertion_ids"
    ][0]
    assert store.source_assertion(packet.cite("subject", sa_id))["id"] == sa_id
    # Assembling the same knowledge again adds no revision; the history says whether
    # the knowledge changed.
    _packet(query, clients, store=store, packet_name="tim_pair")
    history = store.packet_history("tim_pair")
    assert [h["knowledge_changed"] for h in history] == [None]
    assert store.packet_names() == ["tim_pair"]


def test_a_packet_is_stored_only_with_the_cards_it_cites(tmp_path, packet):
    store = sabueso.KnowledgeStore(tmp_path / "k.db")
    with pytest.raises(StorageError):
        store.save_packet(packet, "orphan")
    assert store.packet_names() == []


def test_a_changed_packet_is_refused(tmp_path, query, clients):
    path = tmp_path / "k.db"
    store = sabueso.KnowledgeStore(path)
    packet = _packet(query, clients, store=store, packet_name="tim_pair")
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE packet_snapshots SET document = replace(document, "
            "'knowledge_state@2', 'knowledge_state@9')"
        )
    with pytest.raises(StorageError, match="no longer matches"):
        store.load_packet(packet.ref)


def test_an_unresolved_or_mismatched_card_is_refused(query, clients):
    options = {**query.options(), **clients}
    subject = sabueso.resolve("P60174", **options)[0]
    with pytest.raises(ValueError, match="comparator"):
        sabueso.compose_packet(query, subject)
    with pytest.raises(ValueError, match="asks about"):
        sabueso.compose_packet(query, subject, subject)
    with pytest.raises(ResolverError, match="did not resolve"):
        _packet(sabueso.KnowledgeQuery("A0A000XXX0"), clients)


def test_the_clients_never_change_what_is_asked(query, clients):
    # Knowledge options come from the query only; a keyword is a source client or
    # the resolver.
    with pytest.raises(argdigest.UnknownArgumentError):
        sabueso.knowledge_packet(query, bindingdb={}, **clients)
