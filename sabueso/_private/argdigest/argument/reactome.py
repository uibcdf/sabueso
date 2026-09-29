from sabueso._private.argdigest._shared import boolean


def digest_reactome(reactome, caller=None):
    return boolean("reactome", reactome, caller)
