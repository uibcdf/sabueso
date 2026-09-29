from sabueso._private.argdigest._shared import refuse


def digest_topic(topic, caller=None):
    """The topic of a curated claim (``curation.CLAIM_TOPICS``), or None in a view."""
    from sabueso.core.curation import CLAIM_TOPICS

    if topic in CLAIM_TOPICS or (
        topic is None and caller and caller.endswith(".claims")
    ):
        return topic
    raise refuse("topic", topic, caller, f"expected one of {list(CLAIM_TOPICS)}")
