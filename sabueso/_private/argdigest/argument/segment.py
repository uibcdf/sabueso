from sabueso._private.argdigest._shared import positive_int, refuse


def digest_segment(segment, caller=None):
    reason = positive_int(segment)
    if reason:
        raise refuse("segment", segment, caller, reason)
    return segment
