"""Original SDK205 shapes, independent of mutable public digesters."""

from .._bioactivity_history_v1.validation import digest_item_ref as digest_item_ref
from ..errors import ArgumentError, StorageError
from ..snapshot import parse_ref


def digest_target_card_ref(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            reference = parse_ref(value)
        except StorageError:
            pass
        else:
            if (
                reference.snapshot_id is not None
                and reference.item_id is None
                and str(reference) == value
            ):
                return value
    raise ArgumentError(
        "target_card_ref requires None or a complete canonical captured Card pin."
    )
