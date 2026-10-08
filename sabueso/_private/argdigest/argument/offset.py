from sabueso._private.argdigest._shared import refuse


def digest_offset(offset, caller=None):
    """A nonnegative number of source records to skip."""
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise refuse("offset", offset, caller, "expected a nonnegative integer")
    return offset
