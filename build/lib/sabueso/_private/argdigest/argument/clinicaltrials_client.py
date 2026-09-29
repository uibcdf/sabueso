from sabueso._private.argdigest._shared import client


def digest_clinicaltrials_client(clinicaltrials_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("clinicaltrials_client", clinicaltrials_client, caller)
