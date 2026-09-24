from sabueso._private.argdigest._shared import refuse


def digest_units(units, caller=None):
    """None, or ``{column: unit}`` for quantity columns to express as numbers."""
    if units is None:
        return None
    if isinstance(units, dict) and all(
        isinstance(k, str) and isinstance(v, str) and v.strip()
        for k, v in units.items()
    ):
        return units
    raise refuse("units", units, caller, "expected {column: unit name}")
