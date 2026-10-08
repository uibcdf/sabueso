import re

from sabueso._private.argdigest._shared import refuse


def digest_checksum(checksum, caller=None):
    if isinstance(checksum, str) and re.fullmatch(r"[0-9a-fA-F]{32}", checksum):
        return checksum.upper()
    raise refuse(
        "checksum", checksum, caller, "expected a 32-digit MD5 sequence search key"
    )
