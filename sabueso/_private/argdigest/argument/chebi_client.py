from sabueso._private.argdigest._shared import client


def digest_chebi_client(chebi_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("chebi_client", chebi_client, caller)
