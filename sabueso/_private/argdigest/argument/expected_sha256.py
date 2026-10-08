import re

from sabueso._private.argdigest._shared import refuse


def digest_expected_sha256(expected_sha256, caller=None):
    if expected_sha256 is None:
        return None
    if isinstance(expected_sha256, str) and re.fullmatch(
        r"[0-9a-fA-F]{64}", expected_sha256
    ):
        return expected_sha256.lower()
    raise refuse(
        "expected_sha256",
        expected_sha256,
        caller,
        "expected 64 hexadecimal digits or None",
    )
