from sabueso._private.argdigest._shared import refuse


def digest_text(text, caller=None):
    """A non-empty text."""
    if isinstance(text, str) and text.strip():
        return text
    raise refuse("text", text, caller, "expected a non-empty text")
