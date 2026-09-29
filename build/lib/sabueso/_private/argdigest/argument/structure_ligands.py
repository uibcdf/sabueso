from sabueso._private.argdigest._shared import refuse

CHOICES = ("of_interest", "all", None)


def digest_structure_ligands(structure_ligands, caller=None):
    """Which structure ligands enter a ligand deck: "of_interest", "all" or None."""
    if structure_ligands in CHOICES:
        return structure_ligands
    raise refuse(
        "structure_ligands",
        structure_ligands,
        caller,
        'expected "of_interest", "all" or None',
    )
