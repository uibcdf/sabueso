"""Bounded development binding to Viewer's experimental public client service.

This does not establish Card/model identity or copy a provider protocol. #368
owns the supported embedding contract; the reviewed source cohort owns this
explicitly experimental receiving scope. Input-byte limits are not a model RAM
guarantee; large/model-residency qualification remains separate under Viewer #55.
"""

from __future__ import annotations

import gzip
import hashlib
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
        target = self._capture()
        self.service = RemoteSessionService(render_on="client")
        self.view = MolSysView(transport=self.service.channel)
        # Startup happens before the application is served. The provider owns
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
            "status": "unavailable"
            if self.error
            else "closed"
            if self.closed
            else "experimental",
            "error": self.error,
            "initial_file_name": self.source.name,
            "initial_input_digest": self.input_digest,
            "correspondence": "not_established",
            "client_url": self.service.client_url if self.origin else None,
            "initial_renderer_ready": observed("client_render_ready"),
            "initial_structure_received": observed("client_structure_complete"),
            "client_registrations": getattr(
                self.service, "client_registration_count", None
            ),
            "camera_snapshot": self.view.camera.get_snapshot()
            if self.view and not self.error
            else None,
            "active_selection_indices": self.view.active_selection.atom_indices
            if self.view and not self.error
            else [],
        }

    async def close(self):
        try:
            if self.service:
                await self.service.close()
                self.service = None
        finally:
            try:
                if self.view:
                    self.view.close()
                    self.view = None
            finally:
                if self.directory:
                    self.directory.cleanup()
                    self.directory = None
                self.closed = True
