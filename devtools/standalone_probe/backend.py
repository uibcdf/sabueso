"""Bounded development service using real Card readers and Viewer's preview host.

This is an experiment, not a public application API or a shared MolI contract.
The molecular iframe uses the provider's existing client-rendering service;
no molecular protocol, scene owner or geometry calculation is reimplemented.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import os
import secrets
import signal
import time
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import distribution, version
from pathlib import Path

from aiohttp import web
from scale_case import BufferObservation, run_scale_case

HERE = Path(__file__).resolve().parent


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_inputs(directory):
    manifest = load_json(directory / "inputs.json")
    for name, expected in manifest["files"].items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise ValueError("Input path escaped the prepared cohort")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Prepared input changed: {name}")
    return manifest


class KnowledgeSession:
    def __init__(self, directory, output):
        from sabueso.core.card import Card

        self.card = Card.from_json(str(directory / "source/card.json"))
        self.explorer = self.card.explore()
        self.current = self.explorer.overview()
        self.stack = []
        self.output = output
        self.saved = None
        self.save_count = 0
        self.reopen_validation = None
        self.before = self.card.to_dict()
        self.topics = list(self.explorer.topics().native_payload)

    def panel(self):
        native = self.current.native_payload
        return {
            "title": self.current.title,
            "text": str(self.current),
            "result_ref": self.current.result_ref,
            "view_ref": self.current.view_ref,
            "items": [
                {"ref": item.item_ref, "label": item.label}
                for item in self.current.items()
            ],
            "can_back": bool(self.stack),
            "mode": self.current.explorer.mode if self.current.explorer else "context",
            "reopen_validation": self.reopen_validation,
            "is_source_assertion": isinstance(native, dict)
            and "source" in native
            and "asserted_value" in native,
        }

    def action(self, action):
        name = action.get("name")
        if name == "topic":
            topic = action.get("topic")
            if topic not in self.topics:
                raise ValueError("Unknown captured topic")
            self.stack.append(self.current)
            self.current = self.explorer.view(topic)
        elif name in {"related", "open"}:
            item = self.current.item(action.get("item_ref"))
            destination = item.related() if name == "related" else item.open()
            self.stack.append(self.current)
            self.current = destination
        elif name == "back":
            if not self.stack:
                raise ValueError("No retained return context")
            self.current = self.stack.pop()
        elif name == "save":
            self.save_count += 1
            path = self.output / f"reading-{self.save_count}.json.gz"
            if path.exists():
                raise ValueError("A saved original must not be overwritten")
            receipt = self.current.save(path, compression="gzip")
            self.saved = (
                path,
                receipt,
                {
                    "panel": self.panel(),
                    "native": self.current.native_payload,
                    "request": self.current.request,
                    "rows": self.current.rows(),
                },
            )
        elif name == "reopen":
            import sabueso

            if self.saved is None:
                raise ValueError("No original reading was saved")
            path, receipt, original = self.saved
            reopened = sabueso.read_exploration(
                path, expected_digest=receipt["bundle_digest"]
            )
            self.reopen_validation = {
                "result_ref": reopened.result_ref == original["panel"]["result_ref"],
                "native_payload": reopened.native_payload == original["native"],
                "request": reopened.request == original["request"],
                "rows_with_support": reopened.rows() == original["rows"],
            }
            if not all(self.reopen_validation.values()):
                raise ValueError(
                    "Reopened reading differs from the original scientific result"
                )
            self.stack.append(self.current)
            self.current = reopened
        else:
            raise ValueError("Unknown knowledge action")
        if self.card.to_dict() != self.before:
            raise ValueError("Presentation changed the original Card")
        return self.panel()


class Probe:
    def __init__(self, inputs, output):
        self.inputs = inputs
        self.output = output
        self.manifest = verify_inputs(inputs)
        self.correspondence = load_json(inputs / "correspondence.json")
        self.knowledge = KnowledgeSession(inputs, output)
        self.panel = self.knowledge.panel()
        self.pick = None
        self.selection = []
        self.action_lock = asyncio.Lock()
        self.stop = asyncio.Event()
        self.token = secrets.token_urlsafe(32)
        self.cookie_name = "sabueso_standalone_probe"
        self.service = None
        self.view = None
        self.bound_load_records = None
        self.independent = None
        self.origin = None
        self.timings = {}
        self.buffers = None

    def authorized(self, request):
        token = request.cookies.get(self.cookie_name, "")
        return bool(token) and hmac.compare_digest(token, self.token)

    def check_origin(self, request):
        if request.headers.get("Origin") != self.origin:
            raise web.HTTPForbidden(text="Different request origin")

    async def auth(self, request):
        self.check_origin(request)
        value = await request.json()
        supplied = value.get("token")
        if not isinstance(supplied, str) or not hmac.compare_digest(
            supplied, self.token
        ):
            raise web.HTTPForbidden(text="Invalid probe capability")
        response = web.json_response({"authenticated": True})
        response.set_cookie(
            self.cookie_name, self.token, httponly=True, samesite="Strict"
        )
        return response

    async def config(self, request):
        if not self.authorized(request):
            raise web.HTTPForbidden()
        return web.json_response(
            {
                "viewer_url": self.service.client_url,
                "card_ref": self.manifest["card_ref"],
                "topics": self.knowledge.topics,
                "panel": self.panel,
                "timings": self.timings,
                "scope": "Public frozen TcTIM/1TCD; live experimental Viewer integration",
            }
        )

    async def state(self, request):
        if not self.authorized(request):
            raise web.HTTPForbidden()
        return web.json_response(
            {
                "pick": self.pick if self.binding_valid() else None,
                "binding_valid": self.binding_valid(),
                "active_selection": self.view.active_selection.atom_indices,
                "camera": self.view.camera.get_snapshot(),
                "viewer_ready": self.service.client_render_ready.is_set(),
                "structure_complete": self.service.client_structure_complete.is_set(),
                "client_registrations": self.service.client_registration_count,
                "viewer_failure": self.service.failure,
                "viewer_client_error": self.service.last_client_error,
                "independent_exists": self.independent is not None,
                "independent_ready": bool(
                    self.independent
                    and self.independent[0].client_structure_complete.is_set()
                ),
            }
        )

    async def action(self, request):
        if not self.authorized(request):
            raise web.HTTPForbidden()
        self.check_origin(request)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise web.HTTPBadRequest(text="A finite action is required")
        async with self.action_lock:
            try:
                name = payload.get("name")
                if name == "select_active_site":
                    if not self.binding_valid():
                        raise ValueError(
                            "The molecular input changed; explicit source rebinding is required"
                        )
                    feature = self.knowledge.card.sections["features_positional"][
                        "active_site"
                    ]["value"][0]
                    sequence = feature["location"]["sequence"]
                    if (
                        sequence["sequence_id"] != "UniProt:P52270"
                        or sequence["indexing"] != "1-based"
                    ):
                        raise ValueError(
                            "Active-site annotation has an incompatible source axis"
                        )
                    selected = [
                        row["atom_index"]
                        for row in self.correspondence["atoms"]
                        if row["source_asym_id"] == "A"
                        and row["uniprot_position"] is not None
                        and sequence["start"]
                        <= row["uniprot_position"]
                        <= sequence["end"]
                    ]
                    if not selected:
                        raise ValueError(
                            "The original annotation has no admitted atoms"
                        )
                    self.view.active_selection.set(selected)
                    self.view.camera.zoom(
                        selected, duration="0 ms", extra_radius="5 angstroms"
                    )
                    self.selection = selected
                elif name == "camera_reset":
                    self.view.camera.reset()
                elif name == "open_independent":
                    from molsysviewer.remote import RemoteSessionService
                    from molsysviewer.viewer import MolSysView

                    if self.independent is not None:
                        raise ValueError("The independent view is already open")
                    service = RemoteSessionService(render_on="client")
                    view = MolSysView(transport=service.channel)
                    try:
                        view.load(str(self.inputs / "1tcd.bcif.gz"))
                        await service.start()
                    except BaseException:
                        await service.close()
                        view.close()
                        raise
                    self.independent = (service, view)
                elif name == "close_independent":
                    if self.independent is None:
                        raise ValueError("No independent view is open")
                    service, view = self.independent
                    await service.close()
                    view.close()
                    self.independent = None
                elif name == "scale_control":
                    result = await run_scale_case(
                        self, payload.get("copies"), payload.get("structures")
                    )
                    return web.json_response({"scale": result})
                elif name == "replace_model_control":
                    if len(self.selection) < 3:
                        raise ValueError(
                            "The reindexing control needs the original annotated selection"
                        )
                    self.view.load(
                        str(self.inputs / "1tcd.bcif.gz"),
                        selection=self.selection[:3],
                        mode="replace",
                    )
                elif name == "shutdown":
                    self.stop.set()
                else:
                    self.panel = await asyncio.to_thread(self.knowledge.action, payload)
            except (ValueError, KeyError, TypeError) as error:
                return web.json_response({"error": str(error)}, status=422)
        return web.json_response(
            {
                "panel": self.panel,
                "selected_atom_indices": self.selection,
                "independent_url": self.independent[0].client_url
                if self.independent
                else None,
            }
        )

    def binding_valid(self):
        return (
            self.view is not None and self.bound_load_records == self.view.load_blocks
        )

    def on_click(self, event):
        if not self.binding_valid():
            self.pick = None
            return
        indices = event.get("atom_indices") or []
        if any(
            type(i) is not int or i < 0 or i >= len(self.correspondence["atoms"])
            for i in indices
        ):
            raise ValueError("A molecular pick escaped the admitted atom index space")
        self.pick = {
            "kind": event.get("kind"),
            "atom_indices": indices,
            "source_locations": [self.correspondence["atoms"][i] for i in indices],
            "card_ref": self.manifest["card_ref"],
            "source_assertion_id": self.correspondence["admission"][
                "source_assertion_id"
            ],
        }


async def run(args):
    started = time.monotonic()
    from molsysviewer.remote import RemoteSessionService
    from molsysviewer.viewer import MolSysView

    args.output.mkdir(parents=True, exist_ok=False)
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(
        max_workers=1, thread_name_prefix="sabueso-probe-knowledge"
    )
    loop.set_default_executor(executor)
    probe = Probe(args.inputs, args.output)
    probe.service = RemoteSessionService(render_on="client")
    probe.buffers = BufferObservation(probe.service.channel)
    probe.view = MolSysView(transport=probe.service.channel)
    runner = None
    try:
        probe.view.load(str(args.inputs / "1tcd.bcif.gz"))
        probe.bound_load_records = probe.view.load_blocks
        probe.view.on_click(probe.on_click)
        await probe.service.start()
        app = web.Application(client_max_size=16 * 1024)

        async def index(request):
            return web.FileResponse(HERE / "index.html")

        app.add_routes(
            [
                web.get("/", index),
                web.post("/auth", probe.auth),
                web.get("/api/config", probe.config),
                web.get("/api/state", probe.state),
                web.post("/api/action", probe.action),
                web.static("/dist", HERE / "dist"),
            ]
        )
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        probe.origin = f"http://127.0.0.1:{port}"
        probe.timings["backend_ready_s"] = time.monotonic() - started
        bootstrap = {
            "url": f"{probe.origin}/#token={probe.token}",
            "backend_pid": os.getpid(),
            "timings": probe.timings,
        }
        fd = os.open(args.bootstrap, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(bootstrap, output)
        versions = {
            name: version(name)
            for name in ("sabueso", "molsysviewer", "molsysmt", "PySide6", "aiohttp")
        }
        placements = {}
        for name in ("sabueso", "molsysviewer", "molsysmt"):
            direct = distribution(name).read_text("direct_url.json")
            placements[name] = json.loads(direct) if direct else None
        import molsysviewer

        viewer_asset = Path(molsysviewer.__file__).resolve().parent / "viewer.js"
        with viewer_asset.open("rb") as asset:
            opaque_runtime_digest = hashlib.file_digest(asset, "sha256").hexdigest()
        (args.output / "cohort.json").write_text(
            json.dumps(
                {
                    "versions": versions,
                    "placements": placements,
                    "opaque_viewer_asset_sha256": opaque_runtime_digest,
                    "inputs": probe.manifest,
                    "timings": probe.timings,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        for signum in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(signum, probe.stop.set)
        print("Probe backend ready; private bootstrap written", flush=True)
        await probe.stop.wait()
    finally:
        if probe.independent is not None:
            service, view = probe.independent
            await service.close()
            view.close()
        probe.view.off_click(probe.on_click)
        await probe.service.close()
        probe.view.close()
        probe.buffers.close()
        if runner:
            await runner.cleanup()
        args.bootstrap.unlink(missing_ok=True)
        executor.shutdown(wait=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
