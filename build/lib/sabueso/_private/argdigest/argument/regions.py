from sabueso._private.argdigest._shared import refuse
from sabueso._private.argdigest.argument.region import _positions


def digest_regions(regions, caller=None):
    """None, one region for every card, or ``{card_id: region}``."""
    if regions is None:
        return None
    if isinstance(regions, dict):
        out = {}
        for key, region in regions.items():
            positions = _positions(region)
            if not isinstance(key, str) or positions is None:
                raise refuse(
                    "regions",
                    regions,
                    caller,
                    "expected {card_id: region}, a region being positions and [begin, end] ranges",
                )
            out[key] = positions
        return out
    positions = _positions(regions)
    if positions is None:
        raise refuse(
            "regions",
            regions,
            caller,
            "expected None, a region, or {card_id: region}",
        )
    return positions
