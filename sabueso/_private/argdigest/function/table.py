"""``Card.table`` passes ``**options`` to the view it runs; it admits the options of the
card views, and the view refuses one it does not take."""

from argdigest import FunctionContract

contract = FunctionContract(
    caller="sabueso.core.card.table",
    admits="view_options",
    description="Options of the card view the table is built from.",
)
