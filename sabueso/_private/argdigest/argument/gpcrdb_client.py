from sabueso._private.argdigest._shared import client


def digest_gpcrdb_client(gpcrdb_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("gpcrdb_client", gpcrdb_client, caller)
