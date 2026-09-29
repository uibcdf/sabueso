from sabueso._private.argdigest._shared import refuse


def digest_profile(profile, caller=None):
    """None or a packaged enrichment profile, named with its version (``name@1``)."""
    from sabueso.resolver.loader import load_enrichment_profiles

    if profile is None:
        return None
    known = load_enrichment_profiles()
    if profile in known:
        return profile
    raise refuse("profile", profile, caller, f"expected one of {sorted(known)}")
