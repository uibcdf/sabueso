from sabueso._private.argdigest._shared import client


def digest_alphafold_client(alphafold_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("alphafold_client", alphafold_client, caller)
