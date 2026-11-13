"""Application Deck navigation over the native captured contract."""

import json
import secrets
from copy import copy

from sabueso.core.errors import ArgumentError

from ._session import _Session


class _DeckSession:
    def __init__(self, deck, output_directory):
        self.explorer = deck.explore()
        self.current = self.explorer.overview()
        self.output_directory = output_directory
        self.revision = secrets.token_hex(16)
        self.card_session = None
        self.visit = None
        self.entry_position = None
        self.metadata_open = False
        self.cursor = None
        self.previous = []
        self.history = []

    def fork(self):
        result = copy(self)
        result.previous = list(self.previous)
        result.history = [
            (view, cursor, list(previous)) for view, cursor, previous in self.history
        ]
        result.card_session = self.card_session.fork() if self.card_session else None
        return result

    def panel(self):
        if self.card_session is not None:
            panel = self.card_session.panel()
            panel.update(
                revision=self.revision,
                can_back=True,
                deck_context={
                    **self.visit.context,
                    "scope": "entry_occurrence",
                    "entry_position": self.entry_position,
                    "current_card": self.card_session.current.context,
                },
            )
            return panel
        page = self.current.page(limit=40, max_bytes=1048576, cursor=self.cursor)
        text = f"{self.current.context['selected_count']} selected from {self.explorer.context['input_count']} retained input occurrences. Choose a member to explore its original Card; membership and metadata remain separately inspectable."
        if self.metadata_open:
            text = json.dumps(self.current.inspect(), ensure_ascii=False, indent=2)
        return {
            "format": "sabueso.explorer_panel@1",
            "workspace": "deck",
            "revision": self.revision,
            "title": "Original Deck metadata" if self.metadata_open else "Deck members",
            "text": text,
            "full_text": None,
            "result_ref": self.explorer.context["capture_ref"],
            "view_ref": self.current.view_ref,
            "mode": "live",
            "profile": "deck",
            "topics": [],
            "items": []
            if self.metadata_open
            else [
                {
                    "ref": item["member_ref"],
                    "label": item.get("card_ref") or f"Member {item['position'] + 1}",
                    "kind": f"occurrence {item['position'] + 1}",
                }
                for item in page["items"]
            ],
            "offset": page["offset"],
            "count": self.current.context["selected_count"],
            "has_previous": bool(self.previous) and not self.metadata_open,
            "has_next": page["next_cursor"] is not None and not self.metadata_open,
            "can_back": bool(self.history) or self.metadata_open,
            "can_save": False,
            "can_related": False,
            "saved_file": None,
            "outcome": {
                "status": "ok" if self.current.context["selected_count"] else "empty",
                "reason": None,
            },
        }

    def dispatch(self, request):
        if not isinstance(request, dict) or request.get("revision") != self.revision:
            raise ArgumentError("The Deck reading changed; reload before acting again.")
        name = request.get("name")
        if self.card_session is not None:
            if name == "deck" or name == "back" and not self.card_session.history:
                if set(request) != {"name", "revision"}:
                    raise ArgumentError("Unexpected Deck return arguments.")
                self.card_session = self.visit = None
                self.entry_position = None
            else:
                self.card_session.dispatch(
                    {**request, "revision": self.card_session.revision}
                )
            self.revision = secrets.token_hex(16)
            return self.panel()
        fields = {
            "open": {"item_ref"},
            "search": {"text"},
            "sort": {"column", "descending"},
            "back": set(),
            "overview": set(),
            "metadata": set(),
            "deck_next": set(),
            "deck_previous": set(),
        }
        if (
            not isinstance(name, str)
            or name not in fields
            or set(request) != {"name", "revision", *fields[name]}
        ):
            raise ArgumentError("Unknown or malformed Deck action.")
        destination = None
        if name == "open":
            if (
                self.metadata_open
                or not isinstance(request["item_ref"], str)
                or request["item_ref"]
                not in {row["ref"] for row in self.panel()["items"]}
            ):
                raise ArgumentError("Choose an occurrence from the current Deck page.")
            member = self.current.member(request["item_ref"])
            visit = member.open()
            reader = _Session(visit.overview(), self.output_directory)
            self.visit, self.card_session = visit, reader
            self.entry_position = member.position
        elif name == "metadata":
            self.metadata_open = True
        elif name == "back":
            if self.metadata_open:
                self.metadata_open = False
            elif self.history:
                self.current, self.cursor, self.previous = self.history.pop()
            else:
                raise ArgumentError("There is no previous Deck selection.")
        elif name == "deck_next":
            page = self.current.page(limit=40, max_bytes=1048576, cursor=self.cursor)
            if self.metadata_open or page["next_cursor"] is None:
                raise ArgumentError("There is no next Deck page.")
            self.previous.append(self.cursor)
            self.cursor = page["next_cursor"]
        elif name == "deck_previous":
            if self.metadata_open or not self.previous:
                raise ArgumentError("There is no previous Deck page.")
            self.cursor = self.previous.pop()
        elif name == "search":
            destination = self.current.filter(request["text"])
        elif name == "sort":
            destination = self.current.sort(
                request["column"], descending=request["descending"]
            )
        else:
            destination = self.explorer.overview()
        if destination is not None:
            if len(self.history) >= 256:
                raise ArgumentError(
                    "Deck history is full; return before opening another selection."
                )
            self.history.append((self.current, self.cursor, list(self.previous)))
            self.current, self.cursor, self.previous = destination, None, []
            self.metadata_open = False
        self.revision = secrets.token_hex(16)
        return self.panel()
