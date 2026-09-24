from datetime import date

from sabueso._private.argdigest._shared import refuse


def digest_curated_at(curated_at, caller=None):
    """None (today, UTC) or an ISO date such as 2026-09-24."""
    if curated_at is None:
        return None
    try:
        return date.fromisoformat(str(curated_at)).isoformat()
    except ValueError:
        raise refuse("curated_at", curated_at, caller, "expected an ISO date") from None
