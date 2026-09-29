from sabueso._private.argdigest._shared import client


def digest_bindingdb_client(bindingdb_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("bindingdb_client", bindingdb_client, caller)
