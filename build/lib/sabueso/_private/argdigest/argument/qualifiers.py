from sabueso._private.argdigest._shared import refuse


def digest_qualifiers(qualifiers, caller=None):
    """None or a dict of the relationship's qualifiers."""
    if qualifiers is None or isinstance(qualifiers, dict):
        return qualifiers
    raise refuse("qualifiers", qualifiers, caller, "expected a dict or None")
