from sabueso._private.argdigest._shared import refuse


def digest_deck_name(deck_name, caller=None):
    """A deck name (letters, digits, ``_ . -``), ``sabueso:deck:<name>``, or a pinned
    deck reference; its form is checked where it is resolved."""
    if (
        isinstance(deck_name, str)
        and deck_name.strip()
        and not any(c.isspace() for c in deck_name.strip())
    ):
        return deck_name.strip()
    raise refuse("deck_name", deck_name, caller, "expected a deck name without spaces")
