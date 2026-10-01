from sabueso._private.argdigest._shared import client


def digest_uniref_client(uniref_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("uniref_client", uniref_client, caller)
