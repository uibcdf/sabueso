from sabueso._private.argdigest._shared import refuse


def digest_curator(curator, caller=None):
    """Who curated the assertion: a person or an agent, never anonymous."""
    if isinstance(curator, str) and curator.strip():
        return curator.strip()
    raise refuse("curator", curator, caller, "expected a non-empty name")
