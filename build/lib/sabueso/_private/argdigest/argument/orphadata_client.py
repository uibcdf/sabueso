from sabueso._private.argdigest._shared import client


def digest_orphadata_client(orphadata_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("orphadata_client", orphadata_client, caller)
