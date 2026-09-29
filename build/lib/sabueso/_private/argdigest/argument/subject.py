from sabueso._private.argdigest._shared import refuse


def digest_subject(subject, caller=None):
    """A UniProt accession, bare (``P60174``) or prefixed (``uniprot:P60174``); returned
    prefixed."""
    return _accession("subject", subject, caller)


def _accession(name, value, caller):
    import re

    if isinstance(value, str):
        text = value.strip()
        if text.lower().startswith("uniprot:"):
            text = text.split(":", 1)[1]
        if re.fullmatch(r"[A-Z0-9]{6,10}", text):
            return f"uniprot:{text}"
    raise refuse(name, value, caller, "expected a UniProt accession, e.g. 'P60174'")
