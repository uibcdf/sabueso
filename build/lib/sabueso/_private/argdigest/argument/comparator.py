from sabueso._private.argdigest.argument.subject import _accession


def digest_comparator(comparator, caller=None):
    """None, or a UniProt accession, bare or prefixed; returned prefixed."""
    if comparator is None:
        return None
    return _accession("comparator", comparator, caller)
