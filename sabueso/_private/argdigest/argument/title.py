from sabueso._private.argdigest._shared import optional_text


def digest_title(title, caller=None):
    return optional_text("title", title, caller)
