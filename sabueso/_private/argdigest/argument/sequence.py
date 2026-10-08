from sabueso._private.argdigest._shared import refuse


def digest_sequence(sequence, caller=None):
    """Only the stored canonical sequence; isoform positions need their own sequence."""
    if sequence == "canonical":
        return sequence
    raise refuse(
        "sequence", sequence, caller, "only the stored canonical sequence is supported"
    )
