"""Bounded development binding to Viewer's experimental public client service.

This does not establish Card/model identity or copy a provider protocol. #368
owns the supported embedding contract; the reviewed source cohort owns this
explicitly experimental receiving scope. Input-byte limits are not a model RAM
guarantee; large/model-residency qualification remains separate under Viewer #55.
"""

from __future__ import annotations

import gzip
import hashlib
import secrets
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from depdigest import dep_digest

from sabueso.core.errors import ArgumentError, SabuesoError

ENCODED_LIMIT = 16 * 1024**2
DECODED_LIMIT = 64 * 1024**2


class _Molecular:
    def __init__(self, source):
        self.source = Path(source)
        self.directory = None
        self.service = self.view = None
        self.input_digest = None
        self.error = None
        self.closed = False
        self.finalized = False
        self.target = None
        self.allowed_origin = None
        self.operation = None
        self.revision = secrets.token_hex(16)

    def _capture(self):
        suffixes = self.source.suffixes
        compressed = bool(suffixes and suffixes[-1].lower() == ".gz")
        form = (
            suffixes[-2].lower()
            if compressed and len(suffixes) > 1
            else self.source.suffix.lower()
        )
        if form not in {".pdb", ".ent", ".cif", ".mmcif", ".bcif"}:
            raise ArgumentError(
                "The experimental model accepts PDB, mmCIF or BinaryCIF, optionally gzip-compressed."
            )
        self.directory = tempfile.TemporaryDirectory(prefix="sabueso-model-")
        target = Path(self.directory.name) / (
            "input" + form + (".gz" if compressed else "")
        )
        target.touch(mode=0o600)
        hasher, size = hashlib.sha256(), 0
        with self.source.open("rb") as origin, target.open("wb") as snapshot:
            for block in iter(lambda: origin.read(65536), b""):
                size += len(block)
                if size > ENCODED_LIMIT:
                    raise ArgumentError(
                        "This experimental model exceeds the 16 MiB input limit."
                    )
                hasher.update(block)
                snapshot.write(block)
        if not size:
            raise ArgumentError("The molecular input file is empty.")
        if compressed:
            decoded = 0
            with gzip.open(target, "rb") as stream:
                for block in iter(lambda: stream.read(65536), b""):
                    decoded += len(block)
                    if decoded > DECODED_LIMIT:
                        raise ArgumentError(
                            "This experimental model exceeds the 64 MiB decoded limit."
                        )
            if not decoded:
                raise ArgumentError(
                    "The molecular input file is empty after decompression."
                )
        self.input_digest = "sha256:" + hasher.hexdigest()
        self.target = target
        return target

    @dep_digest("molsysviewer")
    async def start(self):
        try:
            from molsysviewer.remote import RemoteSessionService
            from molsysviewer.viewer import MolSysView
        except ImportError as error:
            raise SabuesoError(
                "This MolSysViewer installation does not provide the received experimental embedding surface."
            ) from error
        if self.finalized or self.service is not None or self.view is not None:
            raise ArgumentError(
                "The molecular runtime cannot be started in this state."
            )
        target = self.target if self.target is not None else self._capture()
        if (
            "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
            != self.input_digest
        ):
            raise ArgumentError("The captured initial molecular input changed.")
        # Reuse only the already admitted origin; the native host/CSP never
        # broadens its loopback allowlist to accommodate a new runtime.
        port = urlsplit(self.allowed_origin).port if self.allowed_origin else 0
        self.service = RemoteSessionService(render_on="client", listen_port=port)
        self.view = MolSysView(transport=self.service.channel)
        # Initial startup precedes serving; explicit reopening starts a fresh view.
        # The provider owns
        # parsing, geometry, binary transport, runtime state and rendering.
        self.view.load(str(target))
        await self.service.start()
        origin = urlsplit(self.service.origin)
        if (
            origin.scheme != "http"
            or origin.hostname != "127.0.0.1"
            or not origin.port
            or origin.username
            or origin.password
            or origin.path
            or origin.query
            or origin.fragment
        ):
            raise SabuesoError(
                "The molecular service did not expose its owned loopback origin."
            )
        client = urlsplit(self.service.client_url)
        if client.scheme != "http" or client.netloc != origin.netloc:
            raise SabuesoError(
                "The molecular client does not belong to its owned service."
            )
        if (
            self.allowed_origin is not None
            and self.service.origin != self.allowed_origin
        ):
            raise SabuesoError("The molecular runtime changed its admitted origin.")
        self.allowed_origin = self.service.origin
        self.closed = False
        self.error = None

    @property
    def origin(self):
        return (
            self.service.origin
            if self.service and self.error is None and not self.closed
            else None
        )

    def descriptor(self):
        def observed(name):
            event = getattr(self.service, name, None)
            return event.is_set() if callable(getattr(event, "is_set", None)) else None

        return {
            "format": "sabueso.experimental_molecular_panel@1",
            "status": self.operation
            if self.operation
            else "unavailable"
            if self.error
            else "closed"
            if self.closed
            else "experimental",
            "error": self.error,
            "lifecycle_revision": self.revision,
            "can_close": not self.finalized and bool(self.service or self.view),
            "can_reopen": self.can_reopen,
            "initial_file_name": self.source.name,
            "initial_input_digest": self.input_digest,
            "correspondence": "not_established",
            "client_url": self.service.client_url
            if not self.operation and self.origin
            else None,
            "initial_renderer_ready": observed("client_render_ready"),
            "initial_structure_received": observed("client_structure_complete"),
            "client_registrations": getattr(
                self.service, "client_registration_count", None
            ),
            "camera_snapshot": self.view.camera.get_snapshot()
            if self.view and not self.error and not self.operation
            else None,
            "active_selection_indices": self.view.active_selection.atom_indices
            if self.view and not self.error and not self.operation
            else [],
        }

    @property
    def can_reopen(self):
        return bool(
            self.closed
            and not self.finalized
            and self.target is not None
            and self.allowed_origin
            and self.service is None
            and self.view is None
            and not self.operation
        )

    async def _dispose_runtime(self):
        try:
            if self.service:
                await self.service.close()
                self.service = None
        finally:
            if self.view:
                self.view.close()
                self.view = None

    async def close_preview(self):
        """Release only this runtime; retain its initial input for explicit reopen."""
        if self.finalized:
            raise ArgumentError("The molecular panel has been finalized.")
        self.revision = secrets.token_hex(16)
        self.operation, self.closed = "closing", True
        try:
            await self._dispose_runtime()
            self.error = None
        except Exception as error:
            self.error = f"Molecular runtime cleanup failed: {error}"
        finally:
            self.operation = None

    async def reopen(self):
        """Create a fresh runtime from the initial copy, without scene recovery."""
        if not self.can_reopen:
            raise ArgumentError("Close the molecular runtime before reopening it.")
        self.revision = secrets.token_hex(16)
        self.operation, self.error = "opening", None
        try:
            await self.start()
        except Exception as error:
            self.closed = True
            self.error = f"Molecular preview unavailable: {error}"
            try:
                await self._dispose_runtime()
            except Exception as cleanup_error:
                self.error += f"; cleanup failed: {cleanup_error}"
        finally:
            self.operation = None

    async def close(self):
        """Final application shutdown also retires the captured input."""
        self.finalized, self.closed = True, True
        self.revision = secrets.token_hex(16)
        try:
            await self._dispose_runtime()
        finally:
            if self.directory:
                self.directory.cleanup()
                self.directory = None
