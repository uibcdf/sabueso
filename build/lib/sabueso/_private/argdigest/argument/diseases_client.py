from sabueso._private.argdigest._shared import client


def digest_diseases_client(diseases_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("diseases_client", diseases_client, caller)
