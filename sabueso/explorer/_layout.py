"""Versioned presentation only; never restore Knowledge or a molecular model."""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path

from sabueso.core.errors import ArgumentError

FORMAT = "sabueso.presentation_layout@1"
RENDERER = "dockview@8.9.0"
LIMIT = 64 * 1024
COMPONENTS = {
    "reading": "reading",
    "orientation": "orientation",
    "molecular": "molecular",
}


def _validate(value):
    def bounded(item, depth=0):
        if depth > 16:
            raise ArgumentError("The presentation layout is too deeply nested.")
        if isinstance(item, dict):
            if len(item) > 32 or any(
                not isinstance(k, str)
                or len(k) > 128
                or k in {"__proto__", "constructor", "prototype"}
                for k in item
            ):
                raise ArgumentError("The presentation layout has unsupported fields.")
            for child in item.values():
                bounded(child, depth + 1)
        elif isinstance(item, list):
            if len(item) > 32:
                raise ArgumentError("The presentation layout has too many entries.")
            for child in item:
                bounded(child, depth + 1)
        elif isinstance(item, str):
            if len(item) > 256:
                raise ArgumentError("Presentation text exceeds its supported scope.")
        elif item is not None and type(item) not in {bool, int, float}:
            raise ArgumentError("The presentation layout must contain JSON values.")
        elif type(item) in {int, float} and (
            abs(item) > 1_000_000 or not math.isfinite(item)
        ):
            raise ArgumentError("The presentation layout has an invalid dimension.")

    bounded(value)
    if (
        not isinstance(value, dict)
        or set(value) != {"format", "renderer", "workspace"}
        or value["format"] != FORMAT
        or value["renderer"] != RENDERER
    ):
        raise ArgumentError("Unsupported presentation layout version or renderer.")
    workspace = value["workspace"]
    if (
        not isinstance(workspace, dict)
        or not {"grid", "panels"} <= set(workspace)
        or set(workspace)
        - {"grid", "panels", "activeGroup", "floatingGroups", "popoutGroups"}
        or workspace.get("popoutGroups", []) != []
    ):
        raise ArgumentError("Only the received in-page presentation is supported.")
    panels = workspace["panels"]
    if (
        not isinstance(panels, dict)
        or "reading" not in panels
        or set(panels) - set(COMPONENTS)
    ):
        raise ArgumentError("Keep the Knowledge panel in the saved presentation.")
    for key, panel in panels.items():
        if (
            not isinstance(panel, dict)
            or panel.get("id") != key
            or panel.get("contentComponent") != COMPONENTS[key]
            or panel.get("title")
            != {
                "reading": "Knowledge",
                "orientation": "Context",
                "molecular": "Molecular model",
            }[key]
            or not isinstance(panel.get("renderer", "onlyWhenVisible"), str)
            or panel.get("renderer", "onlyWhenVisible")
            not in {"always", "onlyWhenVisible"}
            or panel.get("params")
            or panel.get("tabComponent")
            or set(panel)
            - {
                "id",
                "contentComponent",
                "title",
                "renderer",
                "params",
                "minimumWidth",
                "minimumHeight",
                "maximumWidth",
                "maximumHeight",
            }
        ):
            raise ArgumentError("Unsupported panel or data in the presentation.")
    members, groups = [], set()

    def group(data):
        if (
            not isinstance(data, dict)
            or set(data) - {"id", "views", "activeView"}
            or not isinstance(data.get("id"), str)
            or data["id"] in groups
            or not isinstance(data.get("views"), list)
            or not data["views"]
            or any(not isinstance(v, str) or v not in panels for v in data["views"])
            or (
                data.get("activeView") is not None
                and not isinstance(data["activeView"], str)
            )
            or data.get("activeView") not in {None, *data["views"]}
        ):
            raise ArgumentError("Invalid panel group in the presentation.")
        groups.add(data["id"])
        members.extend(data["views"])

    def node(data):
        if not isinstance(data, dict) or set(data) - {
            "type",
            "data",
            "size",
            "visible",
        }:
            raise ArgumentError("Invalid presentation grid.")
        if data.get("type") == "leaf":
            group(data.get("data"))
        elif data.get("type") == "branch" and isinstance(data.get("data"), list):
            for child in data["data"]:
                node(child)
        else:
            raise ArgumentError("Invalid presentation grid node.")

    def grid(data):
        if (
            not isinstance(data, dict)
            or set(data) != {"root", "orientation", "width", "height"}
            or not isinstance(data.get("orientation"), str)
            or data["orientation"] not in {"HORIZONTAL", "VERTICAL"}
            or any(
                type(data.get(k)) not in {int, float} or data[k] < 0
                for k in ("width", "height")
            )
        ):
            raise ArgumentError("Invalid presentation grid dimensions.")
        node(data.get("root"))

    grid(workspace["grid"])
    floating = workspace.get("floatingGroups", [])
    if not isinstance(floating, list):
        raise ArgumentError("Invalid floating presentation groups.")
    for item in floating:
        if (
            not isinstance(item, dict)
            or set(item) - {"data", "grid", "position"}
            or not isinstance(item.get("position"), dict)
            or set(item["position"])
            - {"left", "top", "right", "bottom", "width", "height"}
            or any(type(v) not in {int, float} for v in item["position"].values())
        ):
            raise ArgumentError("Invalid floating presentation position.")
        if "data" in item and "grid" not in item:
            group(item["data"])
        elif "grid" in item and "data" not in item:
            grid(item["grid"])
        else:
            raise ArgumentError("Invalid floating presentation layout.")
    if (
        len(members) != len(set(members))
        or set(members) != set(panels)
        or (
            workspace.get("activeGroup") is not None
            and not isinstance(workspace["activeGroup"], str)
        )
        or workspace.get("activeGroup") not in {None, *groups}
    ):
        raise ArgumentError(
            "The presentation has missing or repeated panel references."
        )
    raw = json.dumps(value, allow_nan=False, ensure_ascii=False).encode("utf-8")
    if len(raw) > LIMIT:
        raise ArgumentError("The presentation layout exceeds 64 KiB.")
    return raw


class _Layout:
    def __init__(self, directory):
        self.path = Path(directory) / "presentation-layout.json"

    def read(self):
        try:
            if self.path.is_symlink():
                raise ArgumentError("A presentation file cannot be a symbolic link.")
            if not self.path.exists():
                return {"layout": None, "error": None}
            with self.path.open("rb") as source:
                raw = source.read(LIMIT + 1)
            if len(raw) > LIMIT:
                raise ArgumentError("Unsupported presentation file or size.")
            value = json.loads(raw)
            _validate(value)
            return {"layout": value, "error": None}
        except (OSError, ValueError, RecursionError, ArgumentError) as error:
            return {"layout": None, "error": str(error)}

    def save(self, value):
        raw = _validate(value)
        if self.read()["error"]:
            raise ArgumentError(
                "The existing presentation cannot be read. Move it aside before saving a replacement."
            )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(
            prefix=".presentation-", dir=self.path.parent
        )
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(raw)
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)
        return self.read()
