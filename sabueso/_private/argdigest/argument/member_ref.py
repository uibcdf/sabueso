import re

from sabueso._private.argdigest._shared import refuse


def digest_member_ref(member_ref, caller=None):
    if isinstance(member_ref, str) and re.fullmatch(r"DM_[0-9a-f]{64}", member_ref):
        return member_ref
    raise refuse(
        "member_ref", member_ref, caller, "expected a captured DM_ member reference"
    )
