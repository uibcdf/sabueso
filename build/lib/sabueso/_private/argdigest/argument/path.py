import os

from sabueso._private.argdigest._shared import refuse


def digest_path(path, caller=None):
    """A file path: a string or a path-like object."""
    if isinstance(path, (str, os.PathLike)) and str(path):
        return path
    raise refuse("path", path, caller, "expected a file path")
