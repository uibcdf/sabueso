from sabueso._private.argdigest._shared import boolean


def digest_orphadata(orphadata, caller=None):
    return boolean("orphadata", orphadata, caller)
