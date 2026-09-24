from sabueso._private.argdigest._shared import refuse


def digest_identifiers(identifiers, caller=None):
    """One identifier or an iterable of them, as a list of non-empty strings."""
    if isinstance(identifiers, str):
        identifiers = [identifiers]
    try:
        values = [str(i).strip() for i in identifiers]
    except TypeError:
        raise refuse(
            "identifiers", identifiers, caller, "expected identifiers"
        ) from None
    if not values or not all(values):
        raise refuse(
            "identifiers", identifiers, caller, "expected non-empty identifiers"
        )
    return values
