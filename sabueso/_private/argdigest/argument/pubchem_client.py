from sabueso._private.argdigest._shared import client


def digest_pubchem_client(pubchem_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("pubchem_client", pubchem_client, caller)
