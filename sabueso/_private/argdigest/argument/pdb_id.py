import re

from sabueso._private.argdigest._shared import refuse


def digest_pdb_id(pdb_id, caller=None):
    """An explicitly selected four-character PDB identifier."""
    if isinstance(pdb_id, str) and re.fullmatch(r"[1-9][A-Za-z0-9]{3}", pdb_id):
        return pdb_id.lower()
    raise refuse("pdb_id", pdb_id, caller, "expected a four-character PDB identifier")
