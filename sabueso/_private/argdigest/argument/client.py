from sabueso._private.argdigest._shared import client as _client


def digest_client(client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return _client("client", client, caller)
