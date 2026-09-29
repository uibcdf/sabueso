from sabueso._private.argdigest._shared import client


def digest_mondo_client(mondo_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("mondo_client", mondo_client, caller)
