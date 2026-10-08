from sabueso._private.argdigest._shared import refuse


def digest_sequence_ref(sequence_ref, caller=None):
    if (
        isinstance(sequence_ref, str)
        and sequence_ref
        and (
            sequence_ref == "canonical"
            or (
                ":" in sequence_ref
                and all(sequence_ref.split(":", 1))
                and not any(c.isspace() for c in sequence_ref)
            )
        )
    ):
        return sequence_ref
    raise refuse(
        "sequence_ref",
        sequence_ref,
        caller,
        "expected canonical or an explicit namespaced sequence reference",
    )
