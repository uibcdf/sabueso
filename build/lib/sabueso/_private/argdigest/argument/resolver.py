from sabueso._private.argdigest._shared import refuse


def digest_resolver(resolver, caller=None):
    """None (the online default) or an object able to resolve entities."""
    if resolver is None or callable(getattr(resolver, "resolve", None)):
        return resolver
    raise refuse("resolver", resolver, caller, "expected an EntityResolver or None")
