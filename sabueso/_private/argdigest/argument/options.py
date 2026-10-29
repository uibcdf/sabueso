from sabueso._private.argdigest._shared import refuse

ENTITY_TYPES = ("protein", "small_molecule", "disease")


def digest_options(options, caller=None):
    """None, or resolve options per entity type: ``{"protein": {...}, ...}``."""
    if options is None:
        return None
    if caller in {
        "sabueso.core.card_access.select",
        "sabueso.core.card_exploration.view",
        "sabueso.core.card_exploration.answer",
    }:
        if isinstance(options, dict):
            from copy import deepcopy

            from sabueso.core.region_requests import compact, current_budget

            if "region" in options:
                compact(options["region"], current_budget())

            return deepcopy(options)
        raise refuse(
            "options", options, caller, "expected scientific options as a mapping"
        )
    if isinstance(options, dict) and all(
        k in ENTITY_TYPES and isinstance(v, dict) for k, v in options.items()
    ):
        return options
    raise refuse(
        "options",
        options,
        caller,
        f"expected a dict of option dicts keyed by {', '.join(ENTITY_TYPES)}",
    )
