"""Original typed sequence-change machine request binding, using frozen selection rules."""

from ..card_access import _handle
from ..errors import StorageError
from ..snapshot import canonical_json
from .adapter import TOPIC
from .selection import active, evaluate, normalize, projection, selection_ref


def require(value, message):
    if not value:
        raise StorageError(message)


def same(actual, expected, scope):
    require(
        canonical_json(actual) == canonical_json(expected),
        "Saved " + scope + " differs.",
    )


def _machine(selection, access, result):
    context = access._resolve(selection._context_location)[0]
    request = context["request"]
    fields, spec = projection(selection._fields), request.get("selection")
    if spec is None:
        entries = result.entries
        ref = _handle(
            "XA_",
            {
                "format": "scientific_access_selection@1",
                "result_ref": result.result_ref,
                "fields": fields,
            },
        )
    else:
        query = normalize(spec["where"], spec["item_refs"], spec["order_by"])
        require(
            active(query),
            "An unrestricted sequence-change selection has a foreign policy.",
        )
        entries, expected = evaluate(result, query)
        same(
            spec,
            expected,
            "sequence-change exact membership, order and exclusions",
        )
        ref = selection_ref(result, fields, expected)
    expected_request = {
        "topic": TOPIC,
        "fields": list(fields),
        "options": result.options,
    }
    if spec is not None:
        expected_request["selection"] = spec
    same(
        context,
        {"context": result.wire["context"], "request": expected_request},
        "sequence-change machine request",
    )
    require(
        selection.selection_ref == ref and selection._operation == "select:" + TOPIC,
        "Variant tissue-context machine request identity differs.",
    )
    same(
        selection._target,
        {
            "node_type": "scientific_result",
            "location": selection._target["location"],
            "size": len(result.entries),
        },
        "sequence-change machine target",
    )
    same(
        access._resolve(selection._target["location"])[1],
        result.location("native_payload"),
        "sequence-change machine native target",
    )
    return entries
