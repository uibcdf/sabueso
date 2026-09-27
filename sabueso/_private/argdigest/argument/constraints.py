from sabueso._private.argdigest._shared import refuse


def digest_constraints(constraints, caller=None):
    """None, or a mapping of known constraints: ``bioactivity_sources``, a non-empty
    sequence of distinct sources among ``sabueso.core.packets.BIOACTIVITY_SOURCES``."""
    from collections.abc import Mapping

    from sabueso.core.packets import BIOACTIVITY_SOURCES, CONSTRAINTS

    if constraints is None:
        return None
    if isinstance(constraints, Mapping) and set(constraints) <= set(CONSTRAINTS):
        sources = constraints.get(
            "bioactivity_sources", CONSTRAINTS["bioactivity_sources"]
        )
        if isinstance(sources, str):
            sources = (sources,)
        if (
            isinstance(sources, (list, tuple))
            and sources
            and all(s in BIOACTIVITY_SOURCES for s in sources)
            and len(set(sources)) == len(sources)
        ):
            return {"bioactivity_sources": tuple(sources)}
    raise refuse(
        "constraints",
        constraints,
        caller,
        "expected None or {'bioactivity_sources': [...]} among "
        + ", ".join(BIOACTIVITY_SOURCES),
    )
