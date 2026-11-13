"""Original saved bytes receive through the same verifier as Python reading."""

import asyncio

import pytest

from sabueso.core.card import Card
from sabueso.core.errors import StorageError
from sabueso.explorer._service import _Service


@pytest.mark.parametrize("compression", ["none", "gzip", "zstd"])
def test_original_upload_is_inert_and_keeps_exact_literal_types(
    tmp_path, monkeypatch, compression
):
    pytest.importorskip("aiohttp")
    card = Card(meta={"entity_type": "small_molecule"})
    original = {
        "float": 1.0,
        "large": 9007199254740993,
        "quantity": {"value": 0.5, "unit": "nanometer"},
        "unknown": None,
        "flag": False,
    }
    card.unknown_stored["synthetic"] = original
    explorer = card.explore()
    view = next(
        item for item in explorer.view("content").items() if item.label == "synthetic"
    ).open()
    path = tmp_path / "original"
    view.save(path, compression=compression)
    raw = path.read_bytes()

    def forbidden(*unused, **also_unused):
        raise AssertionError("Opening an original must not construct or acquire a Card")

    monkeypatch.setattr(Card, "from_dict", forbidden)
    service = _Service(tmp_path)
    panel = service.load_reading(raw)
    assert panel["mode"] == "saved" and panel["result_ref"] == view.result_ref
    assert service.session.current.native_payload == original
    assert type(service.session.current.native_payload["float"]) is float
    assert path.read_bytes() == raw
    before = service.session
    with pytest.raises(StorageError):
        service.load_reading(b"not an original saved reading")
    assert service.session is before


def test_actual_file_body_upload_and_stale_refusal(tmp_path):
    pytest.importorskip("aiohttp")
    view = Card().explore().overview()
    path = tmp_path / "original.json.gz"
    view.save(path, compression="gzip")

    async def run():
        from aiohttp import CookieJar
        from aiohttp.test_utils import TestClient, TestServer

        service = _Service(tmp_path)
        async with TestClient(
            TestServer(service.application()), cookie_jar=CookieJar(unsafe=True)
        ) as client:
            service.origin = str(client.make_url("/")).rstrip("/")
            headers = {"Origin": service.origin, "X-Sabueso-Revision": ""}
            await client.post("/auth", json={"token": service.token}, headers=headers)
            response = await client.post(
                "/api/reading", data=path.read_bytes(), headers=headers
            )
            assert response.status == 200
            panel = (await response.json())["panel"]
            assert panel["mode"] == "saved" and panel["result_ref"] == view.result_ref
            response = await client.post(
                "/api/reading", data=path.read_bytes(), headers=headers
            )
            assert response.status == 400

    asyncio.run(run())
