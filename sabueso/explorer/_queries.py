"""One explicit background source query; adoption remains serialized and exact.

Cancellation discards the pending result. It cannot promise to interrupt an HTTP
request already executing inside a provider. A single daemon worker belongs to
the backend process; no queue of source work or additional process is created.
"""

from __future__ import annotations

import asyncio
import secrets
import threading

from sabueso.core.errors import ArgumentError


class _Queries:
    def __init__(self, service):
        self.service = service
        self.job = None
        self.closed = threading.Event()

    def descriptor(self):
        job = self.job
        if job is None:
            return None
        return {
            key: job[key] for key in ("ref", "kind", "query", "state", "phase", "error")
        } | {
            "worker_running": job["thread"].is_alive(),
            "protein_source": job["protein_source"],
            "original_revision": job["revisions"][0],
            "original_resolution_revision": job["revisions"][1],
            "cancellation_scope": "Discard the result; an active provider request may finish",
        }

    def start(self, body, *, choice=False):
        if self.closed.is_set():
            raise ArgumentError("The source-query service is closing.")
        if self.job and self.job["thread"].is_alive():
            raise ArgumentError(
                "One source query is still running; wait for it before starting another."
            )
        kind, query = self.service._query_request(body, choice=choice)
        options = self.service._source_options(body)
        loop = asyncio.get_running_loop()
        job = {
            "ref": secrets.token_hex(16),
            "kind": kind,
            "query": query,
            "protein_source": body.get("protein_source", "identity"),
            "state": "running",
            "phase": "querying_sources",
            "error": None,
            "prepared": None,
            "exception": None,
            "revisions": (body["revision"], body["resolution_revision"]),
        }

        def worker():
            try:
                prepared = self.service._prepare_resolution(kind, query, **options)
            except Exception as error:
                if not self.closed.is_set():
                    loop.call_soon_threadsafe(self._finished, job, None, error)
            else:
                if not self.closed.is_set():
                    loop.call_soon_threadsafe(self._finished, job, prepared, None)

        job["thread"] = threading.Thread(
            target=worker, name="sabueso-source-query", daemon=True
        )
        self.job = job
        job["thread"].start()
        return self.descriptor()

    def _finished(self, job, prepared, error):
        if self.closed.is_set() or job is not self.job or job["state"] == "cancelled":
            return
        job["prepared"], job["exception"] = prepared, error
        job["state"] = "failed" if error else "ready"
        job["phase"] = "failed" if error else "ready_to_open"
        job["error"] = (
            "The source query failed. Your previous reading remains available."
            if error
            else None
        )

    def _current(self, body, fields):
        if not isinstance(body, dict) or set(body) != {"job_ref", *fields}:
            raise ArgumentError("Malformed source-query action.")
        if (
            not self.job
            or not isinstance(body["job_ref"], str)
            or body["job_ref"] != self.job["ref"]
        ):
            raise ArgumentError("That source query does not belong to this workspace.")
        return self.job

    def cancel(self, body):
        job = self._current(body, set())
        if job["state"] not in ("running", "ready"):
            raise ArgumentError("Only a pending source result can be cancelled.")
        job.update(state="cancelled", phase="result_discarded", prepared=None)
        return self.descriptor()

    def open(self, body):
        job = self._current(body, {"revision", "resolution_revision"})
        if job["state"] != "ready" or job["prepared"] is None:
            raise ArgumentError("This source query has no ready result to open.")
        revision = self.service.session.revision if self.service.session else ""
        previous = self.service.resolution.revision if self.service.resolution else ""
        if body["revision"] != revision or body["resolution_revision"] != previous:
            raise ArgumentError(
                "The workspace changed. Open the ready source result explicitly from the current reading."
            )
        if len(self.service.resolution_history) >= 32:
            raise ArgumentError(
                "Query history is full; return before opening another source result."
            )
        result = self.service._adopt_resolution(*job["prepared"])
        job.update(state="opened", phase="opened", prepared=None)
        return {**result, "query_job": self.descriptor()}

    async def close(self):
        self.closed.set()
        job = self.job
        if job is not None:
            job.update(state="cancelled", phase="service_closed", prepared=None)
            # The backend owns the daemon's final lifetime; an already active
            # native HTTP request is not claimed to have been interrupted.
            await asyncio.to_thread(job["thread"].join, 2.0)
