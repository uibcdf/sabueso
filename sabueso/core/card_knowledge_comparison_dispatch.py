"""Lightweight admission boundary for the new LIVE comparison profile."""

ADAPTER = "protein_knowledge_comparison_exploration@1"
SAVE_REASON = "Independent knowledge-comparison saving requires a clean producer original and frozen reader."


def pending(access):
    session = getattr(access, "_exploration_session", None)
    return bool(session and session.get("pending_knowledge_catalog")) or any(
        getattr(result, "wire", {}).get("context", {}).get("adapter") == ADAPTER
        for result in getattr(access, "_scientific_cache", {}).values()
    )
