from sabueso._private.argdigest._shared import boolean


def digest_uniref(uniref, caller=None):
    return boolean("uniref", uniref, caller)
