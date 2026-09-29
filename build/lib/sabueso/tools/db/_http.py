"""One way for source clients to name themselves over HTTP (#82, #83).

Some servers refuse Python's default user agent (DISEASES's downloads and Reactome's
Content Service answer 403). Sabueso names itself and its version, as a well-behaved
client should, with one user agent shared by every client that uses ``request``.
"""

from __future__ import annotations

from typing import Dict
from urllib.request import Request


def user_agent() -> str:
    from sabueso import __version__

    return f"Sabueso/{__version__} (+https://github.com/uibcdf/sabueso)"


def request(
    url: str, data: bytes | None = None, headers: Dict[str, str] | None = None
) -> Request:
    """A ``Request`` carrying Sabueso's user agent (and any other headers)."""
    return Request(
        url, data=data, headers={"User-Agent": user_agent(), **(headers or {})}
    )
