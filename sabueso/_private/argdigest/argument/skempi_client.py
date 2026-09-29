from sabueso._private.argdigest._shared import client


def digest_skempi_client(skempi_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("skempi_client", skempi_client, caller)
