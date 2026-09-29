from sabueso._private.argdigest._shared import path_list


def digest_fields(fields, caller=None):
    """One field path, or an iterable of field paths; returned as a list."""
    return path_list("fields", fields, caller)
