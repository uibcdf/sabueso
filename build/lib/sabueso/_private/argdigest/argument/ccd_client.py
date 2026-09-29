from sabueso._private.argdigest._shared import client


def digest_ccd_client(ccd_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("ccd_client", ccd_client, caller)
