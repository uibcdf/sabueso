from sabueso._private.argdigest._shared import refuse


def digest_deck_name(deck_name, caller=None):
    """The name a deck is stored under in a knowledge store."""
    if isinstance(deck_name, str) and deck_name.strip():
        return deck_name.strip()
    raise refuse("deck_name", deck_name, caller, "expected a non-empty name")
