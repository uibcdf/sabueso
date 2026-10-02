"""Terms follow packet support at saved pins, independently of packet detail."""

import json
from pathlib import Path

import pytest

import sabueso
from sabueso.core import terms as terms_module
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.packets import KnowledgePacket
from sabueso.core.quantities import seal
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient


def card():
    return sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc={"article_ids": "PMC:PMC12400196"},
        europepmc_client=FixtureEuropePMCClient("temp_data"),
    )[0]


def packet(subject, detail="full", aspects=("literature",)):
    return sabueso.compose_packet(
        sabueso.KnowledgeQuery("P60174", aspects=aspects, detail=detail), subject
    )


def test_full_index_same_support_terms_and_fragment_unknowns(tmp_path):
    subject = card()
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(subject)
    full, index = packet(subject), packet(subject, "index")
    before = full.to_dict()
    left, right = (
        full.terms("commercial_product", store),
        index.terms("commercial_product", store),
    )
    for key in (
        "scope",
        "sources",
        "cards",
        "restricted",
        "unknown",
        "obligations",
        "attribution",
    ):
        assert left[key] == right[key]
    assert left["sources"]["UniProt"]["verdict"] == "allowed"
    assert left["sources"]["Europe PMC Annotations"]["verdict"] == "unknown"
    unknown = left["cards"][0]["unknown"]
    assert {r["predicate"] for r in unknown if r["kind"] == "relationship"} >= {
        "mentioned_in",
        "structure_mentioned_in",
    }
    assert any(r["kind"] == "source_assertion" for r in unknown)
    scope = left["scope"]["subject"]["items"]
    assert any(
        r.get("predicate") == "has_structure" and r["object_ref"] == "pdb:2JK2"
        for r in scope
    )
    assert full.to_dict() == before
    assert left["packet_rule"] == "packet_terms@1"
    left["scope"]["subject"]["items"].clear()
    assert full.terms("commercial_product", store)["scope"]["subject"]["items"]


def test_historical_scope_does_not_follow_current_head_or_whole_card_sources(tmp_path):
    subject = card()
    # An unrelated synthetic measurement is on the card but outside this literature packet.
    sa = make_source_assertion(
        "relationships.has_bioactivity",
        {"value": "synthetic"},
        "ChEMBL",
        "test",
        "2026-10-02",
        subject_ref="uniprot:P60174",
    )
    subject.source_assertion_store.add(sa)
    subject.relationship_store.add(
        make_relationship(
            "uniprot:P60174",
            "has_bioactivity",
            "chembl:test",
            source_assertion_ids=[sa["id"]],
        )
    )
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    old = store.save(subject)
    answer = packet(subject, "index")
    packet_ref = store.save_packet(answer, "literature")
    expected = answer.terms("redistribution", store)
    assert "ChEMBL" not in expected["sources"]
    assert "share_alike" not in expected["obligations"]
    later = Card.from_dict(subject.to_dict())
    later.meta["later_observation"] = True
    store.save(later)
    assert store.load_packet(packet_ref).terms("redistribution", store) == expected
    assert expected["scope"]["subject"]["card_ref"] == old


def test_bibliographic_support_does_not_license_attached_fragments(tmp_path):
    subject = card()
    existing = subject.relationships("mentioned_in")[0]
    sa = make_source_assertion(
        "relationships.mentioned_in",
        {"bibliography": "synthetic alternative"},
        "Europe PMC",
        "test",
        "2026-10-02",
        subject_ref="uniprot:P60174",
    )
    subject.source_assertion_store.add(sa)
    existing["source_assertion_ids"].append(sa["id"])
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(subject)
    report = packet(subject).terms("commercial_product", store)
    unknown = report["cards"][0]["unknown"]
    assert not any(r.get("id") == existing["id"] for r in unknown)
    assert report["sources"]["Europe PMC"]["verdict"] == "allowed"
    assert "Europe PMC Annotations" in report["unknown"]
    assert any(
        r["kind"] == "source_assertion" and r["sources"] == ["Europe PMC Annotations"]
        for r in unknown
    )


def test_derived_context_needs_both_legs_not_one_allowed_source(tmp_path, monkeypatch):
    subject = card()
    stated = dict(terms_module.source_terms())
    stated["Europe PMC Annotations"] = {"licence": "CC0-1.0"}
    stated["UniProt"] = {"licence": "CC-BY-NC-4.0"}
    monkeypatch.setattr(terms_module, "source_terms", lambda: stated)
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(subject)
    report = packet(subject).terms("commercial_product", store)
    lost = report["cards"][0]["lost"]
    assert any(r.get("predicate") == "structure_mentioned_in" for r in lost)
    assert not any(r.get("predicate") == "mentioned_in" for r in lost)


@pytest.mark.parametrize("which", ["card", "assertion", "relationship"])
def test_missing_pinned_support_is_refused_not_currently_replaced(tmp_path, which):
    data = card().to_dict()
    if which != "card":
        rel = next(
            r
            for r in data["relationship_store"]
            if r["predicate"] == "structure_mentioned_in"
        )
        context = rel["qualifiers"]["structure_context"]
        identifier = context[
            "source_assertion_ids" if which == "assertion" else "relationship_ids"
        ][0]
        key = "source_assertion_store" if which == "assertion" else "relationship_store"
        data[key] = [r for r in data[key] if r["id"] != identifier]
        data["quantities"] = seal(data)
    subject = Card.from_dict(data)
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    if which != "card":
        store.save(subject)
    with pytest.raises(StorageError):
        packet(subject).terms("commercial_product", store)


def test_old_mapping_remains_readable_without_using_current_scope(tmp_path):
    payload = json.loads(
        Path(
            "temp_data/frozen_packets/packet_aspects_5__literature_index__P60174.json"
        ).read_text()
    )
    old = KnowledgePacket(payload)
    before = old.snapshot_id()
    with pytest.raises(StorageError, match="no scope adapter"):
        old.terms("redistribution", sabueso.KnowledgeStore(tmp_path / "knowledge.db"))
    assert old.snapshot_id() == before and old.to_dict() == payload


def test_current_index_with_unknown_view_rule_is_refused(tmp_path):
    subject = card()
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(subject)
    data = packet(subject, "index").to_dict()
    data["facts"]["literature"]["subject"]["full_rules"] = ["unknown_future_rule@99"]
    with pytest.raises(StorageError, match="unrecognized"):
        KnowledgePacket(data).terms("redistribution", store)


def test_invalid_use_and_missing_store_are_refused(tmp_path):
    answer = packet(card())
    with pytest.raises(ArgumentError):
        answer.terms("commercial", sabueso.KnowledgeStore(tmp_path / "knowledge.db"))
    with pytest.raises(StorageError, match="require a KnowledgeStore"):
        answer.terms("commercial_product", None)


def test_all_aspects_and_two_roles_have_same_full_index_scope(tmp_path):
    subjects = [
        Card.from_dict(
            json.loads(
                Path(
                    f"temp_data/frozen_cards/schema_{version}__{accession}.json"
                ).read_text()
            )
        )
        for version, accession in (("0.3.10", "P60174"), ("0.3.9", "P52270"))
    ]
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    for subject in subjects:
        store.save(subject)
    reports = [
        sabueso.compose_packet(
            sabueso.KnowledgeQuery("P60174", comparator="P52270", detail=detail),
            *subjects,
        ).terms("redistribution", store)
        for detail in ("full", "index")
    ]
    assert reports[0]["scope"] == reports[1]["scope"]
    assert reports[0]["sources"] == reports[1]["sources"]
    assert set(reports[0]["scope"]) == {"subject", "comparator"}
    assert "share_alike" in reports[0]["obligations"]


def test_conflicting_assertions_are_reported_even_when_not_selected(tmp_path):
    subject = card()
    original = subject.get("sequence.length")["source_assertion_ids"][0]
    alternate = make_source_assertion(
        "sequence.length",
        999,
        "Unrecorded synthetic source",
        "test",
        "2026-10-02",
        subject_ref="uniprot:P60174",
    )
    subject.source_assertion_store.add(alternate)
    subject.quality.setdefault("conflicts", []).append(
        {
            "field": "sequence.length",
            "type": "disagreement",
            "values": [249, 999],
            "source_assertion_ids": [[original], [alternate["id"]]],
        }
    )
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(subject)
    report = packet(subject, aspects=("identity",)).terms("redistribution", store)
    assert "Unrecorded synthetic source" in report["unknown"]
    assert any(row["id"] == alternate["id"] for row in report["cards"][0]["unknown"])
