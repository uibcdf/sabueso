"""Automatic attribution preserves pinned knowledge and observes real reusable credits."""

import json
import subprocess
import sys
import textwrap
from contextvars import Context

import pytest

import sabueso
from sabueso._private.smonitor.warnings import AttributionTrackingWarning
from sabueso.core import attribution as adapter
from sabueso.core.card import Card
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient


@pytest.fixture(scope="module")
def card():
    return sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc={"article_ids": "PMC:PMC12400196"},
        europepmc_client=FixtureEuropePMCClient("temp_data"),
    )[0]


@pytest.fixture
def provider():
    import ackredit

    return ackredit


def compose(card, aspects=("literature",), detail="full"):
    return sabueso.compose_packet(
        sabueso.KnowledgeQuery("P60174", aspects=aspects, detail=detail), card
    )


def test_default_composition_has_detached_attribution_without_collector(card, provider):
    with provider.session("automatic result"):
        packet = compose(card)
        record = packet.attribution
        assert record["provider"]["status"] == "available"
        assert record["packet_snapshot_id"] == packet.snapshot_id()
        assert provider.get_attribution().to_dict()["items"]
    document = packet.to_dict()
    record["scope"].clear()
    assert packet.attribution["scope"]
    assert packet.to_dict() == document
    # A scientific payload does not pretend to reproduce an earlier execution.
    assert sabueso.KnowledgePacket(document).attribution is None


def test_support_does_not_rehash_the_entire_card_per_statement(card, monkeypatch):
    packet = compose(card)
    original_pin = card.pinned_ref
    calls = []

    def counted_pin():
        calls.append(True)
        return original_pin()

    monkeypatch.setattr(card, "pinned_ref", counted_pin)
    support = adapter._support(packet, [("subject", card)])
    uses = [use for resource in support["resources"] for use in resource["uses"]]
    assert len(uses) > 2
    assert len(calls) == 1  # support closure computes its own pin once
    assert all(use["card_ref"] == packet.entities["subject"]["ref"] for use in uses)


def test_two_results_reuse_resources_in_application_workflow(card, provider):
    before = card.to_dict()
    baseline = compose(card)
    with provider.session("public packet pilot") as session:
        with provider.capture("workflow") as workflow:
            with provider.scope("application.prepare"):
                with sabueso.attribution() as run:
                    identity = compose(card, ("identity",))
                    literature = compose(card)
                    assert provider.current_session() is session
        records = run.records
        assert len(records) == 2
        assert records[0]["packet_snapshot_id"] == identity.snapshot_id()
        assert records[1]["packet_snapshot_id"] == literature.snapshot_id()
        assert identity.attribution == records[0]
        assert literature.attribution == records[1]
        left, right = [record["provider"]["attribution"] for record in records]
        assert all(record["provider"]["status"] == "available" for record in records)
        left_ids = {item["id"] for item in left["items"]}
        right_ids = {item["id"] for item in right["items"]}
        assert "doi:10.1093/nar/gkae1010" in left_ids & right_ids
        assert "doi:10.1093/nar/gkad1085" in right_ids - left_ids
        assert {
            item["id"] for item in workflow.attribution.to_dict()["items"]
        } == left_ids | right_ids
        assert {
            item["id"] for item in provider.get_attribution().to_dict()["items"]
        } == left_ids | right_ids
        assert (
            "sabueso.compose_packet"
            in workflow.attribution.to_dict()["usage_tree"]["application.prepare"][
                "children"
            ]
        )
        assert {role for use in right["uses"] for role in use["roles"]} == {
            "executed_software",
            "stored_knowledge",
            "resource_description",
        }
    assert literature.to_dict() == baseline.to_dict()
    assert card.to_dict() == before
    assert records[1][
        "bibliography_gaps"
    ]  # Article/provider citations stay incomplete.
    refs = [
        item
        for item in records[1]["scope"]["subject"]["items"]
        if item["kind"] == "relationship"
    ]
    assert any(
        item.get("predicate") == "has_structure" and item["object_ref"] == "pdb:2JK2"
        for item in refs
    )


def test_saved_readers_preserve_original_versions_without_new_credit(
    card, provider, tmp_path, monkeypatch
):
    with provider.session("original"):
        with sabueso.attribution() as run:
            original = compose(card)
    record = run.records[0]
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(card)
    reference = store.save_packet(original, "literature")
    saved = tmp_path / "attribution.json"
    saved.write_text(json.dumps(record))
    monkeypatch.setattr(sabueso, "__version__", "999.reader")
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: pytest.fail("Reading must not load the backend"),
    )
    with provider.session("reader"):
        with sabueso.attribution() as reading:
            restored = json.loads(saved.read_text())
            assert store.load_packet(reference).to_dict() == original.to_dict()
            attribution = provider.Attribution.from_dict(
                restored["provider"]["attribution"]
            )
            text = attribution.report(format="text")
            csl = json.loads(attribution.report(format="csl-json"))
            bibtex = attribution.report(format="bibtex")
        assert reading.records == []
        assert provider.get_attribution().to_dict()["items"] == []
    assert restored == record
    assert "999.reader" not in text
    assert "author = {{The UniProt Consortium}}" in bibtex
    assert "Rosonovski, Summer and Levchenko, Maria" in bibtex
    assert "Xing, Lijun and Harrison, Melissa" in bibtex
    assert "{'literal':" not in bibtex
    uniprot = next(item for item in csl if item["id"] == "doi:10.1093/nar/gkae1010")
    assert uniprot["author"] == [{"literal": "The UniProt Consortium"}]
    assert (
        len(
            next(item for item in csl if item["id"] == "doi:10.1093/nar/gkad1085")[
                "author"
            ]
        )
        == 22
    )


def test_full_and_index_scope_agree_and_unused_source_has_no_credit(card, provider):
    subject = Card.from_dict(card.to_dict())
    subject.source_assertion_store.add(
        make_source_assertion(
            "unasked.synthetic", "unused", "ChEMBL", "synthetic", "fixture"
        )
    )
    with provider.session("scope"):
        with sabueso.attribution() as run:
            compose(subject)
            compose(subject, detail="index")
    full, index = run.records
    assert full["scope"] == index["scope"]
    assert full["resources"] == index["resources"]
    assert {resource["source"]["name"] for resource in full["resources"]} == {
        "UniProt",
        "Europe PMC",
    }
    assert any(resource["source"]["version"] is None for resource in full["resources"])
    assert all(
        use["retrieved_at"]
        for resource in full["resources"]
        for use in resource["uses"]
    )


@pytest.mark.parametrize("failure", ["import", "after_credit"])
def test_installed_provider_failure_keeps_host_record_and_result(
    card, provider, monkeypatch, failure
):
    baseline = compose(card)
    if failure == "import":

        def broken():
            raise ImportError("broken installed provider")

        monkeypatch.setattr(adapter, "_load_backend", broken)
    else:
        original_track = provider.track_item

        def broken(*args, **kwargs):
            original_track(*args, **kwargs)
            raise RuntimeError("provider failed after a credit")

        monkeypatch.setattr(provider, "track_item", broken)
    with provider.session("provider failure"):
        with pytest.warns(AttributionTrackingWarning) as warning:
            with sabueso.attribution() as run:
                packet = compose(card)
    assert warning[0].message.code == "SABUESO-W-ATTRIBUTION-001"
    assert packet.to_dict() == baseline.to_dict()
    record = run.records[0]
    assert record["provider"]["status"] == "failed"
    assert record["provider"]["attribution"] is None
    assert record["resources"] and record["bibliography"] and record["scope"]


def test_unknown_resource_bibliography_stays_a_visible_gap(card, provider):
    subject = Card.from_dict(card.to_dict())
    for assertion in subject.source_assertion_store.to_list():
        if assertion["field_path"] == "sequence.length":
            assertion["source"] = {
                "name": "Unregistered source",
                "type": "other",
                "record_id": "test",
                "version": None,
            }
    with provider.session("unknown bibliography"):
        with sabueso.attribution() as run:
            compose(subject, ("identity",))
    record = run.records[0]
    unknown = next(
        resource
        for resource in record["resources"]
        if resource["source"]["name"] == "Unregistered source"
    )
    assert unknown["description_citation_ids"] == []
    assert {
        "resource_id": unknown["id"],
        "reason": "description_citation_not_declared",
    } in record["bibliography_gaps"]


def test_nested_contexts_observe_reuse_without_duplicate_tracking(card, provider):
    with provider.session("nested"):
        with provider.capture("workflow") as workflow:
            with sabueso.attribution() as outer:
                with sabueso.attribution() as inner:
                    compose(card)
                compose(card)
        assert len(outer.records) == 2 and len(inner.records) == 1
        assert len(workflow.attribution.to_dict()["uses"]) == len(
            inner.records[0]["provider"]["attribution"]["uses"]
        )
    original = outer.records
    original[0]["scope"].clear()
    assert outer.records[0]["scope"] and inner.records[0]["scope"]


def test_context_isolation_and_scientific_exception_propagation(card, provider):
    with sabueso.attribution() as run:
        result = Context().run(compose, card)
        assert result.attribution["provider"]["status"] == "available"
        with pytest.raises(ValueError, match="comparator"):
            sabueso.compose_packet(
                sabueso.KnowledgeQuery("P60174", comparator="P52270"), card
            )
    assert run.records == []
    assert adapter._runs.get() == ()


def test_recorded_empty_or_unqueried_source_is_not_a_new_acquisition(card, provider):
    subject = sabueso.resolve(
        "P60174", resolver=EntityResolver(FixtureUniProtClient("temp_data"))
    )[0]
    # A composition adapter has no acquisition observation. A stored empty
    # outcome must not become a claim that it fetched this source in this run.
    subject.quality.setdefault("enrichments", []).append(
        {
            "source": "Europe PMC",
            "status": "not_found",
            "count": 0,
            "version": None,
            "retrieved_at": "fixture",
            "query": "synthetic empty outcome",
        }
    )
    with provider.session("stored empty source outcome"):
        with sabueso.attribution() as run:
            packet = compose(subject)
    assert packet.unknowns
    assert not any(
        resource["source"]["name"] == "Europe PMC"
        for resource in run.records[0]["resources"]
    )
    assert all(
        "acquired_resource" not in use["roles"]
        for use in run.records[0]["provider"]["attribution"]["uses"]
    )


def test_missing_support_is_diagnosed_without_destroying_completed_packet(
    card, monkeypatch
):
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: pytest.fail("Do not load provider without support"),
    )
    subject = Card.from_dict(card.to_dict())
    rel = subject.relationships("structure_mentioned_in")[0]
    missing = rel["qualifiers"]["structure_context"]["relationship_ids"][0]
    del subject.relationship_store.store[missing]
    with pytest.warns(AttributionTrackingWarning):
        baseline = compose(subject)
    with pytest.warns(AttributionTrackingWarning):
        with sabueso.attribution() as run:
            packet = compose(subject)
    assert packet.to_dict() == baseline.to_dict()
    assert run.records[0]["support_status"] == "unavailable"
    assert run.records[0]["provider"]["status"] == "not_attempted"


def test_fresh_process_absence_laziness_and_saved_reading(tmp_path):
    # Hide the provider through Python's actual discovery/import boundary in a new
    # interpreter, even when the developer has an editable Ackredit installed.
    script = textwrap.dedent("""
        import importlib.abc, importlib.util, json, sys, warnings
        from pathlib import Path
        class Absent(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "ackredit" or fullname.startswith("ackredit."):
                    raise ModuleNotFoundError("Ackredit is absent in this process", name=fullname)
        sys.meta_path.insert(0, Absent())
        import sabueso
        from sabueso.core.card import Card
        from sabueso.core.packets import KnowledgePacket
        card = Card.from_dict(json.loads(Path("temp_data/frozen_cards/schema_0.3.10__P60174.json").read_text()))
        query = sabueso.KnowledgeQuery("P60174", aspects=["identity"])
        from sabueso._private.smonitor.warnings import AttributionTrackingWarning
        with warnings.catch_warnings(record=True) as diagnosed:
            warnings.simplefilter("always")
            baseline = sabueso.compose_packet(query, card)
        assert any(isinstance(w.message, AttributionTrackingWarning) for w in diagnosed)
        assert baseline.attribution["provider"]["status"] == "failed"
        with sabueso.attribution() as empty:
            pass
        assert empty.records == []
        with sabueso.attribution() as run:
            packet = sabueso.compose_packet(query, card)
        assert run.records[0]["provider"]["status"] == "failed"
        assert "ModuleNotFoundError" in run.records[0]["provider"]["reason"]
        assert run.records[0]["resources"] and run.records[0]["bibliography"]
        saved = json.loads(json.dumps(run.records))
        with sabueso.attribution() as reading:
            KnowledgePacket(packet.to_dict())
            json.loads(json.dumps(saved))
        assert not reading.records
        assert packet.to_dict() == baseline.to_dict()
        assert not any(name == "ackredit" or name.startswith("ackredit.") for name in sys.modules)
        assert "sabueso.core.attribution_bibliography" in sys.modules
    """)
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_fresh_import_and_empty_context_never_load_provider_or_bibliography():
    script = textwrap.dedent("""
        import json, sys
        from pathlib import Path
        import sabueso
        from sabueso.core.card import Card
        card = Card.from_dict(json.loads(Path("temp_data/frozen_cards/schema_0.3.10__P60174.json").read_text()))
        with sabueso.attribution() as run:
            pass
        assert not run.records
        assert "ackredit" not in sys.modules
        assert "sabueso.core.attribution_bibliography" not in sys.modules
    """)
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
