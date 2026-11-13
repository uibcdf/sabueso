"""Real loopback receiving and serialized session admission, without source calls."""

import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

from sabueso.core.card import Card
from sabueso.explorer._service import _Service


def test_loopback_auth_origin_card_admission_and_stale_requests(tmp_path):
    pytest.importorskip("aiohttp")

    async def run():
        from aiohttp import CookieJar
        from aiohttp.test_utils import TestClient, TestServer

        service = _Service(tmp_path)
        async with TestClient(
            TestServer(service.application()), cookie_jar=CookieJar(unsafe=True)
        ) as client:
            service.origin = str(client.make_url("/")).rstrip("/")
            assert (await client.get("/api/panel")).status == 403
            assert (
                await client.post(
                    "/auth",
                    json={"token": service.token},
                    headers={"Origin": "https://foreign.invalid"},
                )
            ).status == 403
            response = await client.post(
                "/auth",
                json={"token": service.token},
                headers={"Origin": service.origin},
            )
            assert response.status == 200
            cookie = response.cookies["sabueso_explorer"]
            assert cookie["httponly"] and cookie["samesite"] == "Strict"
            assert (await (await client.get("/api/panel")).json())["panel"] is None
            card = Card(meta={"entity_type": "protein"})
            card.unknown_stored["synthetic"] = {
                "text": "<script>window.injected=true</script>",
                "number": 1.0,
                "large": 9007199254740993,
            }
            response = await client.post(
                "/api/card",
                json=card.to_dict(),
                headers={"Origin": service.origin, "X-Sabueso-Revision": ""},
            )
            assert response.status == 200
            original = service.session.explorer.inspect().native_payload["synthetic"]
            assert type(original["number"]) is float
            assert original["large"] == 9007199254740993
            panel = (await response.json())["panel"]
            action = {
                "name": "topic",
                "topic": "content",
                "revision": panel["revision"],
            }
            results = await asyncio.gather(
                *[
                    client.post(
                        "/api/action", json=action, headers={"Origin": service.origin}
                    )
                    for _ in range(2)
                ]
            )
            assert sorted(r.status for r in results) == [200, 400]
            result = next(r for r in results if r.status == 200)
            current = (await result.json())["panel"]
            assert "script-src" in result.headers["Content-Security-Policy"]
            assert result.headers["Cache-Control"] == "no-store"
            for body in (
                [],
                {
                    "name": "open",
                    "revision": current["revision"],
                    "path": "/etc/passwd",
                },
                {"name": []},
            ):
                response = await client.post(
                    "/api/action", json=body, headers={"Origin": service.origin}
                )
                assert response.status == 400
            assert (
                await client.get("/api/panel", headers={"Host": "foreign.invalid"})
            ).status == 403
            assert (await client.get("/assets/private.json")).status == 404
            assert (await client.get("/")).status == 200
            assert (await client.get("/assets/app.js")).status == 200
            from sabueso.core.deck import Deck

            deck_path = tmp_path / "original-deck.jsonl"
            Deck(
                [card, card],
                meta={"extension": {"number": 1.0, "large": 9007199254740993}},
            ).to_jsonl(str(deck_path))
            response = await client.post(
                "/api/deck",
                data=deck_path.read_bytes(),
                headers={
                    "Origin": service.origin,
                    "X-Sabueso-Revision": current["revision"],
                    "Content-Type": "application/jsonl",
                },
            )
            assert response.status == 200
            deck_panel = (await response.json())["panel"]
            assert deck_panel["workspace"] == "deck" and deck_panel["count"] == 2
            assert deck_panel["items"][0]["ref"] != deck_panel["items"][1]["ref"]
            original_meta = service.session.current.inspect()
            assert type(original_meta["extension"]["number"]) is float
            assert original_meta["extension"]["large"] == 9007199254740993
            response = await client.post(
                "/api/deck",
                data=deck_path.read_bytes(),
                headers={
                    "Origin": service.origin,
                    "X-Sabueso-Revision": current["revision"],
                },
            )
            assert response.status == 400

    asyncio.run(run())


def test_optional_explorer_import_outside_checkout_does_not_import_gui(tmp_path):
    code = "import sys,sabueso.explorer; assert not any(x.split('.')[0] in {'PySide6','aiohttp','molsysviewer','molsysmt'} for x in sys.modules)"
    subprocess.run(
        [sys.executable, "-I", "-c", code], cwd=tmp_path, check=True, timeout=20
    )


def test_frontend_assets_declared_and_contain_no_comparison_runtime():
    import json

    root = Path(__file__).resolve().parents[2]
    package = json.loads((root / "frontend/explorer/package.json").read_text())
    lock = json.loads((root / "frontend/explorer/package-lock.json").read_text())
    assert "electron" not in package["devDependencies"]
    assert not any("node_modules/electron" in key for key in lock["packages"])
    for name in ("index.html", "app.js", "app.css"):
        assert (root / "sabueso/explorer/_assets" / name).stat().st_size > 100
