from sabueso._private.argdigest._shared import client


def digest_rcsb_client(rcsb_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("rcsb_client", rcsb_client, caller)
