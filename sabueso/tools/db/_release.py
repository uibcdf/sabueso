"""Release caches: sources published as whole, versioned releases (#83, #86).

PHI-base, DISEASES and Orphadata publish no per-gene API; a client downloads a release
and indexes it. This module is how every such client keeps that index
(``devguide/CACHE_POLICY.md``):

- **In memory by default**, for the life of the process (``remembered``, ``recall``,
  ``keep``), keyed by source and release, so a release is downloaded once however many
  cards ask.
- **On disk only when told** (``cache_directory``): the ``cache_dir=`` a client was
  given, or ``$SABUESO_CACHE_DIR``. Sabueso has no default path.
- **Written atomically** (``write_release``): files are staged next to their target and
  renamed into place, so an interrupted write never leaves a release half cached.
- **Checked** (``verify_md5``, ``verify_sha256``) against the checksum the source
  publishes, when it publishes one.

A release never changes once published, so a cached release does not expire; a newer
release is a new key.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Hashable

from sabueso.core.errors import ConnectorError

#: Indexed releases, per ``(source, release)``, for the life of the process.
_MEMORY: Dict[tuple, Any] = {}


def cache_directory(source: str, cache_dir: str | Path | None = None) -> Path | None:
    """``<root>/<source>``, where ``root`` is ``cache_dir`` or ``$SABUESO_CACHE_DIR``;
    None when the user chose neither: Sabueso keeps no files unless told where."""
    root = cache_dir or os.environ.get("SABUESO_CACHE_DIR")
    return Path(root) / source if root else None


def remembered(source: str, release: Hashable, build: Callable[[], Any]) -> Any:
    """The release's index kept in memory, built once (``build()``) per process."""
    key = (source, release)
    if key not in _MEMORY:
        _MEMORY[key] = build()
    return _MEMORY[key]


def recall(source: str, release: Hashable) -> Any:
    """The release's index kept in memory, or None."""
    return _MEMORY.get((source, release))


def keep(source: str, release: Hashable, index: Any) -> Any:
    """Keep a release's index in memory for the process."""
    _MEMORY[(source, release)] = index
    return index


def forget(source: str | None = None) -> None:
    """Drop the releases kept in memory (every source's, or one source's)."""
    for key in [k for k in _MEMORY if source is None or k[0] == source]:
        del _MEMORY[key]


def verify_md5(payload: bytes, md5: str, what: str) -> None:
    if hashlib.md5(payload).hexdigest() != md5:  # nosec - the source's own checksum
        raise ConnectorError(f"{what} does not match its published checksum.")


def verify_sha256(payload: bytes, sha256: str, what: str) -> None:
    if hashlib.sha256(payload).hexdigest() != sha256:
        raise ConnectorError(f"{what} does not match its published checksum.")


def write_release(target: Path, files: Dict[str, str]) -> Path:
    """Write ``files`` (relative path → text) as the directory ``target``, atomically."""
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=target.parent))
    try:
        for name, text in files.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        if target.exists():
            shutil.rmtree(target)
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target


def write_file(path: Path, text: str) -> Path:
    """Write one cached file atomically (staged, then renamed into place)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, staging = tempfile.mkstemp(dir=path.parent, suffix=".part")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(staging, path)
    finally:
        if os.path.exists(staging):
            os.remove(staging)
    return path
