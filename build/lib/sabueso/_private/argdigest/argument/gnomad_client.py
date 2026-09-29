from sabueso._private.argdigest._shared import client


def digest_gnomad_client(gnomad_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("gnomad_client", gnomad_client, caller)
