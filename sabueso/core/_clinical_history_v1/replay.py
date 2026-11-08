"""Frozen SDK224 literal view construction, without public digesters or LIVE UI."""

from copy import copy, deepcopy

from ..card_access import AccessSelection, CardAccess, _Entry, _handle, _type
from ..card_exploration import CardView
from ..errors import ArgumentError
from .adapter import ADAPTER
from .catalogs import NATURE_TOPICS, QUESTIONS, TOPICS


def _key(value):
    return {"type": "Key", "value": value}


class _ReplayAccess(CardAccess):
    def read(self, location):
        node, full = self._resolve(location)
        return self._make_selection("read", full, node)

    def _children(self, value, location):
        if isinstance(value, dict):
            return tuple(
                _Entry(
                    {
                        **location,
                        "segments": [
                            *location["segments"],
                            {"type": "Key", "value": k},
                        ],
                    },
                    k,
                    v,
                )
                for k, v in sorted(value.items())
            )
        if isinstance(value, list):
            store = location["kind"] == "card" and location["segments"] in (
                [{"type": "Key", "value": "source_assertion_store"}],
                [{"type": "Key", "value": "relationship_store"}],
            )
            entries = [
                _Entry(
                    {
                        **location,
                        "segments": [
                            *location["segments"],
                            {
                                "type": "Record" if store else "Index",
                                "value": v["id"] if store else i,
                            },
                        ],
                    },
                    v["id"] if store else i,
                    v,
                    i,
                )
                for i, v in enumerate(value)
            ]
            return tuple(sorted(entries, key=lambda e: e.key) if store else entries)
        return (_Entry(location, None, value),)

    def _make_selection(self, operation, location, value, text_slice=None):
        request = {
            "operation": operation,
            "location": location,
            "text_slice": text_slice,
        }
        result_ref = _handle(
            "XR_",
            {
                "format": "literal_access_result@1",
                "inputs": sorted(self._captures),
                "request": request,
            },
        )
        selection_ref = _handle(
            "XA_",
            {
                "format": "card_access_selection@1",
                "result_ref": result_ref,
                "request": request,
            },
        )
        if selection_ref not in self._selections:
            entries = (
                (_Entry(location, None, value),)
                if text_slice is not None
                else self._children(value, location)
            )
            context_location = self._object_location(
                {"context": self.context, "request": request}
            )
            self._selections[selection_ref] = AccessSelection(
                self,
                result_ref,
                selection_ref,
                entries,
                context_location,
                {
                    "node_type": _type(value),
                    "size": len(value)
                    if isinstance(value, (dict, list, str))
                    else None,
                    "location": self._location(location),
                    "owner": {
                        key: location[key]
                        for key in ("card_ref", "snapshot_id", "result_ref")
                        if key in location
                    },
                },
                operation,
                text_slice,
            )
        return self._selections[selection_ref]


class ReplayExplorer:
    def __init__(self, original):
        source = original.access
        self._access = object.__new__(_ReplayAccess)
        for name in CardAccess.__slots__:
            setattr(self._access, name, getattr(source, name, None))
        self._access._objects = dict(source._objects)
        self._access._locations = dict(source._locations)
        self._access._metadata_refs = set(source._metadata_refs)
        self._access._mode = "live"
        self._access._selections = {}
        self._access._scientific_cache = {
            (ADAPTER, source._focal_key): result
            for result, _ in source._scientific_items.values()
            if result.wire["context"]["adapter"] == ADAPTER
        }
        # An empty result has no item index. Reuse its already validated wire,
        # including the producer's generated rule label, rather than recomputing it.
        from ..card_clinical_history_v1 import restore_result

        for ref, wire in source._objects.items():
            if (
                ref not in source._metadata_refs
                and isinstance(wire, dict)
                and wire.get("context", {}).get("adapter") == ADAPTER
                and wire["context"].get("used_captures") == [source._focal_key]
            ):
                self._access._scientific_cache[(ADAPTER, source._focal_key)] = (
                    restore_result(ref, wire)
                )
        self._session = {"views": {}, "explanations": {}, "links": {}}
        self._origin = original._origin
        self._coverage_result = None
        self._navigation_cache = {}

    @property
    def access(self):
        return self._access

    @property
    def context(self):
        return self.access.context

    @property
    def profile(self):
        return self.access.profile

    @property
    def mode(self):
        return "live"

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
        return self._topics[key][0]

    def shadow(self, view):
        value = copy(view)
        object.__setattr__(value, "_explorer", self)
        object.__setattr__(value, "_saved_state", None)
        return value

    def _location(self, *keys):
        return self.access._card_location(segments=[_key(key) for key in keys])

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
            _status="ok" if selection.count else "empty",
            _reason=None if selection.count else "This retained container is empty.",
        )

    def _metadata(self, value, title, origin=None):
        return self._inspect(self.access._object_location(value), origin, title=title)

    def _support(self, location):
        """Nearest original field/record support; metadata is never source evidence."""
        if location["kind"] != "card":
            return [{"basis": "navigation_metadata", "location": deepcopy(location)}]
        segments = location["segments"]
        # Start at the outside: objects nested inside a field's original value
        # cannot redeclare lineage merely by resembling a field node.
        for stop in range(1, len(segments) + 1):
            owner = {**location, "segments": segments[:stop]}
            node, _ = self.access._resolve(owner)
            store = segments[0]["value"]
            if stop == 2 and store == "source_assertion_store":
                return [{"basis": "original_assertion", "location": owner}]
            relationship = stop == 2 and store == "relationship_store"
            field_support = (
                store == "sections"
                and isinstance(node, dict)
                and "value" in node
                and isinstance(node.get("source_assertion_ids"), list)
                and all(isinstance(ref, str) for ref in node["source_assertion_ids"])
            )
            if relationship or field_support:
                refs = node.get("source_assertion_ids", [])
                support = {
                    "basis": "relationship_level"
                    if relationship
                    else "original_field_support",
                    "location": owner,
                    "source_assertion_ids": deepcopy(refs),
                    "statements": [self._statement(ref) for ref in refs]
                    if isinstance(refs, list)
                    and all(isinstance(ref, str) for ref in refs)
                    else [],
                }
                if relationship:
                    for key in (
                        "derivation",
                        "derivation_applications",
                        "qualifier_conflicts",
                    ):
                        if key in node:
                            support[key] = deepcopy(node[key])
                    if (
                        node.get("predicate") == "has_predicted_structure"
                        and isinstance(node.get("qualifiers"), dict)
                        and (
                            isinstance(
                                (node.get("qualifiers") or {}).get("sequence_context"),
                                dict,
                            )
                            or (
                                isinstance(
                                    node["qualifiers"].get("native_reference_context"),
                                    dict,
                                )
                                and node["qualifiers"]["native_reference_context"].get(
                                    "rule"
                                )
                                == "alphafold_modelcif_reference_context@1"
                            )
                        )
                    ):
                        applications = node.get("derivation_applications")
                        inputs = set()
                        for app in (
                            applications if isinstance(applications, list) else []
                        ):
                            derivation = (
                                app.get("derivation") if isinstance(app, dict) else None
                            )
                            if not isinstance(derivation, dict) or derivation.get(
                                "rule"
                            ) not in (
                                "alphafold_sequence_context@1",
                                "alphafold_sequence_context@2",
                                "alphafold_modelcif_reference_context@1",
                            ):
                                continue
                            declared = derivation.get("inputs")
                            if isinstance(declared, list):
                                inputs.update(
                                    ref
                                    for ref in declared
                                    if isinstance(ref, str) and ref.startswith("SA_")
                                )
                        support["derivation_input_statements"] = [
                            self._statement(ref)
                            for ref in sorted(inputs)
                            if ref not in (refs if isinstance(refs, list) else [])
                        ]
                return [support]
        return [{"basis": "stored_literal", "location": deepcopy(location)}]

    def _statement(self, ref):
        location = {
            **self._location("source_assertion_store"),
            "segments": [
                _key("source_assertion_store"),
                {"type": "Record", "value": ref},
            ],
        }
        try:
            self.access._resolve(location)
        except ArgumentError:
            return {"id": ref, "state": "not_retained", "location": None}
        return {"id": ref, "state": "present", "location": location}
