from sabueso._private.argdigest._shared import refuse


def _positions(region):
    """Sorted positions from positions and inclusive ``[begin, end]`` ranges, or None."""
    if not isinstance(region, (list, tuple, set)) or not region:
        return None
    out = set()
    for item in region:
        if isinstance(item, int) and not isinstance(item, bool) and item > 0:
            out.add(item)
        elif (
            isinstance(item, (list, tuple))
            and len(item) == 2
            and all(isinstance(i, int) and not isinstance(i, bool) for i in item)
            and 0 < item[0] <= item[1]
        ):
            out.update(range(item[0], item[1] + 1))
        else:
            return None
    return sorted(out)


def digest_region(region, caller=None):
    """None, or UniProt positions and inclusive ``[begin, end]`` ranges, as sorted
    positions."""
    if region is None:
        return None
    positions = _positions(region)
    if positions is None:
        raise refuse(
            "region",
            region,
            caller,
            "expected None, or a non-empty list of positive positions and [begin, end] ranges",
        )
    return positions
