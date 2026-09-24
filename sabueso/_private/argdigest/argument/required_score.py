from sabueso._private.argdigest._shared import refuse


def digest_required_score(required_score, caller=None):
    """A STRING score, 0 to 1000."""
    if isinstance(required_score, int) and not isinstance(required_score, bool):
        if 0 <= required_score <= 1000:
            return required_score
    raise refuse("required_score", required_score, caller, "expected an int in 0..1000")
