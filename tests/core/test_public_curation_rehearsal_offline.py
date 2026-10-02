"""The public review draft rehearses preservation without asserting human approval."""

import json

import pytest

import sabueso
from tools import rehearse_public_curation as rehearsal


def test_a_public_review_draft_has_traceable_outcomes_after_rebuild(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    def no_network(*args, **kwargs):
        raise AssertionError("The rehearsal reads frozen public fixtures only")

    monkeypatch.setattr(_http, "urlopen", no_network)
    output = tmp_path / "rehearsal"
    report = rehearsal.rehearse(output)
    assert report["human_validation"] is None
    assert report["mode"] == "hypothetical_human_curation_rehearsal"
    assert all(report["identity_and_numbering_checks"].values())
    assert [record["outcome"] for record in report["outcomes"]] == [
        "differs",
        "not_compared",
        "not_compared",
    ]
    assert report["new_source_assertions"] == 3
    assert report["new_free_text_claims"] == 2
    assert report["difference_warnings"] == 1
    assert report["conflicts"]
    assert report["rebuild"] == {"applied": 3, "skipped_retracted": 0, "changed": []}
    assert json.loads((output / "report.json").read_text()) == report
    knowledge = sabueso.KnowledgeStore(output / "hypothetical_knowledge.db")
    baseline = knowledge.load(report["baseline_ref"])
    rebuilt = knowledge.load(report["rebuilt_ref"])
    assert (
        report["original_variant"]
        in baseline.get("features_positional.natural_variant")["value"]
    )
    assert (
        report["original_variant"]
        in rebuilt.get("features_positional.natural_variant")["value"]
    )
    for outcome in report["outcomes"]:
        historical = knowledge.source_assertion(outcome["source_assertion_ref"])
        assert historical == rebuilt.source_assertion_store.get(historical["id"])
        assert historical["source_metadata"]["curation"]["curator"] == (
            rehearsal.SIMULATED_CURATOR
        )
        for ref in outcome["compared_with_refs"]:
            assert knowledge.source_assertion(ref)
    assert (
        json.loads(rehearsal.PROPOSAL.read_text())["status"] == "draft_for_human_review"
    )


def test_a_numbering_mismatch_stops_the_rehearsal(tmp_path, monkeypatch):
    proposal = json.loads(rehearsal.PROPOSAL.read_text())
    proposal["placement"]["author_position"] = "105"
    changed = tmp_path / "proposal.json"
    changed.write_text(json.dumps(proposal))
    monkeypatch.setattr(rehearsal, "PROPOSAL", changed)
    output = tmp_path / "rehearsal"
    with pytest.raises(ValueError, match="identity/numbering basis failed"):
        rehearsal.rehearse(output)
    assert not (output / "hypothetical_curations.jsonl").exists()
