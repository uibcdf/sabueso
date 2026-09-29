from sabueso._private.argdigest._shared import refuse


def digest_card_id(card_id, caller=None):
    """None (the latest stored card) or the id of a stored card."""
    if card_id is None or (isinstance(card_id, str) and card_id.strip()):
        return card_id
    raise refuse("card_id", card_id, caller, "expected a card id or None")
