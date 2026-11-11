"""Explicit display policies that preserve historical defaults through resaving."""

from copy import deepcopy

from .errors import StorageError

POLICIES = {
    "overview_orientation": "card_orientation@1",
    "chemical_context": "chemical_context_reading@1",
}
LEGACY_POLICIES = {
    "overview_orientation": "legacy_card_orientation@1",
    "chemical_context": "legacy_chemical_context@1",
}
UNMARKED_ORIENTATION_PRODUCERS = frozenset(
    ("0.14.0+248.gca4f88e", "0.14.0+249.g2d7dffc")
)


def metadata():
    return dict(POLICIES)


def validate(original):
    if isinstance(original, dict):
        for key, expected in POLICIES.items():
            if key in original and (
                type(original[key]) is not str
                or original[key] not in (expected, LEGACY_POLICIES[key])
            ):
                raise StorageError("Unsupported recorded source-context presentation.")


def enabled(view, key):
    original = view._explorer._session.get("presentation_metadata", {})
    validate(original)
    return isinstance(original, dict) and original.get(key) == POLICIES[key]


def restored_metadata(original, producer):
    """Recognize only the two documented unmarked orientation producers."""
    result = deepcopy(original)
    validate(result)
    if (
        isinstance(result, dict)
        and "overview_orientation" not in result
        and isinstance(producer, dict)
        and producer.get("sabueso_version") in UNMARKED_ORIENTATION_PRODUCERS
    ):
        # Those exact checkpoints introduced orientation, before a display marker
        # existed. They did not introduce the subsequent chemical supplement.
        result["overview_orientation"] = POLICIES["overview_orientation"]
    if isinstance(result, dict):
        # Make historical defaults explicit before a newer writer changes its
        # producer label; resaving must not upgrade the recorded display.
        for key, historical in LEGACY_POLICIES.items():
            result.setdefault(key, historical)
    return result
