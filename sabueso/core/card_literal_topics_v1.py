"""Named literal molecule routes over an already captured Card (#148)."""

ADAPTER = "molecule_literal_topics@1"


def _route(access, label, path, expected):
    node = access._focal.data
    segments = []
    route = {
        "label": label,
        "state": "not_retained",
        "location": None,
        "container_location": None,
    }
    for key in path:
        if not isinstance(node, dict):
            route.update(
                state="unrecognized_container",
                container_location=access._card_location(segments=segments),
            )
            return route
        if key not in node:
            return route
        node = node[key]
        segments.append({"type": "Key", "value": key})
    route["location"] = access._card_location(segments=segments)
    route["state"] = (
        "retained_null"
        if node is None
        else "unrecognized_shape"
        if not isinstance(node, expected)
        else "retained_empty"
        if not node
        else "retained"
    )
    return route


def descriptors(access):
    """Expose locations, never inferred identities, methods or source coverage."""
    if access.profile != "small_molecule":
        return {}
    topics = {
        "chemical_identity": {
            "label": "Chemical identity",
            "scope": (
                "Original identifiers, names and all stored relationships. Inspect each "
                "relationship's predicate, endpoints and support; no identity merge, "
                "stereochemical completeness or physical charge is inferred."
            ),
            "routes": {
                "identifiers": _route(
                    access, "Identifiers", ("sections", "identifiers"), dict
                ),
                "names": _route(access, "Names", ("sections", "names"), dict),
                "relationships": _route(
                    access, "Original relationships", ("relationship_store",), list
                ),
            },
        },
        "property_context": {
            "label": "Physicochemical properties",
            "scope": (
                "Complete original property fields with their units and source references. "
                "Read the referenced assertions for field-scoped methods; no calculation "
                "or measured/calculated determination is inferred."
            ),
            "routes": {
                "properties": _route(
                    access,
                    "Physicochemical properties",
                    ("sections", "properties", "physchem"),
                    dict,
                )
            },
        },
    }
    for key, topic in topics.items():
        topic.update(
            key=key,
            adapter=ADAPTER,
            scientific_adapter=False,
            operations=["read"],
            source_assertions=_route(
                access,
                "All original source assertions",
                ("source_assertion_store",),
                list,
            ),
            selection_rules=_route(
                access, "Original selection rules", ("selection_rules",), dict
            ),
            quality=_route(access, "Original quality records", ("quality",), dict),
        )
    return topics
