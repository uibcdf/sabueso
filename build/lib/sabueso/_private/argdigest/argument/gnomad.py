from sabueso._private.argdigest._shared import options, positive_int


def digest_gnomad(gnomad, caller=None):
    """gnomAD variants: None (off) or options {limit}."""
    return options("gnomad", gnomad, caller, {"limit": positive_int})
