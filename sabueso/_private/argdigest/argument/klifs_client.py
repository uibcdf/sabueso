from sabueso._private.argdigest._shared import client


def digest_klifs_client(klifs_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("klifs_client", klifs_client, caller)
