from sabueso._private.argdigest._shared import refuse


def digest_source_assertions(source_assertions, caller=None):
    if source_assertions is None:
        return None
    if isinstance(source_assertions, list) and all(
        isinstance(item, dict) for item in source_assertions
    ):
        return source_assertions
    raise refuse(
        "source_assertions",
        source_assertions,
        caller,
        "expected a list of SourceAssertion records or None",
    )
