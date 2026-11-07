"""Choose historical activity semantics by the verified logical file format."""


def _sdk202(access):
    session = access._exploration_session
    return (
        access.mode == "saved"
        and session is not None
        and session.get("format") == "sabueso.card_exploration@19"
    )


def history(access):
    if _sdk202(access):
        from . import card_bioactivity_history_v2

        return card_bioactivity_history_v2
    from . import card_bioactivity_history_v1

    return card_bioactivity_history_v1


def binding(access):
    if _sdk202(access):
        from . import card_exploration_bioactivity_v2

        return card_exploration_bioactivity_v2
    from . import card_exploration_bioactivity

    return card_exploration_bioactivity
