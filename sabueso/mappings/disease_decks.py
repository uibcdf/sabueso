"""Native disease association rows, kept separate from derived deck membership."""

from copy import deepcopy

from sabueso.core.source_assertion_store import make_source_assertion


def native_assertion(source, record, value, response, subject, *, indication=False):
    assertion = make_source_assertion(
        "relationships.investigated_for"
        if indication
        else "relationships.associated_with",
        deepcopy(value),
        source,
        record,
        response.get("retrieved_at") or "",
        subject_ref=subject,
    )
    if response.get("version") is not None:
        assertion["source"]["version"] = str(response["version"])
    return assertion
