from sabueso._private.argdigest._shared import refuse


def digest_reference(reference, caller=None):
    """None, or the card id whose numbering the residue maps target."""
    if reference is None or (isinstance(reference, str) and reference.strip()):
        return reference
    raise refuse("reference", reference, caller, "expected None or a card id")
