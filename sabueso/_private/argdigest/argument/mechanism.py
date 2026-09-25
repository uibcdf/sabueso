from sabueso._private.argdigest._shared import refuse


def digest_mechanism(mechanism, caller=None):
    """How a compound acts on the residues a paper names (``curation.MECHANISMS``)."""
    from sabueso.core.curation import MECHANISMS

    if mechanism in MECHANISMS:
        return mechanism
    raise refuse("mechanism", mechanism, caller, f"expected one of {list(MECHANISMS)}")
