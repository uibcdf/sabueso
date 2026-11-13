"""Optional loopback service; one serialized worker owns the captured session."""

from __future__ import annotations

import argparse
import asyncio
import hmac
import json
import os
import secrets
import signal
import tempfile
from concurrent.futures import ThreadPoolExecutor
from copy import copy
from pathlib import Path
from urllib.parse import urlsplit

from depdigest import dep_digest

from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, SabuesoError
from sabueso.explorer._deck_session import _DeckSession
from sabueso.explorer._resolution import _resolve
from sabueso.explorer._session import _Session

ASSETS = Path(__file__).parent / "_assets"
COOKIE = "sabueso_explorer"


@dep_digest("aiohttp")
def _web():
    from aiohttp import web

    return web


class _Service:
    def __init__(self, output_directory, session=None, resolver=None):
        self.web = _web()
        self.session = session
        self.output_directory = output_directory
        self.origin = None
        self.token = secrets.token_urlsafe(32)
        self.lock = asyncio.Lock()
        self.resolution = None
        self.resolver = resolver
        self.resolution_history = []

    def response(self, panel):
        return {
            "panel": panel,
            "resolution": self.resolution.panel() if self.resolution else None,
            "can_return_query": bool(self.resolution_history),
        }

    def resolve(self, body, *, choice=False):
        fields = {
            "revision",
            "resolution_revision",
            *(("choice_ref",) if choice else ("kind", "query")),
        }
        if not isinstance(body, dict) or set(body) != fields:
            raise ArgumentError("The source query has missing or unexpected arguments.")
        revision = self.session.revision if self.session else ""
        previous = self.resolution.revision if self.resolution else ""
        if body["revision"] != revision or body["resolution_revision"] != previous:
            raise ArgumentError(
                "The workspace changed; reload before querying a source."
            )
        if len(self.resolution_history) >= 32:
            raise ArgumentError(
                "Query history is full; return before querying another source."
            )
        if choice:
            ref = body["choice_ref"]
            if (
                not isinstance(ref, str)
                or not self.resolution
                or ref not in self.resolution.choices
            ):
                raise ArgumentError("Choose a source-declared entity from this result.")
            item = self.resolution.choices[ref]
            kind, query = item["kind"], item["query"]
        else:
            kind, query = body["kind"], body["query"]
        result = _resolve(kind, query, self.resolver)
        # Prepare before committing either context: an invalid answer must not
        # replace a valid captured reading or its original resolution.
        session = (
            _Session.from_card(result.card, self.output_directory)
            if result.card is not None
            else None
        )
        result.panel()
        if session is not None:
            session.panel()
        if self.session is not None or self.resolution is not None:
            self.resolution_history.append(
                (self.session.fork() if self.session else None, self.resolution)
            )
        if session is not None:
            self.session = session
        self.resolution = result
        return self.response(self.panel())

    def return_query(self, body):
        if not isinstance(body, dict) or set(body) != {
            "revision",
            "resolution_revision",
        }:
            raise ArgumentError("Invalid query return request.")
        revision = self.session.revision if self.session else ""
        previous = self.resolution.revision if self.resolution else ""
        if body["revision"] != revision or body["resolution_revision"] != previous:
            raise ArgumentError("The workspace changed; reload before returning.")
        if not self.resolution_history:
            raise ArgumentError("There is no previous query context.")
        self.session, original = self.resolution_history.pop()
        self.resolution = copy(original) if original else None
        if self.session:
            self.session.revision = secrets.token_hex(16)
        if self.resolution:
            self.resolution.revision = secrets.token_hex(16)
        return self.response(self.panel())

    def panel(self):
        return self.session.panel() if self.session else None

    def load_card(self, data):
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("meta"), dict)
            or not isinstance(data.get("sections"), dict)
        ):
            raise ArgumentError("Choose a serialized Sabueso Card JSON file.")
        session = _Session.from_card(Card.from_dict(data), self.output_directory)
        panel = session.panel()
        self.session = session
        self.resolution = None
        self.resolution_history = []
        return panel

    def load_deck(self, raw):
        from sabueso.core.deck import Deck

        with tempfile.TemporaryDirectory(prefix="sabueso-deck-input-") as directory:
            path = Path(directory) / "input.jsonl"
            path.write_bytes(raw)
            session = _DeckSession(Deck.from_jsonl(str(path)), self.output_directory)
        panel = session.panel()
        self.session = session
        self.resolution = None
        self.resolution_history = []
        return panel

    def application(self):
        web = self.web

        @web.middleware
        async def boundary(request, handler):
            if self.origin is None or request.host != urlsplit(self.origin).netloc:
                raise web.HTTPForbidden(text="Different application host")
            if (
                request.method == "POST"
                and request.headers.get("Origin") != self.origin
            ):
                raise web.HTTPForbidden(text="Different application origin")
            if request.path.startswith("/api/"):
                token = request.cookies.get(COOKIE, "")
                if not hmac.compare_digest(token, self.token):
                    raise web.HTTPForbidden(text="Open the application session first")
            try:
                response = await handler(request)
            except (ArgumentError, SabuesoError) as error:
                response = web.json_response({"error": str(error)}, status=400)
            except (json.JSONDecodeError, UnicodeDecodeError):
                response = web.json_response(
                    {"error": "Invalid JSON input"}, status=400
                )
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "connect-src 'self'; img-src 'self' data:; font-src 'self'; "
                "frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
            )
            return response

        app = web.Application(middlewares=[boundary], client_max_size=16 * 1024**2)

        async def asset(request):
            name = request.match_info.get("name", "index.html")
            if name not in {"index.html", "app.js", "app.css", "notices.txt"}:
                raise web.HTTPNotFound()
            return web.FileResponse(ASSETS / name)

        async def auth(request):
            body = await request.json()
            value = body.get("token") if isinstance(body, dict) else None
            if not isinstance(value, str) or not hmac.compare_digest(value, self.token):
                raise web.HTTPForbidden(text="Invalid session capability")
            response = web.json_response({"authenticated": True})
            response.set_cookie(COOKIE, self.token, httponly=True, samesite="Strict")
            return response

        async def panel(request):
            async with self.lock:
                result = await asyncio.to_thread(self.panel)
            return web.json_response(self.response(result))

        async def action(request):
            body = await request.json()
            async with self.lock:
                if self.session is None:
                    raise ArgumentError("Open a Card before exploring it.")
                result = await asyncio.to_thread(self.session.dispatch, body)
            return web.json_response(self.response(result))

        async def load(request):
            body = await request.json()
            async with self.lock:
                revision = self.session.revision if self.session else ""
                resolution = self.resolution.revision if self.resolution else ""
                if (
                    request.headers.get("X-Sabueso-Revision") != revision
                    or request.headers.get("X-Sabueso-Resolution", "") != resolution
                ):
                    raise ArgumentError(
                        "The reading changed; reload before opening a Card."
                    )
                result = await asyncio.to_thread(self.load_card, body)
            return web.json_response(self.response(result))

        async def load_deck(request):
            raw = await request.read()
            async with self.lock:
                revision = self.session.revision if self.session else ""
                resolution = self.resolution.revision if self.resolution else ""
                if (
                    request.headers.get("X-Sabueso-Revision") != revision
                    or request.headers.get("X-Sabueso-Resolution", "") != resolution
                ):
                    raise ArgumentError(
                        "The reading changed; reload before opening a Deck."
                    )
                result = await asyncio.to_thread(self.load_deck, raw)
            return web.json_response(self.response(result))

        async def resolve(request):
            body = await request.json()
            async with self.lock:
                if request.path.endswith("-back"):
                    result = await asyncio.to_thread(self.return_query, body)
                else:
                    result = await asyncio.to_thread(
                        self.resolve, body, choice=request.path.endswith("-choice")
                    )
            return web.json_response(result)

        app.add_routes(
            [
                web.get("/", asset),
                web.get("/assets/{name}", asset),
                web.post("/auth", auth),
                web.get("/api/panel", panel),
                web.post("/api/action", action),
                web.post("/api/card", load),
                web.post("/api/deck", load_deck),
                web.post("/api/resolve", resolve),
                web.post("/api/resolve-choice", resolve),
                web.post("/api/resolve-back", resolve),
            ]
        )
        return app


async def _run(args, resolver=None):
    stop = asyncio.Event()
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sabueso-reading")
    loop = asyncio.get_running_loop()
    loop.set_default_executor(executor)
    service = _Service(args.output_directory, resolver=resolver)
    runner = None
    try:
        if args.card:
            if args.card.stat().st_size > 16 * 1024**2:
                raise ArgumentError("This Card exceeds the 16 MiB opening limit.")
            data = await asyncio.to_thread(
                lambda: json.loads(args.card.read_text(encoding="utf-8"))
            )
            await asyncio.to_thread(service.load_card, data)
        elif args.reading:
            service.session = await asyncio.to_thread(
                _Session.from_saved, args.reading, args.output_directory
            )
        elif args.deck:
            if args.deck.stat().st_size > 16 * 1024**2:
                raise ArgumentError("This Deck exceeds the 16 MiB opening limit.")
            await asyncio.to_thread(service.load_deck, args.deck.read_bytes())
        runner = service.web.AppRunner(service.application(), access_log=None)
        await runner.setup()
        site = service.web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        service.origin = f"http://127.0.0.1:{port}"
        descriptor = os.open(
            args.bootstrap, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump({"url": f"{service.origin}/#token={service.token}"}, output)
        for signum in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(signum, stop.set)
        await stop.wait()
    finally:
        if runner:
            await runner.cleanup()
        args.bootstrap.unlink(missing_ok=True)
        executor.shutdown(wait=True)


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--card", type=Path)
    inputs.add_argument("--reading", type=Path)
    inputs.add_argument("--deck", type=Path)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--bootstrap", type=Path, required=True)
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    _main()
