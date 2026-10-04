from sabueso._private.argdigest._shared import refuse


def digest_knowledge_area(knowledge_area, caller=None):
    """An optional exact knowledge-state area selector, without aliases."""
    if knowledge_area is None:
        return None
    if isinstance(knowledge_area, str) and knowledge_area.strip():
        return knowledge_area.strip()
    raise refuse(
        "knowledge_area",
        knowledge_area,
        caller,
        "expected None or a nonempty area name",
    )
