from sabueso._private.argdigest._shared import refuse


def digest_note(note, caller=None):
    """None, or a short text recorded with a stored revision."""
    if note is None or isinstance(note, str):
        return note
    raise refuse("note", note, caller, "expected a text or None")
