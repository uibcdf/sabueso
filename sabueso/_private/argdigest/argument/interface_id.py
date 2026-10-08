from sabueso._private.argdigest._shared import positive_int, refuse


def digest_interface_id(interface_id, caller=None):
    reason = positive_int(interface_id)
    if reason:
        raise refuse("interface_id", interface_id, caller, reason)
    return interface_id
