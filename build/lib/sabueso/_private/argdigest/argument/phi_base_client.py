from sabueso._private.argdigest._shared import client


def digest_phi_base_client(phi_base_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("phi_base_client", phi_base_client, caller)
