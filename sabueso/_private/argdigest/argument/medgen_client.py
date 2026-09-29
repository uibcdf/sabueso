from sabueso._private.argdigest._shared import client


def digest_medgen_client(medgen_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("medgen_client", medgen_client, caller)
