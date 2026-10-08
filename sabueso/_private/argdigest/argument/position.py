from sabueso._private.argdigest._shared import positive_int, refuse


def digest_position(position, caller=None):
    reason = positive_int(position)
    if reason:
        raise refuse("position", position, caller, reason)
    return position
