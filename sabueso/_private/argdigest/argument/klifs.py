from sabueso._private.argdigest._shared import options, positive_int


def digest_klifs(klifs, caller=None):
    """KLIFS: None (off) or options {limit}."""
    return options("klifs", klifs, caller, {"limit": positive_int})
