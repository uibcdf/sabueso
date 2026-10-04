from sabueso._private.argdigest._shared import refuse


def digest_knowledge_source(knowledge_source, caller=None):
    """An optional exact knowledge-state source name, without name matching."""
    if knowledge_source is None:
        return None
    if isinstance(knowledge_source, str) and knowledge_source.strip():
        return knowledge_source.strip()
    raise refuse(
        "knowledge_source",
        knowledge_source,
        caller,
        "expected None or a nonempty source name",
    )
