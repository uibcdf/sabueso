from sabueso._private.argdigest._shared import optional_text


def digest_method(method, caller=None):
    """The method the publication used, for fields compared within a method."""
    return optional_text("method", method, caller)
