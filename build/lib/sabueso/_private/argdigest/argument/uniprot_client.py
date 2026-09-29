from sabueso._private.argdigest._shared import client


def digest_uniprot_client(uniprot_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("uniprot_client", uniprot_client, caller)
