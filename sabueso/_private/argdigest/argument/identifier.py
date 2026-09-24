from sabueso._private.argdigest._shared import refuse


def digest_identifier(identifier, caller=None):
    """A non-empty string. Whether it names a supported record is the resolver's answer
    (``status="unsupported"``), recorded in the resolution, not an argument error."""
    if isinstance(identifier, str) and identifier.strip():
        return identifier.strip()
    raise refuse("identifier", identifier, caller, "expected a non-empty string")
