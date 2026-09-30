from sabueso._private.argdigest._shared import client


def digest_sabdab_client(sabdab_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("sabdab_client", sabdab_client, caller)
