"""Optional loopback service; one serialized worker owns the captured session."""

from __future__ import annotations

import argparse
import asyncio
import hmac
import io
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
from sabueso.core.errors import ArgumentError, SabuesoError, StorageError
from sabueso.explorer._deck_session import _DeckSession
from sabueso.explorer._layout import LIMIT as LAYOUT_LIMIT
from sabueso.explorer._layout import _Layout
from sabueso.explorer._queries import _Queries
from sabueso.explorer._resolution import _resolve
from sabueso.explorer._session import _Session

ASSETS = Path(__file__).parent / "_assets"
COOKIE = "sabueso_explorer"


def _publish_bootstrap(path, configuration):
    """Expose only a complete, private descriptor without replacing a caller file."""
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=".sabueso-bootstrap-"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(configuration, output)
            output.flush()
            os.fsync(output.fileno())
            owned = os.fstat(output.fileno())
        os.link(temporary, path)
        return owned.st_dev, owned.st_ino
    finally:
        Path(temporary).unlink(missing_ok=True)


def _remove_bootstrap(path, owned):
    if owned is None:
        return
    try:
        current = path.lstat()
    except FileNotFoundError:
        return
    if (current.st_dev, current.st_ino) == owned:
        path.unlink()


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
        self.molecular = None
        self.molecular_lock = asyncio.Lock()
        self.layout = _Layout(output_directory)
        self.queries = _Queries(self)
        self.workspace_saved = None

    def response(self, panel):
        from ._resolution import source_access_preview
        from ._source_choices import choice_details

        resolution = self.resolution.panel() if self.resolution else None
        if resolution is not None:
            # Presentation-only descriptions never enter the original query wire.
            resolution["choice_details"] = choice_details(self.resolution)
            resolution["source_access"] = source_access_preview(self.resolution)
        return {
            "panel": panel,
            "resolution": resolution,
            "can_return_query": bool(self.resolution_history),
            "molecular": self.molecular.descriptor() if self.molecular else None,
            "presentation": self.layout.read(),
            "query_job": self.queries.descriptor(),
            "workspace_saved_file": self.workspace_saved[0].name
            if self.workspace_saved
            else None,
        }

    def _query_request(self, body, *, choice=False, link=False):
        fields = {
            "revision",
            "resolution_revision",
            *(
                ("item_ref",)
                if link
                else ("choice_ref",)
                if choice
                else ("kind", "query")
            ),
        }
        if not isinstance(body, dict) or set(body) not in (
            fields,
            fields | ({"protein_source"} if not choice and not link else set()),
        ):
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
        if link:
            from ._record_queries import current_item_query

            item = current_item_query(self.session, body["item_ref"])
            kind, query = item["kind"], item["query"]
        elif choice:
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
        from ._resolution import _protein_options, _query

        _protein_options(kind, body.get("protein_source", "identity"))
        _query(kind, query)  # Grammar before launching work; no source access.
        return kind, query

    @staticmethod
    def _source_options(body):
        source = body.get("protein_source", "identity")
        return {"protein_source": source} if source != "identity" else {}

    def _prepare_resolution(self, kind, query, *, protein_source="identity"):
        result = _resolve(kind, query, self.resolver, protein_source=protein_source)
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
        return result, session

    def _adopt_resolution(self, result, session):
        if self.session is not None or self.resolution is not None:
            self.resolution_history.append(
                (self.session.fork() if self.session else None, self.resolution)
            )
        if session is not None:
            self.session = session
        self.resolution = result
        return self.response(self.panel())

    def resolve(self, body, *, choice=False):
        if self.queries.job and self.queries.job["thread"].is_alive():
            raise ArgumentError("A source query is already running.")
        kind, query = self._query_request(body, choice=choice)
        return self._adopt_resolution(
            *self._prepare_resolution(kind, query, **self._source_options(body))
        )

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

    def load_reading(self, raw):
        from sabueso.core import exploration_transport as transport
        from sabueso.core.card_exploration_storage import _unique
        from sabueso.core.deck_exploration_storage import FORMAT as DECK_FORMAT

        from ._workspace import FORMAT as WORKSPACE_FORMAT
        from ._workspace import read_workspace

        decoded, _ = transport.read(
            io.BytesIO(raw),
            encoded_limit=transport.BYTE_LIMIT,
            decoded_limit=transport.BYTE_LIMIT,
            window_limit=transport.WINDOW_LIMIT,
        )
        try:
            data = json.loads(decoded.decode("utf-8"), object_pairs_hook=_unique)
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise StorageError("Cannot read this original saved reading.") from exc
        deck_reading = isinstance(data, dict) and data.get("format") == DECK_FORMAT
        workspace = isinstance(data, dict) and data.get("format") == WORKSPACE_FORMAT
        del decoded, data
        with tempfile.TemporaryDirectory(prefix="sabueso-reading-input-") as directory:
            path = Path(directory) / "original.json"
            path.write_bytes(raw)
            if workspace:
                session, resolution, history = read_workspace(
                    path, self.output_directory
                )
            else:
                reader = _DeckSession if deck_reading else _Session
                session = reader.from_saved(path, self.output_directory)
                resolution, history = None, []
        panel = session.panel() if session else None
        self.session = session
        self.resolution, self.resolution_history = resolution, history
        self.workspace_saved = None
        return panel

    def workspace(self, body, *, reopen=False):
        if not isinstance(body, dict) or set(body) != {
            "revision",
            "resolution_revision",
        }:
            raise ArgumentError("Malformed workspace action.")
        current = self.session.revision if self.session else ""
        resolution = self.resolution.revision if self.resolution else ""
        if body["revision"] != current or body["resolution_revision"] != resolution:
            raise ArgumentError(
                "The workspace changed; reload before saving or reopening it."
            )
        if reopen:
            from ._workspace import read_workspace

            if self.workspace_saved is None:
                raise ArgumentError("Save this workspace before reopening it.")
            session, resolution, history = read_workspace(
                self.workspace_saved[0], self.output_directory, self.workspace_saved[1]
            )
            panel = session.panel() if session else None
            self.session, self.resolution, self.resolution_history = (
                session,
                resolution,
                history,
            )
        else:
            from ._workspace import save_workspace

            output = Path(self.output_directory)
            output.mkdir(parents=True, exist_ok=True)
            path = output / f"workspace-{secrets.token_hex(12)}.json.gz"
            receipt = save_workspace(self, path)
            self.workspace_saved = (path, receipt["bundle_digest"])
            panel = self.panel()
        return self.response(panel)

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
            if self.molecular and self.molecular.allowed_origin:
                response.headers["Content-Security-Policy"] += (
                    f"; frame-src {self.molecular.allowed_origin}"
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
                        "The reading changed; reload before opening this file."
                    )
                loader = (
                    self.load_reading
                    if request.path.endswith("/reading")
                    else self.load_deck
                )
                result = await asyncio.to_thread(loader, raw)
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

        async def molecular(request):
            return web.json_response(
                {"molecular": self.molecular.descriptor() if self.molecular else None}
            )

        async def molecular_action(request):
            body = await request.json()
            async with self.molecular_lock:
                model = self.molecular
                if (
                    model is None
                    or not isinstance(body, dict)
                    or set(body) != {"lifecycle_revision"}
                    or body["lifecycle_revision"] != model.revision
                ):
                    raise ArgumentError(
                        "The molecular panel changed; reload its controls."
                    )
                if request.path.endswith("-reopen"):
                    await model.reopen()
                else:
                    await model.close_preview()
                return web.json_response({"molecular": model.descriptor()})

        async def query_job(request):
            if request.method == "GET":
                return web.json_response({"query_job": self.queries.descriptor()})
            body = await request.json()
            async with self.lock:
                if request.path.endswith("-cancel"):
                    result = {"query_job": self.queries.cancel(body)}
                elif request.path.endswith("-open"):
                    result = await asyncio.to_thread(self.queries.open, body)
                else:
                    result = {
                        "query_job": self.queries.start(
                            body,
                            choice=request.path.endswith("-choice"),
                            link=request.path.endswith("-link"),
                        )
                    }
            return web.json_response(result)

        async def close_queries(application):
            await self.queries.close()

        app.on_cleanup.append(close_queries)

        async def workspace(request):
            body = await request.json()
            async with self.lock:
                result = await asyncio.to_thread(
                    self.workspace, body, reopen=request.path.endswith("-reopen")
                )
            return web.json_response(result)

        async def layout(request):
            raw = await request.read()
            if len(raw) > LAYOUT_LIMIT:
                raise ArgumentError("The presentation layout exceeds 64 KiB.")
            try:
                body = json.loads(raw)
            except RecursionError as error:
                raise ArgumentError(
                    "The presentation layout is too deeply nested."
                ) from error
            async with self.lock:
                result = await asyncio.to_thread(self.layout.save, body)
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
                web.post("/api/reading", load_deck),
                web.post("/api/resolve", resolve),
                web.post("/api/resolve-choice", resolve),
                web.post("/api/resolve-back", resolve),
                web.get("/api/query", query_job),
                web.post("/api/query-start", query_job),
                web.post("/api/query-choice", query_job),
                web.post("/api/query-link", query_job),
                web.post("/api/query-cancel", query_job),
                web.post("/api/query-open", query_job),
                web.post("/api/workspace-save", workspace),
                web.post("/api/workspace-reopen", workspace),
                web.get("/api/molecular", molecular),
                web.post("/api/molecular-close", molecular_action),
                web.post("/api/molecular-reopen", molecular_action),
                web.post("/api/layout", layout),
            ]
        )
        return app


async def _run(args, resolver=None):
    stop = asyncio.Event()
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sabueso-reading")
    loop = asyncio.get_running_loop()
    loop.set_default_executor(executor)
    service = _Service(args.output_directory, resolver=resolver)
    runner, bootstrap_owned = None, None
    try:
        if args.card:
            if args.card.stat().st_size > 16 * 1024**2:
                raise ArgumentError("This Card exceeds the 16 MiB opening limit.")
            data = await asyncio.to_thread(
                lambda: json.loads(args.card.read_text(encoding="utf-8"))
            )
            await asyncio.to_thread(service.load_card, data)
        elif args.reading:
            if args.reading.stat().st_size > 64 * 1024**2:
                raise ArgumentError("This reading exceeds the 64 MiB opening limit.")
            await asyncio.to_thread(service.load_reading, args.reading.read_bytes())
        elif args.deck:
            if args.deck.stat().st_size > 16 * 1024**2:
                raise ArgumentError("This Deck exceeds the 16 MiB opening limit.")
            await asyncio.to_thread(service.load_deck, args.deck.read_bytes())
        model = getattr(args, "experimental_model", None)
        if model:
            from sabueso.explorer._molecular import _Molecular

            service.molecular = _Molecular(model)
            try:
                await service.molecular.start()
            except Exception as error:
                service.molecular.error = str(error)
                try:
                    await service.molecular.close()
                except Exception as cleanup_error:
                    service.molecular.error += (
                        f"; molecular cleanup failed: {cleanup_error}"
                    )
        runner = service.web.AppRunner(service.application(), access_log=None)
        await runner.setup()
        site = service.web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        service.origin = f"http://127.0.0.1:{port}"
        bootstrap_owned = _publish_bootstrap(
            args.bootstrap,
            {
                "url": f"{service.origin}/#token={service.token}",
                "molecular_origin": service.molecular.origin
                if service.molecular
                else None,
            },
        )
        for signum in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(signum, stop.set)
        await stop.wait()
    finally:
        try:
            if runner:
                await runner.cleanup()
        finally:
            try:
                if service.molecular:
                    await service.molecular.close()
            finally:
                _remove_bootstrap(args.bootstrap, bootstrap_owned)
                executor.shutdown(wait=True)


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--card", type=Path)
    inputs.add_argument("--reading", type=Path)
    inputs.add_argument("--deck", type=Path)
    parser.add_argument("--experimental-model", type=Path)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--bootstrap", type=Path, required=True)
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    _main()
