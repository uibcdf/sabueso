from sabueso._private.argdigest._shared import positive_int, refuse


def digest_limit(limit, caller=None):
    """A positive number of records."""
    reason = positive_int(limit)
    if reason:
        raise refuse("limit", limit, caller, reason)
    return limit
