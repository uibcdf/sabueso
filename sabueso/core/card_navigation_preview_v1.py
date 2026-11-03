"""Versioned presentation of complete retained navigation, without new decisions."""

from .errors import StorageError

RULE = "question_destination_preview@1"
KEY = "navigation_preview"
LIMIT = 10


def metadata():
    return {KEY: RULE}


def rule(original):
    """An absent policy retains the historical prefix; unknown named rules fail."""
    if not isinstance(original, dict) or KEY not in original:
        return None
    if type(original[KEY]) is not str or original[KEY] != RULE:
        raise StorageError("Unsupported recorded navigation preview policy.")
    return RULE


def plan(view):
    """Return bounded display indices and role counts, never reordered members."""
    count = len(view._selected)
    if (
        not view._link_panel
        or rule(view._explorer._session.get("presentation_metadata", {})) is None
    ):
        return tuple(range(min(count, LIMIT))), ()
    groups = ([], [], [])
    totals = [0, 0, 0]
    for index, entry in enumerate(view._selected):
        role = entry.value.get("role")
        group = 0 if role == "question" else 2 if role == "source" else 1
        totals[group] += 1
        if len(groups[group]) < LIMIT:
            groups[group].append(index)
    indices, shown = [], []
    for group in groups:
        selected = group[: LIMIT - len(indices)]
        indices.extend(selected)
        shown.append(len(selected))
    return tuple(indices), tuple(zip(shown, totals))


def guidance(counts):
    """Show every category's omitted scope and the public complete-access route."""
    if not counts:
        return []
    return [
        "Navigation preview · "
        + " · ".join(
            f"{label}: {shown}/{total} shown"
            for label, (shown, total) in zip(
                ("Questions", "Destinations", "Source links"), counts
            )
        ),
        "Questions and destinations appear before source links. Indices refer to items()[i]; full membership and ordering are unchanged.",
        "All questions: filter('role', equals='question'). All source links: filter('role', equals='source').",
    ]
