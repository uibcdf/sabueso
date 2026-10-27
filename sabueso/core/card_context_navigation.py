"""Source-supported navigation over detached supplied captures, never acquisition."""

from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from dataclasses import replace

from .card_access import _Entry
from .errors import StorageError
from .snapshot import parse_ref

RULE = "retained_context_links@2"


def _location(capture, segments=()):
    return {
        "format": "card_access_location@1",
        "kind": "card",
        "card_ref": capture.pin,
        "snapshot_id": capture.snapshot,
        "segments": list(segments),
    }


def _record(capture, store, ref):
    return _location(
        capture,
        [{"type": "Key", "value": store}, {"type": "Record", "value": ref}],
    )


def _identity(capture):
    ref = capture.data["meta"].get("card_id")
    return ref.split(":", 2)[2] if ref else None


def _graph(explorer):
    edges, blocked = [], []
    for _, capture in sorted(explorer.access._captures.items()):
        statements = {row["id"] for row in capture.data["source_assertion_store"]}
        for row in sorted(
            capture.data["relationship_store"], key=lambda row: row["id"]
        ):
            if row.get("predicate") != "same_as":
                continue
            refs = row.get("source_assertion_ids", [])
            refs = (
                refs
                if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs)
                else []
            )
            retained = [ref for ref in refs if ref in statements]
            edge = {
                "subject_ref": row["subject_ref"],
                "object_ref": row["object_ref"],
                "location": _record(capture, "relationship_store", row["id"]),
                "source_assertions": [
                    _record(capture, "source_assertion_store", ref) for ref in retained
                ],
                "missing_source_assertion_ids": [
                    ref for ref in refs if ref not in statements
                ],
                "basis": "source_stated_same_as",
            }
            # A derived/similarity relationship or a dangling assertion reference
            # cannot establish a source-stated identity path.
            (
                edges if retained and not row.get("qualifier_conflicts") else blocked
            ).append(edge)
    return edges, blocked


def _resolve(explorer, target):
    cache = explorer._navigation_cache
    key = ("target", target)
    if key not in cache:
        cache[key] = _resolve_target(explorer, target)
    return deepcopy(cache[key])


def _resolve_target(explorer, target):
    """Return candidates and the retained identity graph, without choosing a revision."""
    captures = explorer.access._captures
    if target.startswith("sabueso:"):
        try:
            ref = parse_ref(target)
        except StorageError:
            return {
                "candidates": [],
                "paths": [],
                "blocked_paths": [],
                "availability": "missing_prerequisite",
            }
        candidates = []
        matched_card = False
        for key, capture in sorted(captures.items()):
            if capture.data["meta"].get("card_id") != ref.card_id:
                continue
            if ref.snapshot_id and capture.snapshot != ref.snapshot_id:
                continue
            matched_card = True
            segments = []
            if ref.item_id:
                store = (
                    "source_assertion_store"
                    if ref.item_id.startswith("SA_")
                    else "relationship_store"
                )
                if not any(row["id"] == ref.item_id for row in capture.data[store]):
                    continue
                segments = _record(capture, store, ref.item_id)["segments"]
            candidates.append(
                {
                    "capture": key,
                    "location": _location(capture, segments),
                    "basis": "exact_pinned_record"
                    if ref.item_id
                    else "exact_card_reference",
                }
            )
        return {
            "candidates": candidates,
            "paths": [],
            "blocked_paths": [],
            "availability": "ambiguous"
            if len(candidates) > 1
            else "available"
            if candidates
            else "missing_prerequisite"
            if matched_card
            else "context_not_supplied",
        }
    if "identity_graph" not in explorer._navigation_cache:
        explorer._navigation_cache["identity_graph"] = _graph(explorer)
    edges, blocked = explorer._navigation_cache["identity_graph"]
    adjacency = defaultdict(list)
    for edge in edges:
        a, b = edge["subject_ref"], edge["object_ref"]
        adjacency[a].append(b)
        adjacency[b].append(a)
    reached, queue = {target}, deque([target])
    while queue:
        for neighbor in adjacency[queue.popleft()]:
            if neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    # Preserve the connected graph, rather than enumerating exponentially many
    # cyclic paths. Every agreeing and conflicting retained identity edge survives.
    paths = [edge for edge in edges if edge["subject_ref"] in reached]
    blocked = [
        edge
        for edge in blocked
        if edge["subject_ref"] in reached or edge["object_ref"] in reached
    ]
    candidates = [
        {
            "capture": key,
            "location": _location(capture),
            "basis": "exact_entity_reference"
            if _identity(capture) == target
            else "source_stated_identity_path",
        }
        for key, capture in sorted(captures.items())
        if _identity(capture) in reached
    ]
    return {
        "candidates": candidates,
        "paths": paths,
        "blocked_paths": blocked,
        "availability": "ambiguous"
        if len(candidates) > 1
        else "available"
        if candidates
        else "missing_prerequisite"
        if blocked
        else "context_not_supplied",
    }


def _link(explorer, role, target, support, *, location=None):
    label = f"{role.capitalize()} · {target}"
    if role == "source" and location:
        original, _ = explorer.access._resolve(location)
        fields = {
            "sequence.checksums": "reference sequence checksums",
            "sequence.primary": "reference primary sequence",
            "identifiers.uniprot": "reference UniProt identity",
            "sequence.length": "reference sequence length",
            "annotations.isoforms": "UniProt isoform declaration",
            "relationships.has_predicted_structure": "predicted model metadata",
        }
        if isinstance(original, dict) and original.get("field_path") in fields:
            label = f"Source · {fields[original['field_path']]} · {target}"
    resolution = (
        {
            "candidates": [
                {
                    "location": location,
                    "capture": explorer.access._focal_key,
                    "basis": "exact_retained_node",
                }
            ],
            "paths": [],
            "blocked_paths": [],
            "availability": "available",
        }
        if location
        else _resolve(explorer, target)
    )
    return {
        "role": role,
        "label": label,
        "target_ref": target,
        "support": deepcopy(support),
        "rule": RULE,
        **resolution,
    }


def _link_view(
    explorer, links, origin, title, *, source_location=None, status=None, rule=RULE
):
    view = explorer._metadata(
        {
            "rule": rule,
            "inputs": explorer.context["captures"],
            "focal": explorer.access._focal_key,
            "source_location": source_location,
            "links": links,
        },
        title,
        origin,
    )
    root = view._selection._target["location"]
    _, root = explorer.access._resolve(root)
    entries = tuple(
        _Entry(
            {
                **root,
                "segments": [
                    {"type": "Key", "value": "links"},
                    {"type": "Index", "value": i},
                ],
            },
            str(i),
            link,
        )
        for i, link in enumerate(links)
    )
    if rule in ("ligand_site_context_links@1", "quaternary_context_links@1"):
        explorer._session["views"].pop(id(view), None)
    return replace(
        view,
        _selection=replace(view._selection, _entries=entries),
        _selected=entries,
        _link_panel=True,
        _status=status or ("ok" if links else "empty"),
        _request=origin.request,
        _reason="Retained sources and an explicit local structural question; no source queries or identity merge."
        if rule == "retained_context_links@3"
        else "Retained sources and explicit destinations only; no source queries or identity merge.",
    )


def related(item):
    if item._view._record_panel == "quaternary_interpretation":
        from .card_quaternary_exploration import links

        return links(item)
    if item._view._field_panel == "quaternary_structure":
        from .card_quaternary_source_v1 import related as quaternary_related

        return quaternary_related(item)
    if item._view._record_panel == "ligand_site_comparisons":
        from .card_ligand_site_exploration import links

        return links(item)
    explorer = item._view._explorer
    # A catalog item's open() executes its explicit topic/question operation;
    # asking for links must not implicitly execute that scientific reader.
    origin = (
        explorer._inspect(
            item.payload_location, item._view, title=f"Retained entry · {item.label}"
        )
        if item._view._route_catalog or item._view._link_panel
        else item.open()
    )
    if item._view._link_panel:
        # Link details already contain their full retained basis. No recursive
        # resolution of link-metadata strings as new scientific entities.
        return _link_view(explorer, [], origin, "Related retained context")
    links = []
    support = item.support
    from .card_annotation_regions_v1 import annotation_path
    from .card_annotation_regions_v1 import link as annotation_link

    annotation = annotation_path(item.payload_location)
    question = None
    if annotation is not None:
        question = annotation_link(explorer, item.payload_location)
        support = question["support"]
    else:
        from .card_model_regions_v1 import link as model_link

        question = model_link(explorer, item.payload_location)
        if question is not None:
            support = question["support"]
    seen = set()
    for basis in support:
        for statement in [
            *basis.get("statements", basis.get("source_assertions", [])),
            *basis.get("derivation_input_statements", []),
        ]:
            ref = statement["id"]
            if ref in seen:
                continue
            seen.add(ref)
            if statement["state"] == "present":
                links.append(
                    _link(
                        explorer, "source", ref, [basis], location=statement["location"]
                    )
                )
            else:
                links.append(
                    {
                        "role": "source",
                        "label": f"Source · {ref}",
                        "target_ref": ref,
                        "support": [deepcopy(basis)],
                        "rule": RULE,
                        "candidates": [],
                        "paths": [],
                        "blocked_paths": [],
                        "availability": "missing_prerequisite",
                    }
                )
    location = item.payload_location
    relationship = None
    if item._view._selection._scientific is not None:
        relationship = next(
            (
                row
                for row in explorer.access._focal.data["relationship_store"]
                if row["id"] == item._entry.key
            ),
            None,
        )
    elif location["kind"] == "card":
        segments = location["segments"]
        if (
            len(segments) >= 2
            and segments[0] == {"type": "Key", "value": "relationship_store"}
            and segments[1]["type"] == "Record"
        ):
            relationship = explorer.access._resolve(
                {**location, "segments": segments[:2]}
            )[0]
    if (
        location["kind"] == "card"
        and len(location["segments"]) == 2
        and location["segments"][0] == {"type": "Key", "value": "entities"}
    ):
        links.append(
            _link(explorer, "entity", location["segments"][1]["value"], support)
        )
    if relationship:
        for role in ("subject", "object"):
            links.append(_link(explorer, role, relationship[f"{role}_ref"], support))
    # An assertion's subject is a declared reference. Its arbitrary asserted value,
    # a field's text and generic extensions are deliberately not join instructions.
    if (
        location["kind"] == "card"
        and len(location["segments"]) >= 2
        and location["segments"][0]
        == {"type": "Key", "value": "source_assertion_store"}
    ):
        record = explorer.access._resolve(
            {**location, "segments": location["segments"][:2]}
        )[0]
        if isinstance(record.get("subject_ref"), str):
            links.append(_link(explorer, "subject", record["subject_ref"], support))
    rule = RULE
    if question is not None:
        rule = question["rule"]
        links = [{**row, "rule": rule} for row in links]
        links.append(question)
    return _link_view(
        explorer,
        links,
        origin,
        f"Related to {item.label}",
        source_location=location,
        rule=rule,
    )


def _destination(explorer, candidate, origin):
    from .card_exploration import CardExplorer

    destination = object.__new__(CardExplorer)
    destination._access = explorer.access._for_capture(candidate["capture"])
    destination._coverage_result = None
    destination._origin = origin
    destination._navigation_cache = explorer._navigation_cache
    destination._session = explorer._session
    location = candidate["location"]
    return (
        destination._inspect(location, origin, title="Referenced source record")
        if location["segments"]
        else destination.overview()
    )


def follow(item):
    explorer, link = item._view._explorer, item._entry.value
    if link.get("role") == "question" and link.get("rule") in (
        "retained_context_links@3",
        "retained_context_links@4",
    ):
        key = (
            "model_context"
            if link["rule"] == "retained_context_links@4"
            else "annotation_context"
        )
        basis = link[key]
        if basis["state"] == "ready":
            request = basis["request"]
            return explorer._answer(request["question"], request["options"], item._view)
        from .card_exploration import CardView

        selection = explorer.access.read(
            explorer.access._object_location({key: basis, "link": link})
        )
        return CardView(
            explorer,
            selection,
            selection._entries,
            "Model structural context unavailable"
            if key == "model_context"
            else "Annotation structural context unavailable",
            item._view,
            _status=basis["state"],
            _reason=basis["reason"],
        )
    candidates = link["candidates"]
    if len(candidates) == 1:
        return _destination(explorer, candidates[0], item._view)
    if len(candidates) > 1:
        choices = []
        for candidate in candidates:
            capture = explorer.access._captures[candidate["capture"]]
            choices.append(
                {
                    **deepcopy(link),
                    "role": "candidate",
                    "label": f"Captured destination · {_identity(capture)} · {capture.snapshot[:23]}",
                    "target_ref": capture.pin or capture.snapshot,
                    "availability": "available",
                    "candidates": [candidate],
                }
            )
        return _link_view(
            explorer,
            choices,
            item._view,
            "Choose a captured destination",
            status="ambiguous",
        )
    # Preserve useful local glossary/relationship support without synthesizing a
    # destination Card. Its public explorer and focal identity are explicitly null.
    entity = explorer.access._focal.data.get("entities", {}).get(link["target_ref"])
    view = explorer._metadata(
        {"subject_ref": link["target_ref"], "entity": entity, "link": link},
        "Retained destination context",
        item._view,
    )
    contributors = {explorer.access._focal_key}
    for path in [*link["paths"], *link["blocked_paths"]]:
        location = path["location"]
        contributors.add(location["card_ref"] or location["snapshot_id"])
    return replace(
        view,
        _status=link["availability"],
        _reason="Destination Card not supplied or its identity support is unavailable. Pass it explicitly through related_cards to explore its fields.",
        _context_only=True,
        _context_override={
            "card_ref": None,
            "snapshot_id": None,
            "subject_ref": link["target_ref"],
            "profile": None,
            "mode": "live",
            "adapter": link["rule"],
            "contributing_captures": sorted(contributors),
            "captures": explorer.context["captures"],
        },
        _request=item._view.request,
    )
