"""An original candidate permits an explicit new query, never a silent identity."""

import json
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.explorer._resolution import _query, _Resolution
from sabueso.explorer._service import _Service
from sabueso.explorer._source_choices import choice_details, declared_choices
from sabueso.explorer._workspace import read_workspace, save_workspace
from sabueso.resolver.entity_resolver import EntityResolution
from sabueso.tools.db.pubchem import FixturePubChemClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"


@pytest.fixture
def source(tmp_path, monkeypatch):
    from sabueso.tools.db import _http

    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("No live sources")
    )

    class Several(FixturePubChemClient):
        def structure(self, notation, structure):
            return {
                "retrieved_at": "Explicit synthetic ambiguity control",
                "cids": ["3717450", "999999999"],
                "fault": None,
            }

    calls = []
    client = Several(DATA)

    def resolve(query, **options):
        calls.append((query, options.copy()))
        return sabueso.resolve(query, pubchem_client=client, **options)

    return _Service(tmp_path, resolver=resolve), calls


def ambiguous(service):
    return service.resolve(
        {"kind": "smiles", "query": "CCO", "revision": "", "resolution_revision": ""}
    )


def choose(service, ref):
    return service.resolve(
        {
            "choice_ref": ref,
            "revision": service.session.revision if service.session else "",
            "resolution_revision": service.resolution.revision,
        },
        choice=True,
    )


def test_candidate_only_queries_the_chosen_source_record_and_keeps_ambiguity(source):
    service, calls = source
    original = ambiguous(service)
    assert original["panel"] is None and original["resolution"]["status"] == "ambiguous"
    assert len(calls) == 1
    choices = original["resolution"]["choices"]
    assert [c["entity_ref"] for c in choices] == [
        "pubchem:3717450",
        "pubchem:999999999",
    ]
    selected = choose(service, choices[0]["ref"])
    assert selected["panel"]["profile"] == "small_molecule"
    assert selected["resolution"]["kind"] == "pubchem"
    assert calls[-1][0] == "pubchem:3717450" and calls[-1][1]["unichem"] is False
    native = json.loads(selected["resolution"]["original_text"])["resolution"]
    assert "structure" not in native["decision"]
    previous = service.return_query(
        {
            "revision": service.session.revision,
            "resolution_revision": service.resolution.revision,
        }
    )
    assert (
        previous["resolution"]["original_text"]
        == original["resolution"]["original_text"]
    )
    assert previous["resolution"]["choices"] == choices and len(calls) == 2


def test_candidate_workspace_reopens_original_reports_without_queries(
    source, tmp_path, monkeypatch
):
    service, calls = source
    original = ambiguous(service)
    choose(service, original["resolution"]["choices"][0]["ref"])
    path = tmp_path / "candidates.json.gz"
    save_workspace(service, path)
    monkeypatch.setattr(
        Card, "__init__", lambda *a, **k: pytest.fail("No current Card")
    )
    session, result, history = read_workspace(path, tmp_path)
    assert session.explorer.mode == "saved" and result.kind == "pubchem"
    assert (
        history[0][1].panel()["original_text"]
        == original["resolution"]["original_text"]
    )
    assert history[0][1].panel()["choices"] == original["resolution"]["choices"]
    assert len(calls) == 2


@pytest.mark.parametrize("change", ["query", "basis", "order"])
def test_resealed_saved_candidates_cannot_rebind_source_basis_or_order(
    source, tmp_path, change
):
    service, _ = source
    ambiguous(service)
    path = tmp_path / "candidates.json"
    save_workspace(service, path, compression="none")
    value = json.loads(path.read_text())
    resolution = value["current"]["resolution"]
    if change == "order":
        resolution["choices"].reverse()
        resolution["panel"]["choices"].reverse()
    else:
        resolution["choices"][0]["value"][change] = "999999999"
    value["bundle_digest"] = digest(
        canonical_json({k: v for k, v in value.items() if k != "bundle_digest"})
    )
    before = service.response(service.panel())
    with pytest.raises(StorageError, match="source-declared basis"):
        service.load_reading(canonical_json(value).encode())
    assert service.response(service.panel()) == before


def test_unsupported_and_duplicate_candidates_stay_literal_without_identity_merge():
    original = {
        "status": "ambiguous",
        "decision": {
            "candidates": [
                "pubchem:3717450",
                "pubchem:3717450",
                "pubchem:../private",
                "other:one",
            ]
        },
    }
    choices = declared_choices("smiles", original)
    assert len(choices) == 2 and choices[0] == choices[1]
    assert len(original["decision"]["candidates"]) == 4


def test_protein_candidate_basis_is_detached_and_exact():
    first = {
        "entity_ref": "sabueso:protein:uniprot:P52270",
        "basis": {"reviewed": True, "organism": 5693},
    }
    resolution = EntityResolution(
        "ambiguous",
        candidates=[first],
        decision={"rules": ["Synthetic candidate control"]},
    )
    result = _Resolution("uniprot", "uniprot:synthetic", None, resolution)
    choice = next(iter(result.choices.values()))
    first["basis"]["organism"] = 9606
    assert choice["basis"]["basis"]["organism"] == 5693
    assert result.original["candidates"][0]["basis"]["organism"] == 5693


def test_source_details_are_separate_from_the_original_report(source):
    service, _ = source
    result = ambiguous(service)
    ref = result["resolution"]["choices"][0]["ref"]
    details = result["resolution"]["choice_details"][ref]
    assert details["title"] == "PubChem candidate record"
    assert "synthetic" in details["context"][0]
    assert "choice_details" not in service.resolution.panel()
    assert "choice_details" not in result["resolution"]["original_text"]


def test_choice_preview_preserves_unknown_false_and_zero_source_fields():
    resolution = EntityResolution(
        "ambiguous",
        candidates=[
            {
                "entity_ref": "sabueso:protein:uniprot:P52270",
                "basis": {"organism_name": None, "reviewed": False, "length": 0},
            }
        ],
    )
    result = _Resolution("uniprot", "uniprot:synthetic", None, resolution)
    context = next(iter(choice_details(result).values()))["context"]
    assert "Organism: null (retained)" in context
    assert "Reviewed: False" in context and "Recorded length: 0" in context


def test_source_preference_alternative_is_a_new_query_not_a_replacement():
    alternative = {
        "entity_ref": "sabueso:protein:uniprot:P52270",
        "basis": {"reviewed": True},
    }
    original = {
        "status": "resolved",
        "entity_ref": "sabueso:protein:uniprot:synthetic",
        "alternatives": [alternative],
        "policy": "prefer_reviewed@1",
    }
    choices = declared_choices("uniprot", original)
    assert choices[0]["entity_ref"] == alternative["entity_ref"]
    assert original["entity_ref"] == "sabueso:protein:uniprot:synthetic"


@pytest.mark.parametrize("value", ["0", "../3717450", "1;2", "1" * 21])
def test_pubchem_candidate_grammar_is_finite_and_does_not_query_sources(value):
    with pytest.raises(ArgumentError):
        _query("pubchem", value)
