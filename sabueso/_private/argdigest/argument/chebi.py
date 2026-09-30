from sabueso._private.argdigest._shared import boolean


def digest_chebi(chebi, caller=None):
    """ChEBI classes and roles of a molecule (#83): True or False."""
    return boolean("chebi", chebi, caller)
