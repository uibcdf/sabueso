from sabueso._private.argdigest._shared import client


def digest_europepmc_client(europepmc_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("europepmc_client", europepmc_client, caller)
