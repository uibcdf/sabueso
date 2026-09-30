"""Local mirrors of sources: install whole releases, keep them up to date, use them
(#100, phase 2).

A mirror lets cards be built from a source's published release on disk instead of its
service: faster, without the network, and every card of a project on the same release.
Nothing is downloaded unless asked, and only where the user says (``mirror_dir=`` or
``$SABUESO_MIRROR_DIR``).

.. code-block:: python

    import sabueso.mirrors as mirrors

    mirrors.install("bindingdb", mirror_dir="/data/sabueso-mirrors")  # latest release
    mirrors.status("/data/sabueso-mirrors")  # installed releases, sizes, updates
    with mirrors.using("/data/sabueso-mirrors"):
        card, _ = sabueso.resolve("P00533", bindingdb={})  # read from the mirror

Update policies (``update``): ``manual`` (only when called: install the newest release),
``notify`` (say whether a newer release exists, change nothing), and ``auto`` (install
the newest and keep the previous ``keep`` releases). A release in use by ``using(...,
releases={...})`` is never switched silently.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict

from sabueso.core.errors import StorageError
from sabueso.tools.db._mirror import MODES, releases, root, using
from sabueso.tools.db.bindingdb_mirror import BindingDBMirror

#: Sources that can be mirrored, by name.
ADAPTERS: Dict[str, Any] = {"bindingdb": BindingDBMirror()}
POLICIES = ("manual", "notify", "auto")

__all__ = ["ADAPTERS", "MODES", "install", "remove", "status", "update", "using"]


def _adapter(source: str) -> Any:
    if source not in ADAPTERS:
        raise ValueError(
            f"No mirror for {source!r}; mirrors exist for {sorted(ADAPTERS)}"
        )
    return ADAPTERS[source]


def _base(mirror_dir: Any) -> Path:
    base = root(mirror_dir)
    if base is None:
        raise StorageError(
            "No mirror directory: pass mirror_dir= or set $SABUESO_MIRROR_DIR."
        )
    return base


def install(
    source: str,
    release: str = "latest",
    mirror_dir: str | Path | None = None,
    from_file: str | Path | None = None,
    md5: str | None = None,
) -> Dict[str, Any]:
    """Install a release of ``source`` (the newest one by default); nothing is done if
    it is installed already. ``from_file`` indexes a file already downloaded; it is
    checked against the published checksum all the same (``md5`` when it is already
    known, else fetched)."""
    adapter = _adapter(source)
    base = _base(mirror_dir)
    if release == "latest":
        release = adapter.latest()
    for installed in releases(source, base):
        if installed["release"] == release:
            return installed
    info = adapter.install(
        release, base / source / release, from_file=from_file, md5=md5
    )
    return {**info, "directory": str(base / source / release)}


def remove(source: str, release: str, mirror_dir: str | Path | None = None) -> None:
    """Remove an installed release."""
    base = _base(mirror_dir)
    target = base / source / release
    if not (target / "release.json").is_file():
        raise StorageError(f"Release {release} of {source} is not installed in {base}.")
    shutil.rmtree(target)


def status(mirror_dir: str | Path | None = None, check: bool = False) -> Dict[str, Any]:
    """Per mirrorable source, its installed releases (with their size on disk); with
    ``check``, also the newest release the source publishes."""
    base = _base(mirror_dir)
    out: Dict[str, Any] = {}
    for source, adapter in sorted(ADAPTERS.items()):
        installed = []
        for info in releases(source, base):
            size = sum(
                f.stat().st_size
                for f in Path(info["directory"]).rglob("*")
                if f.is_file()
            )
            installed.append({**info, "bytes": size})
        entry: Dict[str, Any] = {"installed": installed}
        if check:
            entry["latest"] = adapter.latest()
            entry["up_to_date"] = bool(installed) and (
                installed[-1]["release"] == entry["latest"]
            )
        out[source] = entry
    return out


def update(
    source: str,
    policy: str = "manual",
    keep: int = 2,
    mirror_dir: str | Path | None = None,
) -> Dict[str, Any]:
    """Apply an update policy to ``source``'s mirror; see the module docstring."""
    if policy not in POLICIES:
        raise ValueError(f"policy is one of {POLICIES}")
    adapter = _adapter(source)
    base = _base(mirror_dir)
    latest = adapter.latest()
    installed = [r["release"] for r in releases(source, base)]
    newer = latest not in installed
    if policy == "notify" or not newer:
        return {
            "source": source,
            "latest": latest,
            "installed": installed,
            "newer": newer,
        }
    info = install(source, latest, base)
    removed = []
    if policy == "auto":
        current = [r["release"] for r in releases(source, base)]
        for old in current[: max(0, len(current) - keep)]:
            remove(source, old, base)
            removed.append(old)
    return {
        "source": source,
        "latest": latest,
        "installed": info["release"],
        "removed": removed,
        "newer": True,
    }
