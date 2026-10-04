import re

from sabueso._private.argdigest._shared import refuse


def digest_measurement_ref(measurement_ref, caller=None):
    """An exact native relationship or measurement group id, local to this card."""
    if isinstance(measurement_ref, str) and re.fullmatch(
        r"(?:REL_[A-Za-z0-9_]+|MG_[0-9a-f]{16})", measurement_ref
    ):
        return measurement_ref
    raise refuse(
        "measurement_ref", measurement_ref, caller, "expected a native REL_ or MG_ id"
    )
