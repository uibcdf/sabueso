from sabueso._private.argdigest._shared import client


def digest_open_targets_client(open_targets_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("open_targets_client", open_targets_client, caller)
