import re

from sabueso._private.argdigest._shared import refuse


def digest_disease_ref(disease_ref, caller=None):
    """A MONDO group selector; namespace formatting never resolves another ontology."""
    if isinstance(disease_ref, str):
        match = re.fullmatch(r"(?:mondo:)?MONDO:([0-9]{7})", disease_ref.strip(), re.I)
        if match:
            return f"mondo:MONDO:{match[1]}"
    raise refuse(
        "disease_ref",
        disease_ref,
        caller,
        'expected "mondo:MONDO:<seven-digit id>" or "MONDO:<seven-digit id>"',
    )
