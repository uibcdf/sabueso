from sabueso._private.argdigest._shared import client


def digest_oma_client(oma_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("oma_client", oma_client, caller)
