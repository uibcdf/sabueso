from sabueso._private.argdigest._shared import refuse


def digest_resolution(resolution, caller=None):
    """The EntityResolution returned with a card."""
    from sabueso.resolver import EntityResolution

    if isinstance(resolution, EntityResolution):
        return resolution
    raise refuse("resolution", resolution, caller, "expected an EntityResolution")
