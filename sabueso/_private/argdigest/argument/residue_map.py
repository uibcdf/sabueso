from sabueso._private.argdigest._shared import refuse


def digest_residue_map(residue_map, caller=None):
    """None, or ``{position: position}`` with positive integer residue numbers."""
    if residue_map is None:
        return None
    if isinstance(residue_map, dict) and all(
        isinstance(k, int)
        and isinstance(v, int)
        and not isinstance(k, bool)
        and not isinstance(v, bool)
        and k > 0
        and v > 0
        for k, v in residue_map.items()
    ):
        return residue_map
    raise refuse(
        "residue_map",
        residue_map,
        caller,
        "expected None or {position: position} with positive integers",
    )
