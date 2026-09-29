from sabueso._private.argdigest._shared import path_list


def digest_field_paths(field_paths, caller=None):
    """One field path, or an iterable of field paths; returned as a list."""
    return path_list("field_paths", field_paths, caller)
