"""Explicit single-source enrichment preserves captures and native outcomes."""

import asyncio
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.explorer._resolution import _resolve
from sabueso.explorer._service import _Service
from sabueso.explorer._workspace import read_workspace, save_workspace
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.alphafold import FixtureAlphaFoldClient
from sabueso.tools.db.interpro import FixtureInterProClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"


@pytest.fixture
def resolver(monkeypatch):
    from sabueso.tools.db import _http

    def forbidden(*args, **kwargs):
        pytest.fail("Source enrichment receiving must not access live sources")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    native = EntityResolver(FixtureUniProtClient(DATA))
    calls = []

    def resolve(query, **options):
        calls.append((query, dict(options)))
        return sabueso.resolve(
            query,
            **options,
            resolver=native,
            interpro_client=FixtureInterProClient(DATA),
            alphafold_client=FixtureAlphaFoldClient(DATA),
        )

    resolve.calls = calls
    return resolve


def request(service, **values):
    return {
        "kind": "uniprot",
        "query": "P52270",
        "revision": service.session.revision if service.session else "",
        "resolution_revision": service.resolution.revision
        if service.resolution
        else "",
        **values,
    }


@pytest.mark.parametrize(
    "source,option,name",
    [
        ("interpro", "family_sites", "InterPro"),
        ("alphafold", "predicted_structures", "AlphaFold DB"),
    ],
)
def test_explicit_source_is_a_new_native_capture_and_keeps_exact_return(
    tmp_path, resolver, source, option, name
):
    service = _Service(tmp_path, resolver=resolver)
    service.resolve(request(service))
    first = service.session
    before = first.panel()
    original = service.resolution.panel()["original_text"]
    service.resolve(request(service, protein_source=source))
    assert resolver.calls[-1] == (
        "uniprot:P52270",
        {"profile": "identity@1", option: True},
    )
    assert service.session is not first
    records = service.resolution.card.quality["enrichments"]
    selected = [row for row in records if row.get("source") == name]
    assert selected and all(row["request_options"] is True for row in selected)
    assert all(row["status"] == "added" for row in selected)
    assert not any(
        row.get("source") == ("AlphaFold DB" if source == "interpro" else "InterPro")
        for row in records
    )
    assert name in service.resolution.panel()["original_text"]
    count = len(resolver.calls)
    returned = service.return_query(
        {k: v for k, v in request(service).items() if k.endswith("revision")}
    )
    assert returned["panel"]["view_ref"] == before["view_ref"]
    assert returned["resolution"]["original_text"] == original
    assert len(resolver.calls) == count


@pytest.mark.parametrize("source", [None, True, [], {}, "structural_baseline@1", "all"])
def test_arbitrary_options_are_rejected_before_any_source(tmp_path, resolver, source):
    service = _Service(tmp_path, resolver=resolver)
    with pytest.raises(ArgumentError):
        service.resolve(request(service, protein_source=source))
    assert resolver.calls == [] and service.session is None


@pytest.mark.parametrize(
    "kind,query",
    [
        ("smiles", "CCO"),
        ("pdb", "1TCD"),
        ("disease", "MONDO:0014221"),
        ("pubchem", "1"),
    ],
)
def test_nonprotein_source_scope_is_refused_before_any_source(kind, query, resolver):
    with pytest.raises(ArgumentError):
        _resolve(kind, query, resolver, protein_source="alphafold")
    assert resolver.calls == []


@pytest.mark.parametrize("source", ["interpro", "alphafold"])
def test_enriched_workspace_reopens_inertly_with_exact_original_report(
    tmp_path, resolver, monkeypatch, source
):
    service = _Service(tmp_path, resolver=resolver)
    service.resolve(request(service))
    previous = service.resolution.panel()["original_text"]
    service.resolve(request(service, protein_source=source))
    report = service.resolution.panel()["original_text"]
    path = tmp_path / "enriched.json.gz"
    save_workspace(service, path, compression="gzip")

    def forbidden(*args, **kwargs):
        pytest.fail("Original enriched workspace must not construct Cards or query")

    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(sabueso, "resolve", forbidden)
    session, resolution, history = read_workspace(path, tmp_path)
    assert session.panel()["mode"] == "saved"
    assert resolution.panel()["original_text"] == report
    assert history[-1][1].panel()["original_text"] == previous


def test_background_enrichment_admission_keeps_reading_available(tmp_path, resolver):
    async def run():
        service = _Service(tmp_path, resolver=resolver)
        service.resolve(request(service))
        try:
            started = service.queries.start(request(service, protein_source="interpro"))
            assert started["protein_source"] == "interpro"
            for unused in range(500):
                if service.queries.descriptor()["state"] != "running":
                    break
                await asyncio.sleep(0.01)
            assert service.queries.descriptor()["state"] == "ready"
            assert len(resolver.calls) == 2
            result = service.queries.open(
                {
                    "job_ref": started["ref"],
                    "revision": service.session.revision,
                    "resolution_revision": service.resolution.revision,
                }
            )
            assert "InterPro" in result["resolution"]["original_text"]
        finally:
            await service.queries.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "source,option,client_option,client,name",
    [
        (
            "interpro",
            "family_sites",
            "interpro_client",
            FixtureInterProClient,
            "InterPro",
        ),
        (
            "alphafold",
            "predicted_structures",
            "alphafold_client",
            FixtureAlphaFoldClient,
            "AlphaFold DB",
        ),
    ],
)
def test_additional_source_failure_is_visible_and_does_not_become_absence(
    tmp_path, monkeypatch, source, option, client_option, client, name
):
    from sabueso.tools.db import _http

    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("No live source")
    )
    native = EntityResolver(FixtureUniProtClient(DATA))

    def resolve(query, **options):
        return sabueso.resolve(
            query,
            **options,
            resolver=native,
            **{client_option: client(DATA, failing={"P52270"})},
        )

    service = _Service(tmp_path, resolver=resolve)
    result = service.resolve(request(service, protein_source=source))
    assert result["resolution"]["status"] == "resolved"
    (record,) = [
        r for r in service.resolution.card.quality["enrichments"] if r["source"] == name
    ]
    assert record["status"] == "error" and record["request_options"] is True
    observations = result["resolution"]["source_access"]["rows"]
    (failed,) = [r for r in observations if r["source"] == name]
    assert failed["outcome"] == "failed" and failed["access"] == "fixture"
    assert result["resolution"]["source_access"]["outcome_counts"] == {
        "received": 1,
        "failed": 1,
    }
    assert "scientific outcomes" in result["resolution"]["source_access"]["scope"]


def test_source_access_preview_is_bounded_ephemeral_and_preserves_false():
    from types import SimpleNamespace

    from sabueso.explorer._resolution import source_access_preview

    records = [
        {
            "source": "X",
            "operation": "read",
            "outcome": "empty",
            "access": "fixture",
            "source_version": False,
        }
        for i in range(20)
    ]
    result = source_access_preview(SimpleNamespace(acquisition={"records": records}))
    assert result["count"] == 20 and len(result["rows"]) == 16
    assert result["outcome_counts"] == {"empty": 20}
    assert result["rows"][0]["source_version"] == "False"
    assert records[0]["source_version"] is False


def test_source_version_shows_original_value_and_basis():
    from types import SimpleNamespace

    from sabueso.explorer._resolution import source_access_preview

    result = source_access_preview(
        SimpleNamespace(
            acquisition={
                "records": [
                    {
                        "source_version": {
                            "value": "101.0",
                            "basis": "fixture_declared_release",
                        }
                    },
                    {"source_version": {"value": None, "basis": "not_stated"}},
                ]
            }
        )
    )
    assert result["rows"][0]["source_version"] == "101.0 (fixture_declared_release)"
    assert result["rows"][1]["source_version"] == "null (retained) (not_stated)"
