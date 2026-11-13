from sabueso._private.argdigest._shared import refuse
from sabueso._private.argdigest.argument.member_ref import digest_member_ref


def digest_member_refs(member_refs, caller=None):
    if not isinstance(member_refs, (list, tuple)):
        raise refuse(
            "member_refs",
            member_refs,
            caller,
            "expected a list or tuple of captured member references",
        )
    return tuple(digest_member_ref(value, caller) for value in member_refs)
