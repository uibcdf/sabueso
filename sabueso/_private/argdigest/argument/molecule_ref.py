import re

from sabueso._private.argdigest._shared import refuse


def digest_molecule_ref(molecule_ref, caller=None):
    """An exact namespaced item key, without identifier resolution or case guessing."""
    if isinstance(molecule_ref, str) and re.fullmatch(
        r"[a-z][a-z0-9_.]*:[^\s#]+", molecule_ref
    ):
        return molecule_ref
    raise refuse(
        "molecule_ref",
        molecule_ref,
        caller,
        "expected an exact namespaced bioactivity item key",
    )
