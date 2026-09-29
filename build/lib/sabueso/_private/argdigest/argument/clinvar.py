from sabueso._private.argdigest._shared import options, positive_int


def digest_clinvar(clinvar, caller=None):
    """ClinVar variants: None (off) or options {limit}."""
    return options("clinvar", clinvar, caller, {"limit": positive_int})
