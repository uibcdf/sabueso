"""Serve a tiny graphics diagnostic on owned loopback; no molecular data or API."""

import argparse
import asyncio
import json
import os
import signal
from pathlib import Path

from aiohttp import web

HERE = Path(__file__).resolve().parent


async def run(args):
    stop = asyncio.Event()
    app = web.Application()

    async def index(unused_request):
        return web.Response(
            text="<!doctype html><title>Graphics diagnostic</title>"
            "<h1>Graphics capability probe</h1>"
            "<p>A small diagnostic triangle; no molecular model is loaded.</p>"
            '<canvas width="256" height="256"></canvas>'
            '<script type="module" src="/graphics_page.mjs"></script>',
            content_type="text/html",
        )

    async def script(unused_request):
        return web.FileResponse(HERE / "graphics_page.mjs")

    app.add_routes([web.get("/", index), web.get("/graphics_page.mjs", script)])
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    try:
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        descriptor = os.open(
            args.bootstrap, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        with os.fdopen(descriptor, "w") as output:
            json.dump(
                {"url": f"http://127.0.0.1:{port}/", "backend_pid": os.getpid()}, output
            )
        loop = asyncio.get_running_loop()
        for signum in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(signum, stop.set)
        await stop.wait()
    finally:
        args.bootstrap.unlink(missing_ok=True)
        await runner.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", type=Path, required=True)
    asyncio.run(run(parser.parse_args()))
