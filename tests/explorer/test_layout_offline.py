"""Presentation persistence does not save or reconstruct scientific context."""

import asyncio
import json
from copy import deepcopy

import pytest

from sabueso.core.errors import ArgumentError
from sabueso.explorer._layout import FORMAT, RENDERER, _Layout, _validate


def presentation():
    return {
        "format": FORMAT,
        "renderer": RENDERER,
        "workspace": {
            "grid": {
                "root": {
                    "type": "branch",
                    "data": [
                        {
                            "type": "leaf",
                            "data": {
                                "id": "1",
                                "views": ["reading"],
                                "activeView": "reading",
                            },
                            "size": 800,
                        }
                    ],
                },
                "width": 800,
                "height": 600,
                "orientation": "HORIZONTAL",
            },
            "panels": {
                "reading": {
                    "id": "reading",
                    "contentComponent": "reading",
                    "title": "Knowledge",
                    "renderer": "always",
                }
            },
            "activeGroup": "1",
        },
    }


def test_presentation_round_trip_is_atomic_and_contains_no_knowledge(tmp_path):
    store = _Layout(tmp_path)
    assert store.read() == {"layout": None, "error": None}
    original = presentation()
    saved = store.save(original)
    assert saved == {"layout": original, "error": None}
    assert _Layout(tmp_path).read() == saved
    assert not list(tmp_path.glob(".presentation-*"))
    assert set(json.loads(store.path.read_bytes())) == {
        "format",
        "renderer",
        "workspace",
    }
    original["workspace"]["panels"]["reading"]["title"] = "changed"
    assert saved["layout"] != original


@pytest.mark.parametrize(
    "case",
    [
        "version",
        "renderer",
        "panel",
        "params",
        "duplicate",
        "foreign",
        "active",
        "dimensions",
        "prototype",
        "deep",
        "popout",
    ],
)
def test_invalid_presentation_preserves_the_prior_file(tmp_path, case):
    store = _Layout(tmp_path)
    original = presentation()
    store.save(original)
    prior = store.path.read_bytes()
    bad = deepcopy(original)
    workspace = bad["workspace"]
    if case == "version":
        bad["format"] = "sabueso.presentation_layout@999"
    elif case == "renderer":
        bad["renderer"] = "unknown"
    elif case == "panel":
        workspace["panels"]["reading"]["contentComponent"] = "unregistered"
    elif case == "params":
        workspace["panels"]["reading"]["params"] = {
            "scientific_state": "not presentation"
        }
    elif case == "duplicate":
        workspace["grid"]["root"]["data"][0]["data"]["views"].append("reading")
    elif case == "foreign":
        workspace["grid"]["root"]["data"][0]["data"]["views"] = ["foreign"]
    elif case == "active":
        workspace["activeGroup"] = []
    elif case == "dimensions":
        workspace["grid"]["width"] = float("nan")
    elif case == "prototype":
        workspace["__proto__"] = {}
    elif case == "deep":
        node = workspace["grid"]["root"]
        for _ in range(18):
            node["data"] = [{"type": "branch", "data": []}]
            node = node["data"][0]
    elif case == "popout":
        workspace["popoutGroups"] = [{"url": "https://unasked.invalid"}]
    with pytest.raises(ArgumentError):
        store.save(bad)
    assert store.path.read_bytes() == prior


def test_unknown_original_is_reported_and_never_overwritten(tmp_path):
    store = _Layout(tmp_path)
    store.path.write_text('{"format":"future"}')
    prior = store.path.read_bytes()
    assert store.read()["layout"] is None and store.read()["error"]
    with pytest.raises(ArgumentError, match="Move it aside"):
        store.save(presentation())
    assert store.path.read_bytes() == prior


def test_floating_presentation_has_complete_unique_membership():
    value = presentation()
    workspace = value["workspace"]
    group = workspace["grid"]["root"]["data"].pop()["data"]
    workspace["floatingGroups"] = [
        {
            "data": group,
            "position": {"left": 10, "top": 20, "width": 700, "height": 550},
        }
    ]
    assert json.loads(_validate(value)) == value


def test_presentation_symlink_never_replaces_the_callers_target(tmp_path):
    original = tmp_path / "caller.json"
    original.write_text("caller-owned")
    store = _Layout(tmp_path)
    store.path.symlink_to(original)
    assert store.read()["error"]
    with pytest.raises(ArgumentError, match="Move it aside"):
        store.save(presentation())
    assert original.read_text() == "caller-owned" and store.path.is_symlink()


def test_layout_http_boundary_and_atomic_unknown_refusal(tmp_path):
    pytest.importorskip("aiohttp")

    async def run():
        from aiohttp import CookieJar
        from aiohttp.test_utils import TestClient, TestServer

        from sabueso.explorer._service import _Service

        service = _Service(tmp_path)
        async with TestClient(
            TestServer(service.application()), cookie_jar=CookieJar(unsafe=True)
        ) as client:
            service.origin = str(client.make_url("/")).rstrip("/")
            assert (
                await client.post(
                    "/api/layout",
                    json=presentation(),
                    headers={"Origin": service.origin},
                )
            ).status == 403
            await client.post(
                "/auth",
                json={"token": service.token},
                headers={"Origin": service.origin},
            )
            assert (
                await client.post(
                    "/api/layout",
                    json=presentation(),
                    headers={"Origin": "https://foreign.invalid"},
                )
            ).status == 403
            response = await client.post(
                "/api/layout", json=presentation(), headers={"Origin": service.origin}
            )
            assert (
                response.status == 200
                and (await response.json())["layout"] == presentation()
            )
            prior = service.layout.path.read_bytes()
            for bad in ({"format": "future"}, [], {**presentation(), "renderer": None}):
                response = await client.post(
                    "/api/layout", json=bad, headers={"Origin": service.origin}
                )
                assert (
                    response.status == 400 and service.layout.path.read_bytes() == prior
                )
            response = await client.post(
                "/api/layout", data=b"x" * 65537, headers={"Origin": service.origin}
            )
            assert response.status == 400 and service.layout.path.read_bytes() == prior

    asyncio.run(run())
