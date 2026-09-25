from sabueso._private.argdigest._shared import refuse


def digest_ref(ref, caller=None):
    """A card reference, ``<card_id>[@<snapshot_id>][#<item_id>]`` (sabueso.core.snapshot).

    Its form is checked where it is resolved, so a malformed pin is reported as such.
    """
    if isinstance(ref, str) and ref.strip():
        return ref.strip()
    raise refuse("ref", ref, caller, "expected a card reference such as 'sabueso:...'")
