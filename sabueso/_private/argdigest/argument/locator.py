from sabueso._private.argdigest._shared import optional_text


def digest_locator(locator, caller=None):
    """Where in the publication: a figure, table, page or section."""
    return optional_text("locator", locator, caller)
