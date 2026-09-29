from sabueso._private.argdigest._shared import client


def digest_pdbe_kb_client(pdbe_kb_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("pdbe_kb_client", pdbe_kb_client, caller)
