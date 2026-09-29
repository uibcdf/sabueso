from sabueso._private.argdigest._shared import refuse


def digest_notation(notation, caller=None):
    """A structure notation PubChem matches: ``smiles`` or ``inchi``."""
    from sabueso.tools.db.pubchem import NOTATIONS

    if notation in NOTATIONS:
        return notation
    raise refuse("notation", notation, caller, f"expected one of {list(NOTATIONS)}")
