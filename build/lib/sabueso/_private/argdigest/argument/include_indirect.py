from sabueso._private.argdigest._shared import boolean


def digest_include_indirect(include_indirect, caller=None):
    return boolean("include_indirect", include_indirect, caller)
