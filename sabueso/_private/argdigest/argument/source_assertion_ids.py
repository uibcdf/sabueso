from sabueso._private.argdigest._shared import refuse


def digest_source_assertion_ids(source_assertion_ids, caller=None):
    """One SourceAssertion id or several, as a list of strings."""
    if isinstance(source_assertion_ids, str):
        source_assertion_ids = [source_assertion_ids]
    try:
        values = [str(i).strip() for i in source_assertion_ids]
    except TypeError:
        values = []
    if values and all(values):
        return values
    raise refuse(
        "source_assertion_ids",
        source_assertion_ids,
        caller,
        "expected SourceAssertion ids",
    )
