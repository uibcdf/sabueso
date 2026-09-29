from sabueso._private.argdigest._shared import refuse


def digest_name(name, caller=None):
    """A non-empty name to search for."""
    if isinstance(name, str) and name.strip():
        return name.strip()
    raise refuse("name", name, caller, "expected a non-empty name")
