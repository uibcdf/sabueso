"""Original AlphaFold range aliases, with explicit agreement and refusal states.

The private projection below is an input to a named derivation, never a source
record. SourceAssertions retain the original model without adding legacy fields.
"""

from copy import deepcopy

from .alphafold_context_v1 import interpret as original_context

RULE = "alphafold_sequence_context@2"
QUALIFIER_PATHS = ["isoform", "sequence_matches", "sequence_context", "range"]
RANGE_FIELDS = (("uniprotStart", "uniprotEnd"), ("sequenceStart", "sequenceEnd"))


def range_basis(model):
    """Require complete positive integer pairs and agreement of every alias."""
    declarations = []
    for fields in RANGE_FIELDS:
        present = [key for key in fields if key in model]
        if not present:
            continue
        values = [deepcopy(model.get(key)) for key in fields]
        start, end = values
        state = (
            "incomplete"
            if len(present) != 2
            else "valid"
            if type(start) is int and type(end) is int and 1 <= start <= end
            else "invalid"
        )
        declarations.append(
            {
                "fields": list(fields),
                "present": present,
                "values": values,
                "state": state,
            }
        )
    invalid = [row for row in declarations if row["state"] != "valid"]
    if not declarations:
        state = "not_stated"
    elif invalid:
        state = (
            "incomplete"
            if all(row["state"] == "incomplete" for row in invalid)
            else "invalid"
        )
    elif (
        len(declarations) == 2
        and declarations[0]["values"] != declarations[1]["values"]
    ):
        state = "conflicting_aliases"
    else:
        state = "agreeing_aliases" if len(declarations) == 2 else "recorded"
    admitted = state in ("recorded", "agreeing_aliases")
    return {
        "state": state,
        "declarations": declarations,
        "resolved_range": deepcopy(declarations[0]["values"])
        if admitted
        else [None, None],
        "supporting_fields": [row["fields"] for row in declarations]
        if admitted
        else [],
    }


def interpret(model, accession, sequence_md5, assertions=None):
    """Extend the original MD5/identity policy; do not choose a range conflict."""
    basis = range_basis(model)
    projection = {**model, **dict(zip(RANGE_FIELDS[0], basis["resolved_range"]))}
    context = original_context(projection, accession, sequence_md5, assertions)
    context["rule"] = RULE
    context["range_basis"] = basis
    if basis["state"] not in ("recorded", "agreeing_aliases"):
        context["reasons"].insert(0, f"model_range_{basis['state']}")
    return context
