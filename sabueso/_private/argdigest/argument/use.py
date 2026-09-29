from sabueso._private.argdigest._shared import refuse


def digest_use(use, caller=None):
    """An intended use of knowledge (#29): internal_research, academic_publication,
    redistribution, derived_dataset or commercial_product."""
    from sabueso.core.terms import USES

    if use in USES:
        return use
    raise refuse("use", use, caller, f"expected one of {', '.join(USES)}")
