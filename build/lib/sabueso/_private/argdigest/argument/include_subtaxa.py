from sabueso._private.argdigest._shared import boolean


def digest_include_subtaxa(include_subtaxa, caller=None):
    return boolean("include_subtaxa", include_subtaxa, caller)
