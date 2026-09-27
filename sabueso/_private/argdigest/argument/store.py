from sabueso._private.argdigest._shared import refuse


def digest_store(store, caller=None):
    """None, a KnowledgeStore, or the path of one (a str or path-like)."""
    import os

    from sabueso.core.knowledge_store import KnowledgeStore

    if store is None or isinstance(store, KnowledgeStore):
        return store
    if isinstance(store, (str, os.PathLike)) and str(store):
        return KnowledgeStore(store)
    raise refuse("store", store, caller, "expected a KnowledgeStore, a path, or None")
