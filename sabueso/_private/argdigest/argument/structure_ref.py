import re

from sabueso._private.argdigest._shared import refuse


def digest_structure_ref(structure_ref, caller=None):
    """None, or an experimental structure reference such as ``pdb:1SUX``."""
    if structure_ref is None:
        return None
    if isinstance(structure_ref, str):
        match = re.fullmatch(r"pdb:([A-Za-z0-9]{4})", structure_ref.strip(), re.I)
        if match:
            return f"pdb:{match[1].upper()}"
    raise refuse(
        "structure_ref",
        structure_ref,
        caller,
        'expected None or "pdb:<four-character id>"',
    )
