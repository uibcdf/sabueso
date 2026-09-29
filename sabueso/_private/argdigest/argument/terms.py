from sabueso._private.argdigest._shared import refuse


def digest_terms(terms, caller=None):
    """None (no profile), or a terms profile (#94): "commercial" or "non_commercial"."""
    from sabueso.core.terms import PROFILES

    if terms is None or terms in PROFILES:
        return terms
    raise refuse("terms", terms, caller, f"expected None or one of {sorted(PROFILES)}")
