"""Literal SDK234 catalogs, with no mutable LIVE catalog dependency."""

from copy import deepcopy

from .._variant_history_v1.catalogs import NATURE_TOPICS as _NATURE_TOPICS
from .._variant_history_v1.catalogs import QUESTIONS as _QUESTIONS
from .._variant_history_v1.catalogs import TOPICS as _TOPICS

NATURE_TOPICS = deepcopy(_NATURE_TOPICS)
QUESTIONS = deepcopy(_QUESTIONS)
TOPICS = deepcopy(_TOPICS)
NATURE_TOPICS["protein"] = (*NATURE_TOPICS["protein"], "sequence_changes")
TOPICS["protein"] = {
    key: value
    for name, entry in TOPICS["protein"].items()
    for key, value in (
        [
            (
                "sequence_changes",
                (
                    "Natural variants and mutagenesis",
                    "Original protein substitutions and source annotations, separate from population genomic variants.",
                ),
            ),
            (name, entry),
        ]
        if name == "literature"
        else [(name, entry)]
    )
}
QUESTIONS["protein"]["sequence_changes"] = {
    "label": "Which natural variants and experimental sequence changes are retained?",
    "topic": "sequence_changes",
    "required_options": [],
    "scope": "Original annotation occurrences, substitutions and source support; no genomic correspondence or clinical inference.",
}
