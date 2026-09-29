from sabueso._private.argdigest._shared import client


def digest_chembl_client(chembl_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("chembl_client", chembl_client, caller)
