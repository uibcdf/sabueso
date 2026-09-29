from sabueso._private.argdigest._shared import options, positive_int


def digest_europepmc(europepmc, caller=None):
    """Europe PMC mentions: None (off) or options {limit}."""
    return options("europepmc", europepmc, caller, {"limit": positive_int})
