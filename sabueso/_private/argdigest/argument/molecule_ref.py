import re

from sabueso._private.argdigest._shared import refuse


def digest_molecule_ref(molecule_ref, caller=None):
    """An exact namespaced item key, without identifier resolution or case guessing."""
    if caller == "sabueso.core.card.explain_ligand":
        if isinstance(molecule_ref, str) and re.fullmatch(
            r"sabueso:small_molecule:[a-z][a-z0-9_.]*:[^\s#]+", molecule_ref
        ):
            return molecule_ref
        raise refuse(
            "molecule_ref",
            molecule_ref,
            caller,
            "expected the exact SmallMoleculeCard id from ligands(deck)",
        )
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
