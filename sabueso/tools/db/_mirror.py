"""Local source mirrors: whole releases installed once, read by the same clients (#100).

A mirror is a source's published release, downloaded once, checked against the checksum
the source publishes, and indexed on disk, so that cards can be built from it without
asking the source's service record by record.

- **Nowhere by default.** Mirrors live where the user says: ``mirror_dir=``, or
  ``$SABUESO_MIRROR_DIR``. Sabueso writes nothing otherwise.
- **Releases side by side**: ``<root>/<source>/<release>/`` holds ``release.json``
  (source, release, URL, checksum, size, when installed, row count) and the index. An
  older release stays until it is removed, so an older build can be answered by it.
- **Used only when asked**: inside ``using(...)``, a card tool asks an installed mirror
  instead of the source's service (``mirror_first``), or never the network
  (``offline``: a source without a mirror is not asked). Each enrichment records the
  access route and the release.

Adapters, one per source, implement ``latest()``, ``install(release, directory)`` and
``client(directory)``; they are listed in ``ADAPTERS``.
"""

from __future__ import annotations

import contextvars
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List

from sabueso.core.errors import StorageError

_USING: contextvars.ContextVar = contextvars.ContextVar("sabueso_mirrors", default=None)
MODES = ("mirror_first", "offline")


def root(mirror_dir: str | Path | None = None) -> Path | None:
    """Where mirrors live: ``mirror_dir``, or ``$SABUESO_MIRROR_DIR``; None if neither."""
    chosen = mirror_dir or os.environ.get("SABUESO_MIRROR_DIR")
    return Path(chosen) if chosen else None


def releases(source: str, mirror_dir: str | Path | None = None) -> List[Dict[str, Any]]:
    """The installed releases of a source, oldest first, each its ``release.json``."""
    base = root(mirror_dir)
    if base is None or not (base / source).is_dir():
        return []
    out = []
    for path in sorted((base / source).iterdir()):
        info = path / "release.json"
        if info.is_file():
            out.append(
                {
                    **json.loads(info.read_text(encoding="utf-8")),
                    "directory": str(path),
                }
            )
    return out


@contextmanager
def using(
    mirror_dir: str | Path | None = None,
    mode: str = "mirror_first",
    releases: Dict[str, str] | None = None,
) -> Iterator[Path]:
    """Within the block, card tools read installed mirrors (``mirror_first``), or never
    the network (``offline``). ``releases`` pins a source to one installed release
    (``{"bindingdb": "202609"}``); otherwise its latest installed release is read."""
    if mode not in MODES:
        raise ValueError(f"mode is one of {MODES}")
    base = root(mirror_dir)
    if base is None:
        raise StorageError(
            "No mirror directory: pass mirror_dir= or set $SABUESO_MIRROR_DIR."
        )
    token = _USING.set({"root": base, "mode": mode, "releases": dict(releases or {})})
    try:
        yield base
    finally:
        _USING.reset(token)


def active() -> Dict[str, Any] | None:
    return _USING.get()


def client_for(source: str) -> Any | None:
    """The mirror client a card tool should use for ``source`` in this context: the
    pinned or latest installed release, or None (no mirror in use or installed)."""
    state = _USING.get()
    if state is None:
        return None
    installed = releases(source, state["root"])
    pinned = state["releases"].get(source)
    if pinned is not None:
        installed = [r for r in installed if r["release"] == pinned]
        if not installed:
            raise StorageError(
                f"Release {pinned} of {source} is not installed in {state['root']}."
            )
    if not installed:
        return None
    from sabueso.mirrors import ADAPTERS

    return ADAPTERS[source].client(Path(installed[-1]["directory"]))


def offline() -> bool:
    """Whether the network must not be asked (``using(mode="offline")``)."""
    state = _USING.get()
    return state is not None and state["mode"] == "offline"
