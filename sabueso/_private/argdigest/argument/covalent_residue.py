from sabueso._private.argdigest._shared import refuse


def digest_covalent_residue(covalent_residue, caller=None):
    """None, or the position of the residue a covalent compound modifies."""
    if covalent_residue is None or (
        isinstance(covalent_residue, int)
        and not isinstance(covalent_residue, bool)
        and covalent_residue > 0
    ):
        return covalent_residue
    raise refuse(
        "covalent_residue", covalent_residue, caller, "expected a position or None"
    )
