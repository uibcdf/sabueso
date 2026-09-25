from sabueso._private.argdigest._shared import client


def digest_taxonomy_client(taxonomy_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("taxonomy_client", taxonomy_client, caller)
