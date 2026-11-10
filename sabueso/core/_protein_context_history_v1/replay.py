"""Frozen SDK239 literal navigation over original result objects only."""

from dataclasses import replace

from .._sequence_change_history_v1.replay import ReplayExplorer as _OriginalReplay
from ..card_exploration import CardView
from ..errors import ArgumentError
from ..snapshot import canonical_json
from .adapter import ADAPTER, options_for_context
from .catalogs import NATURE_TOPICS, PROTEIN_LABELS, QUESTIONS, TOPICS
from .exploration import inherited_request


class ReplayExplorer(_OriginalReplay):
    def __init__(self, original):
        super().__init__(original)
        from ..card_protein_context_history_v1 import restore_result

        source = original.access
        self._access._scientific_cache = {}
        for ref, wire in source._objects.items():
            if (
                ref not in source._metadata_refs
                and isinstance(wire, dict)
                and "native_payload" in wire
                and wire.get("context", {}).get("adapter") == ADAPTER
                and wire["context"].get("card_ref") == source._focal.pin
                and wire["context"].get("snapshot_id") == source._focal.snapshot
            ):
                result = restore_result(ref, wire)
                key = canonical_json(
                    {
                        "adapter": ADAPTER,
                        "focal": source._focal_key,
                        "topic": wire["context"]["topic"],
                        "options": wire["context"]["options"],
                    }
                )
                self._access._scientific_cache[key] = result
        self._session["format"] = "sabueso.card_exploration@33"

    @property
    def _questions(self):
        return QUESTIONS[self.profile]

    @property
    def _nature_topics(self):
        return NATURE_TOPICS[self.profile]

    @property
    def _topics(self):
        return TOPICS[self.profile]

    def _topic_label(self, key):
        return (
            PROTEIN_LABELS[key] if self.profile == "protein" else self._topics[key][0]
        )

    def _answer(self, question, options, origin=None):
        from .exploration import view

        if question not in (
            "related_proteins",
            "protein_associations",
            "sequence_differences",
        ):
            raise ArgumentError("Question is outside original protein-context replay.")
        topic = QUESTIONS[self.profile][question]["topic"]
        if question == "sequence_differences":
            options = {**options, "mode": "sequence"}
        options = options_for_context(topic, options)
        result = view(self, topic, origin, options)
        return replace(
            result, _request={"question": question, "topic": topic, "options": options}
        )

    def _inspect(self, location, origin=None, *, title="All retained content"):
        node, full = self.access._resolve(location)
        origin = self._origin if origin is None else origin
        if full["kind"] == "card" and (
            full["card_ref"] != self.context["card_ref"]
            or full["snapshot_id"] != self.context["snapshot_id"]
        ):
            raise ArgumentError(
                "Inspection is limited to the focal capture; open a related link to switch context explicitly."
            )
        selection = self.access.read(full)
        return CardView(
            self,
            selection,
            selection._entries,
            title,
            origin,
            _request=inherited_request(origin),
            _status="ok" if selection.count else "empty",
            _reason=None if selection.count else "This retained container is empty.",
        )
