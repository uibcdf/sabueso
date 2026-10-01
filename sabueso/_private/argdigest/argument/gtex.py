from sabueso._private.argdigest._shared import boolean


def digest_gtex(gtex, caller=None):
    return boolean("gtex", gtex, caller)
