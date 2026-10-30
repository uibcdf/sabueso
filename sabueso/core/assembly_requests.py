"""Live receiving limits, separate from frozen symbolic operation grammar."""

from .errors import ArgumentError, _diagnostic_details_allowed

DEFAULT_OPERATION_BUDGET = 100_000


def budget(value):
    if value is not None and (type(value) is not int or value < 1):
        raise ArgumentError(
            "operation_budget requires a positive integer or None.",
            argument="operation_budget",
        )
    return value


def check_work(size, limit, phase, *, upper_bound=False):
    if limit is not None and size > limit:
        detailed = _diagnostic_details_allowed()
        message = (
            f"Assembly {phase} exceeds operation_budget={limit}. "
            if detailed
            else "Assembly request exceeds operation_budget. "
        )
        error = ArgumentError(
            message
            + "No operation tuples were expanded. Raise operation_budget or pass "
            "operation_budget=None deliberately; source and syntax validation still apply.",
            argument="operation_budget",
        )
        error.extra["reason"] = "assembly_operation_budget_exceeded"
        if detailed:
            error.extra["assembly_workload"] = {
                "phase": phase,
                "operation_budget": limit,
                "expanded": False,
                **(
                    {"basis": "conservative_upper_bound", "upper_bound": size}
                    if upper_bound
                    else {"basis": "at_least", "at_least": limit + 1}
                ),
            }
        raise error
