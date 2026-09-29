from sabueso._private.argdigest._shared import client


def digest_string_client(string_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("string_client", string_client, caller)
