from sabueso._private.argdigest._shared import client


def digest_unichem_client(unichem_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("unichem_client", unichem_client, caller)
