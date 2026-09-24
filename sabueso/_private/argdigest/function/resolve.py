"""``sabueso.resolve`` passes ``**options`` to the card tool it routes to.

It admits the options of either tool; the tool it calls refuses one it does not take,
so an option meant for the other kind of entity fails loudly instead of being ignored.
"""

from argdigest import FunctionContract

contract = FunctionContract(
    caller="sabueso.tools.resolve.resolve",
    admits="card_options",
    description="Options of the card tool the query is routed to.",
)
