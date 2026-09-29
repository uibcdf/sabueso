from sabueso._private.argdigest._shared import boolean


def digest_disease_identity(disease_identity, caller=None):
    return boolean("disease_identity", disease_identity, caller)
