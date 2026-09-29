from sabueso._private.argdigest._shared import boolean


def digest_ligand_sites(ligand_sites, caller=None):
    return boolean("ligand_sites", ligand_sites, caller)
