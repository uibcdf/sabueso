"""``sabueso.knowledge_packet`` takes ``**clients``: how the sources are reached, never
what is asked of them (the query decides that)."""

from argdigest import FunctionContract

contract = FunctionContract(
    caller="sabueso.tools.packet.knowledge_packet",
    admits="source_clients",
    description="A resolver and source clients for the card tools.",
)
