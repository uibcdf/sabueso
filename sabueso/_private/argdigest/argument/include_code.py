from sabueso._private.argdigest._shared import boolean


def digest_include_code(include_code, caller=None):
    return boolean("include_code", include_code, caller)
