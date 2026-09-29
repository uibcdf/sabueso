from sabueso._private.argdigest._shared import boolean


def digest_pubchem_bioassay(pubchem_bioassay, caller=None):
    return boolean("pubchem_bioassay", pubchem_bioassay, caller)
