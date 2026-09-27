from sabueso._private.argdigest._shared import refuse


def digest_packet_name(packet_name, caller=None):
    """A packet name (letters, digits, ``_ . -``), ``sabueso:packet:<name>``, or a
    pinned packet reference; its form is checked where it is resolved. None where the
    packet is not stored."""
    if packet_name is None:
        return None
    if (
        isinstance(packet_name, str)
        and packet_name.strip()
        and not any(c.isspace() for c in packet_name.strip())
    ):
        return packet_name.strip()
    raise refuse(
        "packet_name", packet_name, caller, "expected a packet name without spaces"
    )
