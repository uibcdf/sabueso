from sabueso._private.argdigest._shared import refuse


def digest_packet(packet, caller=None):
    """A KnowledgePacket."""
    from sabueso.core.packets import KnowledgePacket

    if isinstance(packet, KnowledgePacket):
        return packet
    raise refuse("packet", packet, caller, "expected a KnowledgePacket")
