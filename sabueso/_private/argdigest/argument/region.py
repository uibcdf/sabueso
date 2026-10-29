def digest_region(region, caller=None):
    """Validate compact positions/ranges; expand only after reference admission."""
    from sabueso.core.region_requests import compact, current_budget

    return compact(region, current_budget())
