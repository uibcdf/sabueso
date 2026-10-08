from sabueso._private.argdigest._shared import refuse


def digest_release(release, caller=None):
    """A non-empty release selector; the source validates its native syntax."""
    if isinstance(release, str) and release.strip():
        return release.strip()
    raise refuse("release", release, caller, "expected a non-empty release selector")
