from sabueso._private.argdigest._shared import boolean


def digest_taxonomy(taxonomy, caller=None):
    return boolean("taxonomy", taxonomy, caller)
