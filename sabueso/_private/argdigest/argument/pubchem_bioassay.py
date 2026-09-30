from sabueso._private.argdigest._shared import options, positive_int, refuse


def digest_pubchem_bioassay(pubchem_bioassay, caller=None):
    """PubChem BioAssay results: True or False, or options {limit} (#98)."""
    if isinstance(pubchem_bioassay, bool):
        return pubchem_bioassay
    if isinstance(pubchem_bioassay, dict):
        return options(
            "pubchem_bioassay", pubchem_bioassay, caller, {"limit": positive_int}
        )
    raise refuse(
        "pubchem_bioassay",
        pubchem_bioassay,
        caller,
        "expected True, False or a dict of options",
    )
