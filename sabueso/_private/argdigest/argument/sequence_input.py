from sabueso._private.argdigest._shared import refuse


def digest_sequence_input(sequence_input, caller=None):
    if isinstance(sequence_input, str) and sequence_input.strip():
        return sequence_input
    raise refuse(
        "sequence_input",
        sequence_input,
        caller,
        "expected one raw or FASTA sequence as text",
    )
