from sabueso._private.argdigest._shared import client


def digest_interpro_client(interpro_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("interpro_client", interpro_client, caller)
