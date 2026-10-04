import re

from sabueso._private.argdigest._shared import refuse


def digest_ligand_site_ref(ligand_site_ref, caller=None):
    """An exact native has_ligand_site relationship id from this card's site view."""
    if isinstance(ligand_site_ref, str) and re.fullmatch(
        r"REL_[A-Za-z0-9_]+", ligand_site_ref
    ):
        return ligand_site_ref
    raise refuse(
        "ligand_site_ref",
        ligand_site_ref,
        caller,
        "expected a native REL_ ligand-site id",
    )
