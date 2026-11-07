"""Exact captured target context; never resolve an unpinned identity implicitly."""

from sabueso._private.argdigest._shared import refuse
from sabueso.core.errors import StorageError
from sabueso.core.snapshot import parse_ref


def digest_target_card_ref(target_card_ref, caller=None):
    """None or a complete canonical Card pin without an item suffix.

    Membership and target applicability are checked against the actual capture,
    before scientific evaluation. No reference is stripped or coerced here.
    """
    if target_card_ref is None:
        return None
    if isinstance(target_card_ref, str):
        try:
            reference = parse_ref(target_card_ref)
        except StorageError:
            pass
        else:
            if (
                reference.snapshot_id is not None
                and reference.item_id is None
                and str(reference) == target_card_ref
            ):
                return target_card_ref
    raise refuse(
        "target_card_ref",
        target_card_ref,
        caller,
        "expected None or an exact captured Card pin without an item suffix",
    )
