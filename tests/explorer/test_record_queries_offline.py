"""Exact retained link queries acquire a fresh record without rewriting originals."""

import asyncio
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.explorer._deck_session import _DeckSession
from sabueso.explorer._record_queries import current_item_query, reference_query
from sabueso.explorer._service import _Service
from sabueso.explorer._session import _Session
from sabueso.explorer._workspace import read_workspace, save_workspace
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.mondo import FixtureMONDOClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.pubchem import FixturePubChemClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"


def synthetic_card(reference):
    card = Card(
        meta={"card_id": "sabueso:protein:uniprot:P52270", "entity_type": "protein"}
    )
    assertion = make_source_assertion(
        "relationships.associated_with",
        reference,
        "Synthetic",
        "record-query-admission-control",
        "2026-11-13",
        subject_ref="uniprot:P52270",
    )
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(
        make_relationship(
            "uniprot:P52270",
            "associated_with",
            reference,
            source_assertion_ids=[assertion["id"]],
        )
    )
    return card


def act(service, name, **extra):
    return service.session.dispatch(
        {"revision": service.session.revision, "name": name, **extra}
    )


def links(service):
    act(service, "topic", topic="content")
    act(
        service,
        "open",
        item_ref=next(
            row["ref"]
            for row in service.panel()["items"]
            if row["label"] == "Relationships"
        ),
    )
    act(service, "related", item_ref=service.panel()["items"][0]["ref"])
    reading = (
        service.session.card_session
        if isinstance(service.session, _DeckSession)
        else service.session
    )
    return next(
        item.item_ref
        for item in reading.current.items()
        if item.cells["role"].value == "object"
    )


def body(service, item):
    return {
        "revision": service.session.revision,
        "resolution_revision": service.resolution.revision
        if service.resolution
        else "",
        "item_ref": item,
    }


@pytest.fixture
def resolver(monkeypatch):
    from sabueso.tools.db import _http

    monkeypatch.setattr(
        _http,
        "_urlopen",
        lambda *a, **k: pytest.fail("Record queries must use frozen public clients"),
    )
    native = EntityResolver(
        FixtureUniProtClient(DATA), rcsb_client=FixtureRCSBClient(DATA)
    )
    calls = []

    def resolve(query, **options):
        calls.append((query, options.copy()))
        if query.startswith("pdb.ligand:"):
            options["ccd_client"] = FixtureCCDClient(DATA)
        elif query.startswith("pubchem:"):
            options["pubchem_client"] = FixturePubChemClient(DATA)
        elif options.get("entity_type") == "disease":
            options["mondo_client"] = FixtureMONDOClient(DATA)
        else:
            options["resolver"] = native
        return sabueso.resolve(query, **options)

    resolve.calls = calls
    return resolve


async def ready(service):
    async def wait():
        while service.queries.descriptor()["state"] == "running":
            await asyncio.sleep(0.01)

    await asyncio.wait_for(wait(), 10)
    assert service.queries.descriptor()["state"] == "ready"


@pytest.mark.parametrize(
    "reference,kind,canonical,nature",
    [
        ("uniprot:P52270", "uniprot", "uniprot:P52270", "protein"),
        ("sabueso:protein:uniprot:P52270", "uniprot", "uniprot:P52270", "protein"),
        ("pdb.ligand:BTS", "pdb_ligand", "pdb.ligand:BTS", "small_molecule"),
        ("pubchem:3717450", "pubchem", "pubchem:3717450", "small_molecule"),
        ("mondo:MONDO:0001444", "disease", "mondo:MONDO:0001444", "disease"),
        ("pdb:1TCD", "pdb", "pdb:1TCD", None),
    ],
)
def test_fresh_record_query_keeps_original_relationship_and_exact_return(
    tmp_path, resolver, reference, kind, canonical, nature
):
    async def run():
        original = synthetic_card(reference)
        service = _Service(
            tmp_path, _Session.from_card(original, tmp_path), resolver=resolver
        )
        item = links(service)
        previous = service.panel()
        assert current_item_query(service.session, item)["reference"] == reference
        assert (
            next(row for row in previous["items"] if row["ref"] == item)[
                "query_record"
            ]["kind"]
            == kind
        )
        before = original.to_dict()
        try:
            job = service.queries.start(body(service, item), link=True)
            await ready(service)
            result = service.queries.open(
                {
                    "job_ref": job["ref"],
                    "revision": service.session.revision,
                    "resolution_revision": "",
                }
            )
            assert (
                resolver.calls[0][0] == canonical
                and resolver.calls[0][1]["profile"] == "identity@1"
            )
            assert result["resolution"]["kind"] == kind
            if nature:
                assert result["panel"]["profile"] == nature
            else:
                assert result["resolution"]["has_card"] is False
            assert original.to_dict() == before
            restored = service.return_query(
                {
                    "revision": service.session.revision,
                    "resolution_revision": service.resolution.revision,
                }
            )
            assert restored["panel"]["view_ref"] == previous["view_ref"]
            assert (
                restored["panel"]["items"] == previous["items"]
                and len(resolver.calls) == 1
            )
        finally:
            await service.queries.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "reference",
    [
        None,
        True,
        {},
        "P52270",
        "Triosephosphate isomerase",
        "https://example.org/uniprot:P52270",
        "chembl:CHEMBL123",
        "smiles:CCO",
        "uniprot:P52270@sha256:abc",
        "uniprot:P52270#SA_1",
        "sabueso:protein:uniprot:P52270@sha256:abc",
        "pubchem:0",
        "pdb.ligand:../../x",
        "mondo:MONDO:1",
        " uniprot:P52270",
        "sabueso:protein:pubchem:3717450",
        "sabueso:disease:uniprot:P52270",
        "sabueso:small_molecule:uniprot:P52270",
    ],
)
def test_names_ambiguous_namespaces_versions_urls_and_foreign_grammars_are_not_routes(
    reference,
):
    assert reference_query(reference) is None


def test_lookalike_extension_and_invisible_item_cannot_start_a_query(
    tmp_path, resolver
):
    async def run():
        card = Card()
        card.unknown_stored["fake"] = {"role": "object", "target_ref": "uniprot:P52270"}
        service = _Service(
            tmp_path, _Session.from_card(card, tmp_path), resolver=resolver
        )
        try:
            with pytest.raises(ArgumentError):
                service.queries.start(body(service, "invented"), link=True)
            assert all(row["query_record"] is None for row in service.panel()["items"])
            assert resolver.calls == [] and service.queries.job is None
        finally:
            await service.queries.close()

    asyncio.run(run())


def test_stale_or_rebound_link_is_refused_before_sources(tmp_path, resolver):
    async def run():
        service = _Service(
            tmp_path,
            _Session.from_card(synthetic_card("pdb.ligand:BTS"), tmp_path),
            resolver=resolver,
        )
        item = links(service)
        previous = body(service, item)
        act(service, "back")
        try:
            with pytest.raises(ArgumentError):
                service.queries.start(previous, link=True)
            with pytest.raises(ArgumentError):
                service.queries.start(body(service, item), link=True)
            with pytest.raises(ArgumentError):
                service.queries.start(
                    {**body(service, item), "target_ref": "uniprot:P60174"}, link=True
                )
            assert resolver.calls == [] and service.queries.job is None
        finally:
            await service.queries.close()

    asyncio.run(run())


@pytest.mark.parametrize("in_deck", [False, True])
def test_saved_original_link_queries_preserve_whole_workspace_and_deck_return(
    tmp_path, resolver, monkeypatch, in_deck
):
    async def run():
        card = synthetic_card("pdb.ligand:BTS")
        session = (
            _DeckSession(Deck([card, card]), tmp_path)
            if in_deck
            else _Session.from_card(card, tmp_path)
        )
        service = _Service(tmp_path, session, resolver=resolver)
        entry = service.panel()
        if in_deck:
            selected = act(service, "search", text="P52270")
            act(service, "open", item_ref=selected["items"][1]["ref"])
            entry = selected
        links(service)
        previous = service.panel()
        before = tmp_path / "before.json.gz"
        save_workspace(service, before, compression="gzip")
        original_bytes = before.read_bytes()
        with monkeypatch.context() as no_cards:
            no_cards.setattr(
                Card,
                "__init__",
                lambda *a, **k: pytest.fail(
                    "Original reading cannot reconstruct a Card"
                ),
            )
            service.session, service.resolution, service.resolution_history = (
                read_workspace(before, tmp_path)
            )
        restored_item = next(
            row["ref"]
            for row in service.panel()["items"]
            if (row.get("query_record") or {}).get("reference") == "pdb.ligand:BTS"
        )
        try:
            job = service.queries.start(body(service, restored_item), link=True)
            await ready(service)
            service.queries.open(
                {
                    "job_ref": job["ref"],
                    "revision": service.session.revision,
                    "resolution_revision": "",
                }
            )
            after = tmp_path / "after.json.gz"
            save_workspace(service, after, compression="gzip")
            with monkeypatch.context() as no_cards:
                no_cards.setattr(
                    Card, "__init__", lambda *a, **k: pytest.fail("No new Card")
                )
                service.session, service.resolution, service.resolution_history = (
                    read_workspace(after, tmp_path)
                )
            service.return_query(
                {
                    "revision": service.session.revision,
                    "resolution_revision": service.resolution.revision,
                }
            )
            assert service.panel()["view_ref"] == previous["view_ref"]
            if in_deck:
                assert service.panel()["deck_context"]["entry_position"] == 1
                returned = act(service, "deck")
                assert (
                    returned["view_ref"] == entry["view_ref"]
                    and returned["items"] == entry["items"]
                )
            assert before.read_bytes() == original_bytes and len(resolver.calls) == 1
        finally:
            await service.queries.close()

    asyncio.run(run())


def test_nonvisible_native_link_and_source_rows_cannot_be_queried(tmp_path, resolver):
    from sabueso.explorer._record_queries import item_query

    card = synthetic_card("pdb.ligand:BTS")
    original = card.relationship_store.to_list()[0]
    references = list(original["source_assertion_ids"])
    for index in range(42):
        assertion = make_source_assertion(
            "relationships.associated_with",
            "pdb.ligand:BTS",
            "Synthetic",
            f"many-source-control-{index}",
            "2026-11-13",
            subject_ref="uniprot:P52270",
        )
        card.source_assertion_store.add(assertion)
        references.append(assertion["id"])
    # Rebuild the single declared relationship with its complete independent basis.
    from sabueso.core.relationship_store import RelationshipStore

    card.relationship_store = RelationshipStore(
        [
            make_relationship(
                "uniprot:P52270",
                "associated_with",
                "pdb.ligand:BTS",
                source_assertion_ids=references,
            )
        ]
    )
    service = _Service(tmp_path, _Session.from_card(card, tmp_path), resolver=resolver)
    ref = links(service)
    with pytest.raises(ArgumentError):
        current_item_query(service.session, ref)
    assert all(row["query_record"] is None for row in service.panel()["items"])
    act(service, "page", offset=40)
    assert current_item_query(service.session, ref)["query"] == "pdb.ligand:BTS"
    source = next(
        item
        for item in service.session.current.items()
        if item.cells["role"].value == "source"
    )
    assert item_query(service.session.current, source) is None
    assert resolver.calls == []


def test_real_http_link_query_requires_capability_origin_exact_context_and_no_target_override(
    tmp_path, resolver
):
    async def run():
        from aiohttp import CookieJar
        from aiohttp.test_utils import TestClient, TestServer

        service = _Service(
            tmp_path,
            _Session.from_card(synthetic_card("pdb.ligand:BTS"), tmp_path),
            resolver=resolver,
        )
        item = links(service)
        async with TestClient(
            TestServer(service.application()), cookie_jar=CookieJar(unsafe=True)
        ) as client:
            service.origin = str(client.make_url("/")).rstrip("/")
            headers = {"Origin": service.origin}
            assert (
                await client.post(
                    "/api/query-link", json=body(service, item), headers=headers
                )
            ).status == 403
            await client.post("/auth", json={"token": service.token}, headers=headers)
            assert (
                await client.post(
                    "/api/query-link",
                    json=body(service, item),
                    headers={"Origin": "https://foreign.invalid"},
                )
            ).status == 403
            assert (
                await client.post(
                    "/api/query-link",
                    json={**body(service, item), "query": "pdb.ligand:PGA"},
                    headers=headers,
                )
            ).status == 400
            assert resolver.calls == []
            response = await client.post(
                "/api/query-link", json=body(service, item), headers=headers
            )
            assert response.status == 200
            await ready(service)
            job = (await response.json())["query_job"]
            response = await client.post(
                "/api/query-open",
                json={
                    "job_ref": job["ref"],
                    "revision": service.session.revision,
                    "resolution_revision": "",
                },
                headers=headers,
            )
            assert (
                response.status == 200
                and (await response.json())["panel"]["profile"] == "small_molecule"
            )
        assert not service.queries.descriptor()["worker_running"]

    asyncio.run(run())
