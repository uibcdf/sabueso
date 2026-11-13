"""Actual native resolution with frozen public sources and explicit user actions."""

import asyncio
import json
from pathlib import Path

import pytest

import sabueso
from sabueso.core.errors import ArgumentError
from sabueso.explorer._resolution import _resolve
from sabueso.explorer._service import _Service
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.mondo import FixtureMONDOClient
from sabueso.tools.db.pubchem import FixturePubChemClient

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "temp_data"
LOOKUPS = json.loads((DATA / "pubchem/structures.json").read_text())["lookups"]


@pytest.fixture
def resolver(monkeypatch):
    import requests

    def refuse(*args, **kwargs):
        raise AssertionError("An offline application action attempted a network call")

    monkeypatch.setattr(requests.sessions.Session, "request", refuse)
    native = EntityResolver(
        FixtureUniProtClient(DATA), rcsb_client=FixtureRCSBClient(DATA)
    )
    calls = []

    def resolve(query, **options):
        calls.append((query, dict(options)))
        if query.startswith("smiles:"):
            options["pubchem_client"] = FixturePubChemClient(DATA)
        elif options.get("entity_type") == "disease":
            options["mondo_client"] = FixtureMONDOClient(DATA)
        else:
            options["resolver"] = native
        return sabueso.resolve(query, **options)

    resolve.calls = calls
    return resolve


@pytest.mark.parametrize(
    "kind,query,nature",
    [
        ("uniprot", "P52270", "protein"),
        ("smiles", LOOKUPS[0]["query"], "small_molecule"),
        ("disease", "MONDO:0014221", "disease"),
    ],
)
def test_source_stated_identity_retains_native_resolution(
    kind, query, nature, resolver
):
    result = _resolve(kind, query, resolver)
    assert result.card.meta["entity_type"] == nature
    assert result.panel()["status"] == "resolved"
    original = json.loads(result.panel()["original_text"])
    assert original["resolution"]["decision"]["route"]["entity_type"] == nature
    assert original["resolution"]["decision"]["profile"]["name"] == "identity@1"
    assert len(resolver.calls) == 1
    if kind == "smiles":
        assert resolver.calls[0][1]["unichem"] is False
        assert (
            original["resolution"]["decision"]["structure"]["basis"]
            == "pubchem_structure_lookup"
        )


def test_pdb_does_not_fabricate_a_card_or_acquire_its_proteins(resolver):
    result = _resolve("pdb", "1TCD", resolver)
    assert result.card is None and result.panel()["status"] == "resolved"
    assert len(resolver.calls) == 1
    assert {x["entity_ref"] for x in result.panel()["choices"]} == {
        "sabueso:protein:uniprot:P52270"
    }
    assert "has_structure" in result.panel()["original_text"]


@pytest.mark.parametrize("index,status", [(3, "not_found"), (4, "unsupported")])
def test_distinct_source_outcomes_are_preserved(index, status, resolver):
    result = _resolve("smiles", LOOKUPS[index]["query"], resolver)
    assert result.card is None and result.panel()["status"] == status
    assert "decision" in json.loads(result.panel()["original_text"])["resolution"]


def test_source_ambiguity_and_failure_are_not_absence():
    class Several(FixturePubChemClient):
        def structure(self, notation, structure):
            return {
                "retrieved_at": "synthetic control",
                "cids": ["1", "2"],
                "fault": None,
            }

    result = _resolve(
        "smiles",
        "CCO",
        lambda query, **options: sabueso.resolve(
            query, **options, pubchem_client=Several()
        ),
    )
    assert result.card is None and result.panel()["status"] == "ambiguous"
    assert json.loads(result.panel()["original_text"])["resolution"]["decision"][
        "candidates"
    ] == ["pubchem:1", "pubchem:2"]
    failing = EntityResolver(FixtureUniProtClient(DATA, failing={"P52270"}))
    result = _resolve(
        "uniprot",
        "P52270",
        lambda query, **options: sabueso.resolve(query, **options, resolver=failing),
    )
    assert result.card is None and result.panel()["status"] == "error"


@pytest.mark.parametrize(
    "kind,query",
    [
        ("disease", "a disease name"),
        ("pdb", "bad id"),
        ("uniprot", "a protein name"),
        ("python", "pass"),
        ([], "P52270"),
        ("smiles", ""),
        ("smiles", "C" * 8193),
    ],
)
def test_invalid_inputs_make_no_acquisitions(kind, query, resolver):
    with pytest.raises(ArgumentError):
        _resolve(kind, query, resolver)
    assert resolver.calls == []


def test_explicit_choice_keeps_prior_reading_until_a_card_is_received(
    tmp_path, resolver
):
    pytest.importorskip("aiohttp")
    service = _Service(tmp_path, resolver=resolver)
    result = service.resolve(
        {
            "kind": "uniprot",
            "query": "P52270",
            "revision": "",
            "resolution_revision": "",
        }
    )
    saved_session = service.session

    def request(**extra):
        return {
            "revision": service.session.revision,
            "resolution_revision": service.resolution.revision,
            **extra,
        }

    result = service.resolve(request(kind="pdb", query="1TCD"))
    assert service.session is saved_session
    choice = result["resolution"]["choices"][0]["ref"]
    stale = request(choice_ref=choice)
    count = len(resolver.calls)
    service.session.dispatch(
        {"name": "topic", "topic": "sequence", "revision": service.session.revision}
    )
    assert len(resolver.calls) == count  # Viewing is source-free.
    with pytest.raises(ArgumentError, match="workspace changed"):
        service.resolve(stale, choice=True)
    service.resolve(request(choice_ref=choice), choice=True)
    assert service.session is not saved_session
    assert len(resolver.calls) == count + 1
    service.return_query(request())
    assert service.resolution.kind == "pdb"
    assert service.session.current.title == saved_session.current.title
    assert service.session.current.view_ref == saved_session.current.view_ref
    assert len(resolver.calls) == count + 1
    # A returned snapshot's history stays independent of the earlier live visit.
    service.session.dispatch({"name": "back", "revision": service.session.revision})
    assert service.session.current.view_ref != saved_session.current.view_ref


def test_real_loopback_rejects_stale_duplicate_queries_and_foreign_origin(
    tmp_path, resolver
):
    pytest.importorskip("aiohttp")

    async def run():
        from aiohttp import CookieJar
        from aiohttp.test_utils import TestClient, TestServer

        service = _Service(tmp_path, resolver=resolver)
        async with TestClient(
            TestServer(service.application()), cookie_jar=CookieJar(unsafe=True)
        ) as client:
            service.origin = str(client.make_url("/")).rstrip("/")
            await client.post(
                "/auth",
                json={"token": service.token},
                headers={"Origin": service.origin},
            )
            body = {
                "kind": "pdb",
                "query": "1TCD",
                "revision": "",
                "resolution_revision": "",
            }
            assert (
                await client.post(
                    "/api/resolve",
                    json=body,
                    headers={"Origin": "https://foreign.invalid"},
                )
            ).status == 403
            responses = await asyncio.gather(
                *(
                    client.post(
                        "/api/resolve", json=body, headers={"Origin": service.origin}
                    )
                    for _ in range(2)
                )
            )
            assert sorted(response.status for response in responses) == [200, 400]
            assert len(resolver.calls) == 1
            from sabueso.core.card import Card

            response = await client.post(
                "/api/card",
                json=Card().to_dict(),
                headers={"Origin": service.origin, "X-Sabueso-Revision": ""},
            )
            assert response.status == 400  # An earlier blank entry is stale too.
            result = await (await client.get("/api/panel")).json()
            assert (
                result["panel"] is None and result["resolution"]["status"] == "resolved"
            )
            body = {
                "revision": "",
                "resolution_revision": result["resolution"]["revision"],
                "choice_ref": "invented",
            }
            assert (
                await client.post(
                    "/api/resolve-choice", json=body, headers={"Origin": service.origin}
                )
            ).status == 400
            assert len(resolver.calls) == 1

    asyncio.run(run())
