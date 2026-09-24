from sabueso._private.argdigest._shared import boolean


def digest_include_fragments(include_fragments, caller=None):
    return boolean("include_fragments", include_fragments, caller)
