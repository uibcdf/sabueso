from sabueso._private.argdigest._shared import boolean


def digest_indications(indications, caller=None):
    return boolean("indications", indications, caller)
