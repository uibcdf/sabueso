# Frozen from 77fd770e4d2a8fa94eea3fbd723a84fc90875efb / SDK135.
"""Frozen symbolic wwPDB operation grammar; no coordinate or instance inference."""

import re
from decimal import Decimal
from itertools import product

RULE = "assembly_operation_expression@1"
_ID = re.compile(r"[A-Za-z0-9_]+\Z")
_RANGE = re.compile(r"(0|[1-9][0-9]*)-(0|[1-9][0-9]*)\Z")
_COUNT_MAX = 2**63 - 1


def _decimal(number):
    # Decimal's exact conversion avoids Python's decimal-int text digit ceiling.
    # The source expression itself is bounded before any numeric conversion.
    return format(Decimal(number), "f")


def parse(expression):
    """Compact source-order groups, preserving duplicates; unsupported stays raw.

    Bare IDs/lists/ranges and adjacent parenthesized products are supported.
    ASCII spaces/tabs are separators, not part of IDs. Leading-zero singleton
    IDs stay literal; zero-padded numeric ranges and other character-code syntax
    are explicitly unsupported rather than normalized into different identities.
    Callers preflight total source work before invoking this frozen parser.
    """
    result = {
        "rule": RULE,
        "expression": expression if isinstance(expression, str) else None,
        "status": "unsupported",
        "groups": [],
    }
    if not isinstance(expression, str) or not expression:
        result["reason"] = "missing_or_nonstring_expression"
        return result
    text = expression.strip(" \t")
    if text.startswith("("):
        groups = re.findall(r"\(([^()]*)\)", text)
        residue = re.sub(r"\([^()]*\)", "", text)
        if not groups or residue.strip(" \t"):
            result["reason"] = "unsupported_group_syntax"
            return result
    elif "(" in text or ")" in text:
        result["reason"] = "unsupported_group_syntax"
        return result
    else:
        groups = [text]
    parsed_groups = []
    for raw in groups:
        terms = []
        count = 0
        for token in raw.split(","):
            token = token.strip(" \t")
            interval = _RANGE.fullmatch(token)
            if interval:
                begin, end = (int(Decimal(value)) for value in interval.groups())
                if begin > end:
                    result["reason"] = "descending_range"
                    return result
                terms.append(
                    {"kind": "range", "begin": interval[1], "end": interval[2]}
                )
                count += end - begin + 1
            elif _ID.fullmatch(token):
                terms.append({"kind": "id", "id": token})
                count += 1
            else:
                result["reason"] = "unsupported_token_syntax"
                return result
        parsed_groups.append({"terms": terms, "count_decimal": _decimal(count)})
    count = 1
    for group in parsed_groups:
        n = int(Decimal(group["count_decimal"]))
        if n > _COUNT_MAX // count:
            count = None
            break
        count *= n
    result.update(
        status="parsed",
        reason=None,
        operation_count=count,
        count_state="exact" if count is not None else "factored",
        application_order="right_to_left",
        groups=parsed_groups,
    )
    return result


def expansion_count(plan, limit):
    """Preflight without products/ranges; stop arithmetic at a finite ceiling."""
    count = 1
    for group in plan["groups"]:
        n = int(Decimal(group["count_decimal"]))
        if limit is not None and n > limit // count:
            return limit + 1
        count *= n
    return count


def tuple_text_bound(plan, count):
    """Conservative ID-text cost, without allocating a range or product pool."""
    width = 0
    for group in plan["groups"]:
        width += max(
            len(term["id"]) if term["kind"] == "id" else len(term["end"])
            for term in group["terms"]
        )
    return count * width


def expand(plan):
    """Materialize only after the entire request has passed its preflight."""

    def values(group):
        for term in group["terms"]:
            if term["kind"] == "id":
                yield term["id"]
            else:
                for value in range(
                    int(Decimal(term["begin"])), int(Decimal(term["end"])) + 1
                ):
                    yield _decimal(value)

    return [list(row) for row in product(*(values(group) for group in plan["groups"]))]
