"""Host-independent, source-free application session over existing Card readers."""

from __future__ import annotations

import secrets
from copy import copy
from pathlib import Path

from sabueso.core.errors import ArgumentError

PAGE_SIZE = 40
TEXT_SIZE = 4096
HISTORY_LIMIT = 256


class _Session:
    """A single captured reading; owned by one serialized backend worker."""

    def __init__(self, view, output_directory):
        self.current = view
        self.explorer = view.explorer
        self.output_directory = Path(output_directory)
        self.history = []
        self.offset = 0
        self.text_offset = 0
        self.revision = secrets.token_hex(16)
        self.saved = None

    @classmethod
    def from_card(cls, card, output_directory):
        return cls(card.explore().overview(), output_directory)

    @classmethod
    def from_saved(cls, path, output_directory):
        from sabueso import read_exploration

        return cls(read_exploration(path), output_directory)

    def panel(self):
        from ._presentation import (
            item_preview,
            orientation,
            relationship_graph,
            text_kind,
        )
        from ._record_queries import item_query

        view = self.current
        items = view.items()
        visible = items[self.offset : self.offset + PAGE_SIZE]
        topics = self.explorer.topics().native_payload if self.explorer else {}
        native = view.native_payload
        full_text = None
        if isinstance(native, str):
            full_text = {
                "kind": text_kind(view),
                "text": native[self.text_offset : self.text_offset + TEXT_SIZE],
                "offset": self.text_offset,
                "count": len(native),
                "has_previous": self.text_offset > 0,
                "has_next": self.text_offset + TEXT_SIZE < len(native),
            }
        return {
            "format": "sabueso.explorer_panel@1",
            "revision": self.revision,
            "title": view.title,
            "text": str(view),
            "full_text": full_text,
            "result_ref": view.result_ref,
            "view_ref": view.view_ref,
            "mode": self.explorer.mode if self.explorer else "context",
            "profile": self.explorer.profile if self.explorer else "context",
            "topics": [
                {"name": key, **descriptor} for key, descriptor in topics.items()
            ],
            "orientation": orientation(view),
            "graph": relationship_graph(visible),
            "trail": [
                {"index": index, "title": prior.title}
                for index, (prior, _, _) in enumerate(self.history)
            ],
            "grain": view.schema.get("grain"),
            "items": [
                {
                    "ref": item.item_ref,
                    "label": item.label,
                    "kind": item.kind,
                    "preview": item_preview(item),
                    "query_record": item_query(view, item),
                }
                for item in visible
            ],
            "offset": self.offset,
            "count": len(items),
            "has_previous": self.offset > 0,
            "has_next": self.offset + PAGE_SIZE < len(items),
            "can_back": bool(self.history),
            "can_save": view.capabilities["save"],
            "can_related": view.capabilities["related"],
            "saved_file": self.saved[0].name if self.saved else None,
            "outcome": view.outcome,
        }

    def fork(self):
        """Retain an exact return point while sharing the immutable Card capture."""
        result = copy(self)
        result.history = list(self.history)
        return result

    def dispatch(self, request):
        """Admit only finite, exact-current-context application actions."""
        if not isinstance(request, dict):
            raise ArgumentError("An exploration action must be an object.")
        name = request.get("name")
        fields = {
            "topic": {"topic"},
            "open": {"item_ref"},
            "related": {"item_ref"},
            "search": {"text"},
            "page": {"offset"},
            "text_page": {"offset"},
            "back": set(),
            "overview": set(),
            "save": set(),
            "reopen": set(),
            "filter_cell": {"item_ref", "column"},
            "back_to": {"history_index"},
            "orientation_field": {"path"},
        }
        if not isinstance(name, str) or name not in fields:
            raise ArgumentError("Unknown exploration action.")
        if set(request) != {"name", "revision", *fields[name]}:
            raise ArgumentError("The action has missing or unexpected arguments.")
        if request["revision"] != self.revision:
            raise ArgumentError("The reading changed; reload before acting again.")
        if (
            name not in {"page", "text_page", "back", "back_to", "save"}
            and len(self.history) >= HISTORY_LIMIT
        ):
            raise ArgumentError(
                "Return to an earlier reading before opening another; history is full."
            )
        destination = None
        if name == "text_page":
            offset = request["offset"]
            text = self.current.native_payload
            if (
                not isinstance(text, str)
                or type(offset) is not int
                or offset < 0
                or offset % TEXT_SIZE
                or offset >= max(1, len(text))
            ):
                raise ArgumentError("Invalid text page in the current reading.")
            self.text_offset = offset
        elif name == "page":
            offset = request["offset"]
            if (
                type(offset) is not int
                or offset < 0
                or offset % PAGE_SIZE
                or offset >= max(1, len(self.current.items()))
            ):
                raise ArgumentError("Invalid page in the current reading.")
            self.offset = offset
        elif name == "back_to":
            index = request["history_index"]
            if type(index) is not int or not 0 <= index < len(self.history):
                raise ArgumentError(
                    "Choose an exact retained point in this reading trail."
                )
            self.current, self.offset, self.text_offset = self.history[index]
            self.history = self.history[:index]
            self.explorer = self.current.explorer
        elif name == "back":
            if not self.history:
                raise ArgumentError("There is no previous reading.")
            self.current, self.offset, self.text_offset = self.history.pop()
            self.explorer = self.current.explorer
        elif name == "save":
            self.output_directory.mkdir(parents=True, exist_ok=True)
            path = self.output_directory / f"reading-{secrets.token_hex(12)}.json.gz"
            receipt = self.current.save(path, compression="gzip")
            self.saved = (path, receipt["bundle_digest"])
        elif name == "reopen":
            from sabueso import read_exploration

            if self.saved is None:
                raise ArgumentError("Save a reading before reopening it.")
            destination = read_exploration(self.saved[0], expected_digest=self.saved[1])
        elif name in {"open", "related", "filter_cell"}:
            ref = request["item_ref"]
            visible = self.current.items()[self.offset : self.offset + PAGE_SIZE]
            if not isinstance(ref, str) or ref not in {
                item.item_ref for item in visible
            }:
                raise ArgumentError("Choose an item from the current page.")
            item = self.current.item(ref)
            if name == "filter_cell":
                column = request["column"]
                if not isinstance(column, str) or column not in item.cells:
                    raise ArgumentError("Choose an original cell from this reading.")
                destination = self.current.filter(
                    column, equals=item.cells[column].value
                )
            else:
                destination = item.open() if name == "open" else item.related()
        elif name == "orientation_field":
            from sabueso.core.card_orientation_v1 import reading

            context = reading(self.current, source_limit=0, copy_values=False)
            path = request["path"]
            matches = (
                [field for field in context["fields"] if field["path"] == path]
                if context
                else []
            )
            if (
                not isinstance(path, str)
                or len(matches) != 1
                or matches[0]["field_location"] is None
            ):
                raise ArgumentError("Choose a retained field from this Card overview.")
            destination = self.explorer.inspect(locator=matches[0]["field_location"])
        else:
            if self.explorer is None:
                raise ArgumentError("This reading has no navigable Card context.")
            if name == "topic":
                topic = request["topic"]
                if (
                    not isinstance(topic, str)
                    or topic not in self.explorer.topics().native_payload
                ):
                    raise ArgumentError("Choose a topic from this captured Card.")
                destination = self.explorer.view(topic)
            elif name == "search":
                text = request["text"]
                if not isinstance(text, str) or not text.strip() or len(text) > 512:
                    raise ArgumentError("Search needs 1–512 characters.")
                destination = self.explorer.search(text)
            else:
                destination = self.explorer.overview()
        if destination is not None:
            self.history.append((self.current, self.offset, self.text_offset))
            self.history = self.history[-HISTORY_LIMIT:]
            self.current, self.offset = destination, 0
            self.text_offset = 0
            self.explorer = destination.explorer
        self.revision = secrets.token_hex(16)
        return self.panel()
