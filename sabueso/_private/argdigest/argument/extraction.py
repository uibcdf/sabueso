from sabueso._private.argdigest._shared import refuse


def digest_extraction(extraction, caller=None):
    """The detached result of the delivered literal literature rule."""
    if isinstance(extraction, dict):
        return extraction
    raise refuse(
        "extraction", extraction, caller, "expected a literal extraction result"
    )
