from sabueso._private.argdigest._shared import boolean


def digest_pubchem(pubchem, caller=None):
    return boolean("pubchem", pubchem, caller)
