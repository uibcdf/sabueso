from sabueso._private.argdigest._shared import refuse


def digest_page(page, caller=None):
    """A nonnegative source page index, starting at zero."""
    if isinstance(page, bool) or not isinstance(page, int) or page < 0:
        raise refuse("page", page, caller, "expected a nonnegative integer")
    return page
