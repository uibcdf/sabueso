"""Bounded background queries do not block reading or replace a changed context."""

import asyncio
import threading
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.explorer._service import _Service
from sabueso.explorer._session import _Session
from sabueso.resolver import EntityResolver, FixtureUniProtClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"


def controlled(tmp_path, monkeypatch, *, fail=False):
    from sabueso.tools.db import _http

    def forbidden(*args, **kwargs):
        pytest.fail("Background receiving must not access live sources")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    native = EntityResolver(FixtureUniProtClient(DATA))
    service = _Service(
        tmp_path,
        _Session.from_card(Card(), tmp_path),
        resolver=lambda query, **options: sabueso.resolve(
            query, **options, resolver=native
        ),
    )
    original = service._prepare_resolution
    entered, release = threading.Event(), threading.Event()

    def prepare(kind, query):
        entered.set()
        if not release.wait(10):
            raise TimeoutError("Synthetic source not released")
        if fail:
            raise ValueError("Synthetic provider failure")
        return original(kind, query)

    service._prepare_resolution = prepare
    return service, entered, release


def request(service):
    return {
        "kind": "uniprot",
        "query": "P52270",
        "revision": service.session.revision,
        "resolution_revision": service.resolution.revision
        if service.resolution
        else "",
    }


async def until(predicate):
    async def wait():
        while not predicate():
            await asyncio.sleep(0.01)

    await asyncio.wait_for(wait(), 5)


def test_source_wait_does_not_block_reading_and_result_requires_current_adoption(
    tmp_path, monkeypatch
):
    async def run():
        service, entered, release = controlled(tmp_path, monkeypatch)
        try:
            body = request(service)
            started = service.queries.start(body)
            await until(entered.is_set)
            assert started["state"] == "running" and started["worker_running"]
            panel = await asyncio.wait_for(
                asyncio.to_thread(
                    service.session.dispatch,
                    {
                        "name": "topic",
                        "topic": "content",
                        "revision": service.session.revision,
                    },
                ),
                3,
            )
            assert (
                not release.is_set()
                and service.queries.descriptor()["state"] == "running"
            )
            original_ref = panel["view_ref"]
            release.set()
            await until(lambda: service.queries.descriptor()["state"] == "ready")
            before = service.panel()
            with pytest.raises(ArgumentError):
                service.queries.open(
                    {
                        "job_ref": started["ref"],
                        "revision": body["revision"],
                        "resolution_revision": "",
                    }
                )
            assert service.panel() == before
            adopted = service.queries.open(
                {
                    "job_ref": started["ref"],
                    "revision": service.session.revision,
                    "resolution_revision": "",
                }
            )
            assert (
                adopted["panel"]["profile"] == "protein"
                and adopted["query_job"]["state"] == "opened"
            )
            restored = service.return_query(
                {
                    "revision": service.session.revision,
                    "resolution_revision": service.resolution.revision,
                }
            )
            assert (
                restored["panel"]["view_ref"] == original_ref
                and restored["resolution"] is None
            )
        finally:
            release.set()
            await service.queries.close()
        assert not service.queries.descriptor()["worker_running"]

    asyncio.run(run())


def test_cancel_discards_result_without_claiming_provider_interruption_or_queue(
    tmp_path, monkeypatch
):
    async def run():
        service, entered, release = controlled(tmp_path, monkeypatch)
        try:
            before = service.panel()
            started = service.queries.start(request(service))
            await until(entered.is_set)
            cancelled = service.queries.cancel({"job_ref": started["ref"]})
            assert cancelled["state"] == "cancelled" and cancelled["worker_running"]
            assert "may finish" in cancelled["cancellation_scope"]
            with pytest.raises(ArgumentError):
                service.queries.start(request(service))
            with pytest.raises(ArgumentError):
                service.queries.open(
                    {
                        "job_ref": started["ref"],
                        "revision": service.session.revision,
                        "resolution_revision": "",
                    }
                )
            release.set()
            await until(lambda: not service.queries.descriptor()["worker_running"])
            await asyncio.sleep(0.01)
            assert service.panel() == before and service.queries.job["prepared"] is None
            next_job = service.queries.start(request(service))
            assert next_job["ref"] != started["ref"]
            with pytest.raises(ArgumentError):
                service.queries.cancel({"job_ref": started["ref"]})
            await until(lambda: service.queries.descriptor()["state"] == "ready")
        finally:
            release.set()
            await service.queries.close()

    asyncio.run(run())


def test_unexpected_failure_is_distinct_from_absence_and_preserves_reading(
    tmp_path, monkeypatch
):
    async def run():
        service, entered, release = controlled(tmp_path, monkeypatch, fail=True)
        try:
            before = service.panel()
            service.queries.start(request(service))
            release.set()
            await until(lambda: service.queries.descriptor()["state"] == "failed")
            assert service.panel() == before
            assert isinstance(service.queries.job["exception"], ValueError)
            assert service.queries.descriptor()["error"]
            assert service.resolution is None
        finally:
            release.set()
            await service.queries.close()

    asyncio.run(run())


def test_actual_http_job_requires_same_origin_capability_and_exact_refs(
    tmp_path, monkeypatch
):
    async def run():
        from aiohttp import CookieJar
        from aiohttp.test_utils import TestClient, TestServer

        service, entered, release = controlled(tmp_path, monkeypatch)
        try:
            async with TestClient(
                TestServer(service.application()), cookie_jar=CookieJar(unsafe=True)
            ) as client:
                service.origin = str(client.make_url("/")).rstrip("/")
                headers = {"Origin": service.origin}
                assert (await client.get("/api/query")).status == 403
                await client.post(
                    "/auth", json={"token": service.token}, headers=headers
                )
                assert (
                    await client.post(
                        "/api/query-start",
                        json=request(service),
                        headers={"Origin": "http://foreign.invalid"},
                    )
                ).status == 403
                assert service.queries.job is None
                response = await client.post(
                    "/api/query-start", json=request(service), headers=headers
                )
                assert response.status == 200
                job = (await response.json())["query_job"]
                await until(entered.is_set)
                assert (await client.get("/api/panel")).status == 200
                assert (
                    await client.post(
                        "/api/query-cancel",
                        json={"job_ref": "foreign"},
                        headers=headers,
                    )
                ).status == 400
                cancelled = await client.post(
                    "/api/query-cancel", json={"job_ref": job["ref"]}, headers=headers
                )
                assert (
                    cancelled.status == 200
                    and (await cancelled.json())["query_job"]["state"] == "cancelled"
                )
                release.set()
                await until(lambda: not service.queries.descriptor()["worker_running"])
        finally:
            release.set()
            await service.queries.close()
        assert service.queries.closed.is_set()

    asyncio.run(run())
