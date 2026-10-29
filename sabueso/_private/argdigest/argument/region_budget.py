def digest_region_budget(region_budget, caller=None):
    """Positive receiving budget, or explicit None for no application ceiling."""
    from sabueso.core.region_requests import budget

    return budget(region_budget)
