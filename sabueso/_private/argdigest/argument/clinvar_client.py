from sabueso._private.argdigest._shared import client


def digest_clinvar_client(clinvar_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("clinvar_client", clinvar_client, caller)
