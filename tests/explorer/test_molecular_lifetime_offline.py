"""Owned runtime transitions are independent of retained Knowledge and identity."""

import asyncio
import secrets
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.explorer._molecular import _Molecular
from sabueso.explorer._service import _Service
from sabueso.explorer._session import _Session


@pytest.fixture
def provider(monkeypatch):
    state = SimpleNamespace(services=[], views=[], fail_start=False, fail_close=False)

    class Service:
        def __init__(self, *, render_on, listen_port):
            assert render_on == "client"
            self.port = listen_port or 19287
            self.channel = self
            self.closed = False
            self.token = secrets.token_hex(16)
            self.client_registration_count = 0
            self.client_render_ready = asyncio.Event()
            self.client_structure_complete = asyncio.Event()
            state.services.append(self)

        @property
        def origin(self):
            return f"http://127.0.0.1:{self.port}"

        @property
        def client_url(self):
            return self.origin + "/session/client#token=" + self.token

        async def start(self):
            if state.fail_start:
                raise OSError("synthetic occupied-port control")

        async def close(self):
            if state.fail_close:
                raise RuntimeError("synthetic cleanup failure")
            self.closed = True

    class View:
        def __init__(self, *, transport):
            self.closed = False
            self.camera = SimpleNamespace(get_snapshot=lambda: {"synthetic": True})
            self.active_selection = SimpleNamespace(atom_indices=[0])
            state.views.append(self)

        def load(self, path):
            self.path = Path(path)
            self.loaded = self.path.read_bytes()

        def close(self):
            self.closed = True

    monkeypatch.setitem(
        sys.modules,
        "molsysviewer.remote",
        SimpleNamespace(RemoteSessionService=Service),
    )
    monkeypatch.setitem(
        sys.modules, "molsysviewer.viewer", SimpleNamespace(MolSysView=View)
    )
    return state


def model(tmp_path):
    path = tmp_path / "input.pdb"
    path.write_bytes(b"HEADER    synthetic lifetime-only control\nEND\n")
    return _Molecular(path)


def test_reopen_uses_initial_copy_fresh_runtime_and_same_admitted_origin(
    tmp_path, provider
):
    async def run():
        m = model(tmp_path)
        independent = model(tmp_path)
        try:
            await m.start()
            await independent.start()
            original = m.descriptor()
            first_service, first_view = m.service, m.view
            raw = m.target.read_bytes()
            m.source.unlink()
            await m.close_preview()
            closed = m.descriptor()
            assert closed["status"] == "closed" and closed["can_reopen"]
            assert not closed["client_url"] and not closed["can_close"]
            assert closed["lifecycle_revision"] != original["lifecycle_revision"]
            assert first_service.closed and first_view.closed and m.directory
            assert not independent.service.closed and not independent.view.closed
            await m.reopen()
            current = m.descriptor()
            assert current["status"] == "experimental"
            assert current["lifecycle_revision"] != closed["lifecycle_revision"]
            assert current["client_url"] != original["client_url"]
            assert m.service.origin == m.allowed_origin == first_service.origin
            assert m.view.loaded == raw and m.target == first_view.path
            assert current["initial_input_digest"] == original["initial_input_digest"]
            assert current["correspondence"] == "not_established"
            directory = Path(m.directory.name)
        finally:
            await m.close()
            await independent.close()
        assert not directory.exists() and not m.can_reopen
        with pytest.raises(ArgumentError):
            await m.reopen()

    asyncio.run(run())


def test_occupied_origin_failure_keeps_original_copy_and_allows_explicit_retry(
    tmp_path, provider
):
    async def run():
        m = model(tmp_path)
        try:
            await m.start()
            origin, target, digest = m.allowed_origin, m.target, m.input_digest
            await m.close_preview()
            provider.fail_start = True
            await m.reopen()
            assert m.descriptor()["status"] == "unavailable"
            assert "occupied-port" in m.error and m.can_reopen
            assert m.allowed_origin == origin and target.exists()
            assert m.service is None and m.view is None
            assert provider.services[-1].closed and provider.views[-1].closed
            provider.fail_start = False
            await m.reopen()
            assert (
                m.origin == origin and m.target == target and m.input_digest == digest
            )
            assert m.error is None and not m.can_reopen
        finally:
            await m.close()

    asyncio.run(run())


def test_cleanup_failure_retains_owner_and_refuses_new_runtime_until_retry(
    tmp_path, provider
):
    async def run():
        m = model(tmp_path)
        try:
            await m.start()
            service = m.service
            provider.fail_close = True
            await m.close_preview()
            assert m.service is service and not m.can_reopen and m.directory
            assert m.descriptor()["can_close"] and "cleanup failed" in m.error
            with pytest.raises(ArgumentError):
                await m.reopen()
            provider.fail_close = False
            await m.close_preview()
            assert service.closed and m.can_reopen
        finally:
            provider.fail_close = False
            await m.close()

    asyncio.run(run())


def test_changed_owned_snapshot_is_refused_without_rereading_caller_input(
    tmp_path, provider
):
    async def run():
        m = model(tmp_path)
        try:
            await m.start()
            raw = m.source.read_bytes()
            await m.close_preview()
            m.target.write_bytes(b"changed owned capture")
            await m.reopen()
            assert "captured initial molecular input changed" in m.error
            assert len(provider.services) == 1 and m.source.read_bytes() == raw
            assert m.descriptor()["client_url"] is None and m.can_reopen
        finally:
            await m.close()

    asyncio.run(run())


def test_changed_runtime_origin_is_not_added_to_the_allowlist(tmp_path, provider):
    async def run():
        m = model(tmp_path)
        try:
            await m.start()
            origin = m.allowed_origin
            await m.close_preview()
            cls = type(provider.services[0])
            original = cls.start

            async def changed(service):
                service.port += 1

            cls.start = changed
            await m.reopen()
            assert "changed its admitted origin" in m.error
            assert m.allowed_origin == origin and m.origin is None and m.can_reopen
            cls.start = original
        finally:
            await m.close()

    asyncio.run(run())


def test_loopback_commands_keep_knowledge_available_during_owned_close(
    tmp_path, provider
):
    async def run():
        from aiohttp import CookieJar
        from aiohttp.test_utils import TestClient, TestServer

        card = Card(meta={"entity_type": "protein"})
        card.unknown_stored["synthetic"] = {"value": 1.0}
        service = _Service(tmp_path, _Session.from_card(card, tmp_path))
        m = service.molecular = model(tmp_path)
        await m.start()
        entered, release = asyncio.Event(), asyncio.Event()
        original_close = m.service.close

        async def pending_close():
            entered.set()
            await release.wait()
            await original_close()

        m.service.close = pending_close
        try:
            async with TestClient(
                TestServer(service.application()), cookie_jar=CookieJar(unsafe=True)
            ) as client:
                service.origin = str(client.make_url("/")).rstrip("/")
                body = {"lifecycle_revision": m.revision}
                assert (
                    await client.post("/api/molecular-close", json=body)
                ).status == 403
                headers = {"Origin": service.origin}
                await client.post(
                    "/auth", json={"token": service.token}, headers=headers
                )
                for wrong in ({}, [], {**body, "path": "/etc/passwd"}):
                    assert (
                        await client.post(
                            "/api/molecular-close", json=wrong, headers=headers
                        )
                    ).status == 400
                assert (
                    await client.post(
                        "/api/molecular-close",
                        json=body,
                        headers={"Origin": "https://foreign.invalid"},
                    )
                ).status == 403
                before = service.panel()
                pending = asyncio.ensure_future(
                    client.post("/api/molecular-close", json=body, headers=headers)
                )
                await asyncio.wait_for(entered.wait(), 2)
                current = await asyncio.wait_for(client.get("/api/panel"), 2)
                result = await current.json()
                assert (
                    result["panel"] == before
                    and result["molecular"]["status"] == "closing"
                )
                assert m.allowed_origin in current.headers["Content-Security-Policy"]
                reading = await client.post(
                    "/api/action",
                    json={
                        "name": "topic",
                        "topic": "content",
                        "revision": before["revision"],
                    },
                    headers=headers,
                )
                assert reading.status == 200
                later = service.panel()
                release.set()
                assert (await pending).status == 200
                stale = await client.post(
                    "/api/molecular-reopen", json=body, headers=headers
                )
                assert stale.status == 400 and len(provider.services) == 1
                reopened = await client.post(
                    "/api/molecular-reopen",
                    json={"lifecycle_revision": m.revision},
                    headers=headers,
                )
                assert reopened.status == 200
                assert service.panel() == later
                assert (await reopened.json())["molecular"]["status"] == "experimental"
                assert card.unknown_stored["synthetic"]["value"] == 1.0
        finally:
            release.set()
            await m.close()

    asyncio.run(run())
