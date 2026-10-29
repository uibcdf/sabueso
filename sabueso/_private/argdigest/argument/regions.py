def digest_regions(regions, caller=None):
    """Validate shared or per-Card compact syntax without expanding positions."""
    from sabueso.core.errors import ArgumentError
    from sabueso.core.region_requests import _check, compact, current_budget

    region_budget = current_budget()
    if isinstance(regions, dict):
        _check(None, len(regions), region_budget)
        if any(
            not isinstance(key, str) or value is None for key, value in regions.items()
        ):
            raise ArgumentError("regions requires {Card id: nonempty region}.")
        _check(
            None,
            sum(
                len(value)
                for value in regions.values()
                if isinstance(value, (list, tuple, set))
            ),
            region_budget,
        )
        return {key: compact(value, region_budget) for key, value in regions.items()}
    return compact(regions, region_budget)
