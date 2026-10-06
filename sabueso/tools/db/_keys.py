"""Personal keys for sources that ask for one (#86).

Some sources answer only with a personal key (BRENDA, VEuPathDB, BioGRID…); others
answer without one, but faster with one (NCBI: 10 requests per second instead of 3).
Keys belong to the user, never to Sabueso:

- the user supplies their own, as the client's ``api_key``, or in the environment
  variable ``SABUESO_<SERVICE>_KEY`` (e.g. ``SABUESO_NCBI_KEY``);
- Sabueso never stores, logs or ships a key: it is sent only to its own service, never
  written into a card, a record or a cache, and ``scrub`` takes it out of any message
  that could echo it;
- a source that needs a key it was not given is not asked (``required`` raises
  ``MissingKeyError``), and an enrichment records ``not_queried`` with the reason, never
  an error.
"""

from __future__ import annotations

import os

from sabueso.core.errors import MissingKeyError


def variable(service: str) -> str:
    """The environment variable of a service's key: ``SABUESO_<SERVICE>_KEY``."""
    return f"SABUESO_{service.upper().replace('-', '_')}_KEY"


def key(service: str, api_key: str | None = None) -> str | None:
    """The key given (``api_key``), else the one in the environment, else None."""
    return api_key or os.environ.get(variable(service)) or None


def required(service: str, api_key: str | None = None, source: str | None = None):
    """The key, or ``MissingKeyError`` naming where to put one."""
    found = key(service, api_key)
    if found is None:
        raise MissingKeyError(
            f"{source or service} answers only with a personal key; none was given "
            f"(api_key=, or ${variable(service)})."
        )
    return found


def scrub(text: str, api_key: str | None) -> str:
    """``text`` without the key, for messages that could echo a URL carrying it."""
    from urllib.parse import quote, quote_plus

    if api_key:
        for value in (quote_plus(api_key), quote(api_key, safe=""), api_key):
            text = text.replace(value, "<key>")
    return text
