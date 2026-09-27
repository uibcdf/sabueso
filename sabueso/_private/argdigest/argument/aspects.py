from sabueso._private.argdigest._shared import refuse


def digest_aspects(aspects, caller=None):
    """None (every aspect), or a non-empty sequence of distinct aspect names of
    ``sabueso.core.packets.ASPECTS``."""
    from sabueso.core.packets import ASPECTS

    if aspects is None:
        return None
    if isinstance(aspects, str):
        aspects = (aspects,)
    if (
        isinstance(aspects, (list, tuple))
        and aspects
        and all(isinstance(a, str) and a in ASPECTS for a in aspects)
        and len(set(aspects)) == len(aspects)
    ):
        return tuple(aspects)
    raise refuse(
        "aspects",
        aspects,
        caller,
        f"expected None or distinct aspects among {', '.join(sorted(ASPECTS))}",
    )
