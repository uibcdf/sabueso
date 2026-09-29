from sabueso._private.argdigest._shared import refuse


def digest_structure(structure, caller=None):
    """A structure as given (a SMILES or an InChI): a non-empty string, without the
    space around it.
    Whether PubChem can read it is PubChem's answer, not an argument error."""
    if isinstance(structure, str) and structure.strip():
        return structure.strip()
    raise refuse("structure", structure, caller, "expected a non-empty string")
