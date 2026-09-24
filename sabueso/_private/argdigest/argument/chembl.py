from sabueso._private.argdigest._shared import options, positive_int


def digest_chembl(chembl, caller=None):
    """ChEMBL bioactivities enrichment: None (off) or options {limit}."""
    return options("chembl", chembl, caller, {"limit": positive_int})
