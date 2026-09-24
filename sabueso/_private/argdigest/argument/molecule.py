from sabueso._private.argdigest._shared import refuse


def digest_molecule(molecule, caller=None):
    """A small-molecule Card, an identifier to resolve, or a recorded identity."""
    from sabueso.core.card import Card

    if isinstance(molecule, Card):
        return molecule
    if isinstance(molecule, str) and molecule.strip():
        return molecule.strip()
    if isinstance(molecule, dict) and molecule.get("inchikey"):
        return molecule
    raise refuse(
        "molecule",
        molecule,
        caller,
        "expected a small-molecule Card, an identifier, or {inchikey, records}",
    )
