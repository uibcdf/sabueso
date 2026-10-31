"""Original exploration @6 predicates; formats @1-@5 retain their own verifier.

Inherited from original @5 at 9aa6d68; adds exact structure assembly navigation.
Expected findings never replace stored output.
"""

from copy import deepcopy
from dataclasses import replace

from .card_access import _handle
from .card_exploration_assembly import (
    is_explanation as is_assembly_explanation,
)
from .card_exploration_assembly import (
    is_view as is_assembly_view,
)
from .card_exploration_assembly import (
    verify_explanation as verify_assembly_explanation,
)
from .card_exploration_assembly import (
    verify_links as verify_assembly_links,
)
from .card_exploration_assembly import (
    verify_view as verify_assembly_view,
)
from .card_exploration_verification import (
    _historical_resolution,
    _verify_cell,
    _verify_display,
    equal,
    require,
)
from .card_exploration_verification import _verify_request as _original_request
from .errors import StorageError
from .snapshot import canonical_json, digest


def _verify_request(view, access):
    if is_assembly_explanation(view):
        return verify_assembly_explanation(view)
    return _original_request(view, access)


def verify_bundle(bundle, expected_digest):
    from .card_exploration_assembly import (
        ADAPTERS as ASSEMBLY_ADAPTERS,
    )
    from .card_exploration_quaternary import ADAPTERS as QUAT_ADAPTERS
    from .card_exploration_quaternary import FORMAT as QUAT_FORMAT
    from .card_exploration_quaternary import VERIFIER as QUAT_VERIFIER
    from .card_exploration_science import ADAPTERS
    from .card_exploration_science import FORMAT as SCIENCE_FORMAT
    from .card_exploration_science import VERIFIER as SCIENCE_VERIFIER
    from .card_exploration_sites import ADAPTERS as SITE_ADAPTERS
    from .card_exploration_sites import FORMAT as SITE_FORMAT
    from .card_exploration_sites import VERIFIER as SITE_VERIFIER
    from .card_exploration_storage import FORMAT, VERIFIER
    from .card_structure_context_v2 import (
        FORMAT as ASSEMBLY_FORMAT,
    )
    from .card_structure_context_v2 import (
        VERIFIER as ASSEMBLY_VERIFIER,
    )

    require(
        isinstance(bundle, dict)
        and bundle.get("format")
        in (FORMAT, SCIENCE_FORMAT, SITE_FORMAT, QUAT_FORMAT, ASSEMBLY_FORMAT),
        "Unsupported exploration format.",
    )
    names = {
        "format",
        "producer",
        "root_view_ref",
        "root_navigation_ref",
        "cards",
        "inputs",
        "objects",
        "locations",
        "views",
        "navigation",
        "capabilities",
        "presentation_metadata",
        "digests",
        "bundle_digest",
    }
    assembly = bundle["format"] == ASSEMBLY_FORMAT
    quaternary = bundle["format"] in (QUAT_FORMAT, ASSEMBLY_FORMAT)
    sites = bundle["format"] in (SITE_FORMAT, QUAT_FORMAT, ASSEMBLY_FORMAT)
    scientific = bundle["format"] in (
        SCIENCE_FORMAT,
        SITE_FORMAT,
        QUAT_FORMAT,
        ASSEMBLY_FORMAT,
    )
    if scientific:
        names.add("scientific_results")
    require(set(bundle) == names, "Missing or unsupported required bundle member.")
    require(
        bundle["producer"]["verifier"]
        == (
            ASSEMBLY_VERIFIER
            if assembly
            else QUAT_VERIFIER
            if quaternary
            else SITE_VERIFIER
            if sites
            else SCIENCE_VERIFIER
            if scientific
            else VERIFIER
        ),
        "The required historical verifier is unavailable.",
    )
    actual = digest(
        canonical_json(
            {key: value for key, value in bundle.items() if key != "bundle_digest"}
        )
    )
    require(
        actual == bundle["bundle_digest"]
        and (expected_digest is None or actual == expected_digest),
        "Exploration digest differs from its retained/expected binding.",
    )
    members = {
        key: digest(canonical_json(value))
        for key, value in bundle.items()
        if key not in ("digests", "bundle_digest")
    }
    require(members == bundle["digests"], "Exploration member digest differs.")
    require(
        bundle["capabilities"]["scientific_saved_adapters"]
        == list(
            ASSEMBLY_ADAPTERS
            if assembly
            else QUAT_ADAPTERS
            if quaternary
            else SITE_ADAPTERS
            if sites
            else ADAPTERS
        )
        if scientific
        else not bundle["capabilities"]["scientific_saved_adapters"],
        "Unsupported saved scientific adapter.",
    )
    for key, value in bundle["objects"].items():
        if (
            isinstance(value, dict)
            and "native_payload" in value
            and value.get("context", {}).get("adapter")
            == "assembly_generation_exploration@1"
        ):
            require(
                assembly and key in bundle["scientific_results"],
                "Assembly findings require their explicit original manifest.",
            )
        if (
            isinstance(value, dict)
            and "native_payload" in value
            and value.get("context", {}).get("adapter") == "quaternary_exploration@1"
        ):
            require(
                quaternary and key in bundle["scientific_results"],
                "A quaternary result needs its explicit original manifest.",
            )
        if (
            isinstance(value, dict)
            and "native_payload" in value
            and value.get("context", {}).get("adapter") == "ligand_site_exploration@1"
        ):
            require(
                sites and key in bundle["scientific_results"],
                "A site result is missing its explicit historical manifest.",
            )
        if scientific and key in bundle["scientific_results"]:
            continue
        require(
            key == _handle("XR_", {"adapter": "literal_metadata@1", "value": value}),
            "Retained metadata identity differs.",
        )


def _verify_links(view):
    if view.native_payload.get("rule") == "structure_declaration_context_links@2":
        from .card_structure_context_v2 import verify_links

        return verify_links(view)
    if view.native_payload.get("rule") == "assembly_generation_links@1":
        return verify_assembly_links(view)
    if view.native_payload.get("rule") == "structure_declaration_context_links@1":
        from .card_structure_context_v1 import verify_links

        return verify_links(view)
    if view.native_payload.get("rule") == "ligand_instance_context_links@1":
        from .card_ligand_instance_navigation_v1 import verify_links

        return verify_links(view)
    if view.native_payload.get("rule") == "quaternary_interpretation_links@1":
        from .card_exploration_quaternary import verify_links

        return verify_links(view)
    if view.native_payload.get("rule") == "quaternary_context_links@1":
        from .card_quaternary_source_v1 import verify_links

        return verify_links(view)
    if view.native_payload.get("rule") == "ligand_site_context_links@1":
        from .card_exploration_sites import verify_links

        return verify_links(view)
    payload, access = view.native_payload, view._explorer.access
    require(
        payload.get("rule")
        in (
            "retained_context_links@1",
            "retained_context_links@2",
            "retained_context_links@3",
            "retained_context_links@4",
        ),
        "Unsupported navigation rule.",
    )
    source = payload["source_location"]
    if source is None:
        if not payload["links"]:
            require(
                view._origin is not None
                and view._origin.native_payload.get("rule")
                in (
                    "retained_context_links@1",
                    "retained_context_links@2",
                    "retained_context_links@3",
                    "retained_context_links@4",
                    "ligand_site_context_links@1",
                    "quaternary_context_links@1",
                    "quaternary_interpretation_links@1",
                    "assembly_generation_links@1",
                    "ligand_instance_context_links@1",
                    "structure_declaration_context_links@1",
                    "structure_declaration_context_links@2",
                ),
                "Missing retained link-detail origin.",
            )
            return
        # Candidate rows explicitly select exactly one of a recorded parent's pins.
        require(
            view._origin is not None and view._origin._link_panel,
            "Missing candidate origin.",
        )
        parents = view._origin.native_payload["links"]
        for link in payload["links"]:
            require(
                link["role"] == "candidate" and len(link["candidates"]) == 1,
                "Invalid candidate choice.",
            )
            candidate = link["candidates"][0]
            require(
                any(
                    candidate in parent["candidates"]
                    and link["paths"] == parent["paths"]
                    and link["blocked_paths"] == parent["blocked_paths"]
                    for parent in parents
                ),
                "Candidate is not bound to its original ambiguity.",
            )
            capture = access._captures[candidate["capture"]]
            require(
                link["target_ref"] == (capture.pin or capture.snapshot),
                "Candidate target pin differs.",
            )
        return
    _, source = access._resolve(source)
    support = view._explorer._support(source)
    question = None
    if payload["rule"] == "retained_context_links@3":
        from .card_annotation_regions_v1 import link as original_annotation_link

        question = original_annotation_link(view._explorer, source)
        require(
            question is not None,
            "Annotation navigation has no original annotation location.",
        )
        support = question["support"]
    elif payload["rule"] == "retained_context_links@4":
        from .card_model_regions_v1 import link as original_model_link

        question = original_model_link(view._explorer, source)
        require(
            question is not None, "Model navigation has no original model location."
        )
        support = question["support"]
    relationship, statement = None, None
    segments = source["segments"]
    if (
        source["kind"] == "result"
        and len(segments) == 2
        and segments[0]["value"] == "items"
    ):
        wire = access._objects[source["result_ref"]]
        if wire.get("context", {}).get("adapter") == "structure_exploration@1":
            key = segments[1]["value"]
            support = [wire["support"][key]]
            relationship = next(
                (
                    row
                    for row in access._focal.data["relationship_store"]
                    if row["id"] == key
                ),
                None,
            )
    if (
        source["kind"] == "card"
        and len(segments) >= 2
        and segments[0]["value"] in ("relationship_store", "source_assertion_store")
    ):
        owner, _ = access._resolve({**source, "segments": segments[:2]})
        if segments[0]["value"] == "relationship_store":
            relationship = owner
        else:
            statement = owner
    expected_targets = []
    seen = set()

    def statements(basis):
        return [
            *basis.get("statements", basis.get("source_assertions", [])),
            *(
                basis.get("derivation_input_statements", [])
                if payload["rule"]
                in (
                    "retained_context_links@2",
                    "retained_context_links@3",
                    "retained_context_links@4",
                )
                else []
            ),
        ]

    for basis in support:
        for original in statements(basis):
            if original["id"] not in seen:
                expected_targets.append(("source", original["id"]))
                seen.add(original["id"])
    if (
        source["kind"] == "card"
        and len(segments) == 2
        and segments[0]["value"] == "entities"
    ):
        expected_targets.append(("entity", segments[1]["value"]))
    if relationship is not None:
        expected_targets.extend(
            (role, relationship[f"{role}_ref"]) for role in ("subject", "object")
        )
    if statement is not None and isinstance(statement.get("subject_ref"), str):
        expected_targets.append(("subject", statement["subject_ref"]))
    if question is not None:
        expected_targets.append(("question", "region_coverage"))
    require(
        [(link["role"], link["target_ref"]) for link in payload["links"]]
        == expected_targets,
        "Retained link membership differs from original references.",
    )
    for link in payload["links"]:
        require(link["rule"] == payload["rule"], "Link rule differs.")
        role, target = link["role"], link["target_ref"]
        if role == "question":
            require(
                question is not None and equal(link, question),
                "Structural request differs from its original source/axis basis.",
            )
            continue
        if role == "source":
            original = [
                record
                for basis in support
                for record in statements(basis)
                if record["id"] == target
            ]
            require(len(original) == 1, "Source link is not original support.")
            basis = original[0]
            require(link["support"] == support, "Source link support differs.")
            if basis["state"] == "present":
                expected = {
                    "candidates": [
                        {
                            "location": basis["location"],
                            "capture": access._focal_key,
                            "basis": "exact_retained_node",
                        }
                    ],
                    "paths": [],
                    "blocked_paths": [],
                    "availability": "available",
                }
            else:
                expected = {
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                    "availability": "missing_prerequisite",
                }
        else:
            if role in ("subject", "object"):
                require(
                    relationship is not None
                    or (role == "subject" and statement is not None),
                    "Endpoint has no original record.",
                )
                record = relationship or statement
                require(
                    record[f"{role}_ref"] == target,
                    "Endpoint target differs from its original record.",
                )
            elif role == "entity":
                require(
                    source["kind"] == "card"
                    and len(segments) == 2
                    and segments[0]["value"] == "entities"
                    and segments[1]["value"] == target,
                    "Glossary target differs.",
                )
            else:
                raise StorageError("Unsupported saved link role.")
            require(link["support"] == support, "Endpoint source basis differs.")
            expected = _historical_resolution(access, target)
        require(
            all(equal(link[key], value) for key, value in expected.items()),
            "Recorded destination/identity decision differs from its captured basis.",
        )


def _verify_state(view, record, native, access):
    from .card_exploration import CardItem
    from .card_exploration_quaternary import is_explanation as is_quaternary_explanation
    from .card_exploration_sites import is_explanation as is_site_explanation

    def is_explanation(value):
        return (
            is_site_explanation(value)
            or is_quaternary_explanation(value)
            or is_assembly_explanation(value)
        )

    from .card_exploration_storage import _cell_record

    state = record["state"]
    if view._context_only:
        anchor = view
        while anchor._origin is not None and anchor._origin._context_only:
            anchor = anchor._origin
        anchor_payload = anchor.native_payload
        require(
            anchor._origin is not None and anchor._origin._link_panel,
            "Missing retained destination origin.",
        )
        require(
            anchor_payload["link"] in anchor._origin.native_payload["links"],
            "Context-only link differs from its originating result.",
        )
        require(
            state["context"]["card_ref"] is None
            and state["context"]["snapshot_id"] is None
            and state["context"]["subject_ref"]
            == anchor_payload["subject_ref"]
            == anchor_payload["link"]["target_ref"],
            "Context-only destination acquired a false focal identity.",
        )
        require(
            equal(
                anchor_payload["entity"],
                access._focal.data.get("entities", {}).get(
                    anchor_payload["subject_ref"]
                ),
            ),
            "Retained glossary context differs.",
        )
    else:
        require(
            state["context"]["card_ref"] == access._focal.pin
            and state["context"]["snapshot_id"] == access._focal.snapshot,
            "View focal capture differs.",
        )
    expected_adapter = (
        anchor_payload["link"]["rule"]
        if view._context_only
        else native["rule"]
        if view._link_panel
        else "structure_exploration@1"
        if view._selection._scientific is not None
        else "knowledge_coverage_exploration@1"
        if view._record_panel == "coverage"
        else "disease_classification_fields@1"
        if view._record_panel == "classification"
        else "protein_function_fields@1"
        if view._field_panel == "function"
        else f"{view._field_panel}_fields@1"
        if view._field_panel
        else "literal_human@1"
    )
    require(
        state["context"]["adapter"] == expected_adapter,
        "The required saved adapter version is unavailable or misbound.",
    )
    if view._context_only:
        require(
            state["context"]["profile"] is None,
            "Context-only destination acquired an invented profile.",
        )
    plain = replace(view, _saved_state=None)
    for key, value in plain.context.items():
        if key != "mode":
            require(
                key in state["context"] and equal(state["context"][key], value),
                "Saved adapter/input context differs from its capture binding.",
            )
    require(
        equal(state["context"]["captures"], sorted(access._captures)),
        "Saved contributing capture registry differs.",
    )
    if view._field_panel or (
        view._record_panel and view._selection._scientific is None
    ):
        require(
            native["context"]["card_ref"] == access._focal.pin
            and native["context"]["snapshot_id"] == access._focal.snapshot,
            "Native field/relationship context differs.",
        )
    require(
        equal(state["schema"], plain.schema),
        "Saved column/quantity schema differs from its adapter.",
    )
    require(
        equal(state["coverage"], plain.coverage),
        "Saved coverage claims differ from their literal scope.",
    )
    require(
        set(state["items"])
        == {CardItem(view, entry).item_ref for entry in view._selection._entries},
        "Saved item closure differs.",
    )
    for entry in view._selection._entries:
        original, owned = access._resolve(entry.location)
        if owned["kind"] == "card":
            require(
                owned["card_ref"] == access._focal.pin
                and owned["snapshot_id"] == access._focal.snapshot,
                "Saved entry belongs to a different focal capture.",
            )
        require(
            equal(entry.value, original),
            "Saved entry value differs from its original captured location.",
        )
        segments = owned["segments"]
        if view._selection._scientific is not None:
            expected_key, expected_ordinal = segments[-1]["value"], None
        elif owned == access._resolve(view._selection._target["location"])[
            1
        ] and not isinstance(original, (dict, list)):
            expected_key, expected_ordinal = None, None
        elif view._field_panel == "annotated_regions":
            from .card_annotation_regions_v1 import annotation_path

            path = annotation_path(owned)
            require(
                path is not None,
                "Saved annotation has no original typed annotation location.",
            )
            expected_key, expected_ordinal = (
                f"features_positional.{path[0]}[{path[1]}]",
                path[1],
            )
        elif (
            view._field_panel
            and owned["kind"] == "card"
            and segments[0]["value"] == "sections"
        ):
            expected_key, expected_ordinal = (
                ".".join(
                    segment["value"]
                    for segment in segments[1:]
                    if segment["type"] == "Key"
                ),
                None,
            )
        elif view._field_panel == "quaternary_structure":
            if len(segments) == 2 and segments[1]["type"] == "Record":
                expected_key, expected_ordinal = segments[1]["value"], None
            else:
                require(
                    owned["kind"] == "card"
                    and len(segments) == 5
                    and [s["type"] for s in segments]
                    == ["Key", "Record", "Key", "Key", "Index"]
                    and [segments[i]["value"] for i in (0, 2, 3)]
                    == ["relationship_store", "qualifiers", "assemblies"]
                    and type(segments[4]["value"]) is int,
                    "Saved assembly is not an original typed assembly record.",
                )
                expected_key, expected_ordinal = (
                    f"{segments[1]['value']}:assembly:{segments[4]['value']}",
                    segments[4]["value"],
                )
        elif view._field_panel == "ligand_instances":
            require(
                owned["kind"] == "card"
                and len(segments) == 7
                and [segment["type"] for segment in segments]
                == ["Key", "Record", "Key", "Key", "Index", "Key", "Index"]
                and [segments[index]["value"] for index in (0, 2, 3, 5)]
                == ["relationship_store", "qualifiers", "ligands", "instances"],
                "Saved ligand instance is not bound to an original typed instance location.",
            )
            expected_key = (
                f"{segments[1]['value']}:{segments[4]['value']}:{segments[6]['value']}"
            )
            expected_ordinal = segments[6]["value"]
        elif view._link_panel:
            expected_key, expected_ordinal = str(segments[-1]["value"]), None
        elif segments and segments[-1]["type"] == "Record":
            expected_key = segments[-1]["value"]
            from .card_exploration_labels import structural_explanation

            direct_explanation = (
                isinstance(native, dict)
                and (
                    native.get("basis") == "stored_literal"
                    or structural_explanation(view) is not None
                    or is_explanation(view)
                )
                and segments[0]["value"] == "source_assertion_store"
            )
            if direct_explanation:
                expected_ordinal = None
            else:
                store = access._resolve({**owned, "segments": segments[:-1]})[0]
                expected_ordinal = next(
                    index
                    for index, row in enumerate(store)
                    if row["id"] == expected_key
                )
        elif segments:
            expected_key = segments[-1]["value"]
            expected_ordinal = expected_key if segments[-1]["type"] == "Index" else None
        else:
            expected_key, expected_ordinal = None, None
        require(
            equal(entry.key, expected_key) and equal(entry.ordinal, expected_ordinal),
            "Saved literal key/original ordinal differs from its typed location.",
        )
        item = CardItem(plain, entry)
        frozen = state["items"][item.item_ref]
        require(
            isinstance(frozen["label"], str)
            and set(frozen) == {"label", "kind", "support", "cells"},
            "Unsupported saved item presentation shape.",
        )
        require(
            frozen["kind"] == item.kind and equal(frozen["support"], item.support),
            "Saved item kind/support differs from its original binding.",
        )
        cells = item.cells
        require(set(cells) == set(frozen["cells"]), "Saved cell membership differs.")
        for column, cell in cells.items():
            expected = _cell_record(item, column, cell)
            # JSON comparison only reads nested values. Keep the independent
            # conversion copy for quantities and detach the top-level edits.
            actual = frozen["cells"][column]
            require(isinstance(actual, dict), "Saved cell must be an object.")
            actual = dict(actual)
            if expected["encoding"] == actual.get("encoding") == "quantity_record":
                actual = deepcopy(actual)
            if column == "label":
                expected["value"] = frozen["label"]
            # Wording is recorded presentation metadata; value, type, state,
            # units and support are independently checked against the capture.
            expected.pop("reason", None)
            actual.pop("reason", None)
            _verify_cell(actual, expected)


def _verify_profile(view, native, access):
    from .card_exploration_adapter_v1 import _v1_region_request

    if (
        view._origin is not None
        and view._origin._link_panel
        and view._origin.native_payload.get("rule")
        in ("retained_context_links@3", "retained_context_links@4")
    ):
        key = (
            "model_context"
            if view._origin.native_payload["rule"] == "retained_context_links@4"
            else "annotation_context"
        )
        questions = [
            item._entry.value
            for item in view._origin.items()
            if item._entry.value.get("role") == "question"
        ]
        if view._selection._scientific is not None:
            require(
                len(questions) == 1 and questions[0][key]["state"] == "ready",
                "Structural annotation destination lost its original question.",
            )
            request = questions[0][key]["request"]
            effective, status, _ = _v1_region_request(
                view._explorer, request["options"]
            )
            require(
                status == "ok"
                and equal(
                    view._selection._scientific.options,
                    {
                        key: value
                        for key, value in effective.items()
                        if key != "sequence_ref"
                    },
                )
                and (
                    view.request is None
                    or equal(
                        view.request,
                        {
                            "question": request["question"],
                            "topic": "structures",
                            "options": effective,
                        },
                    )
                ),
                "Structural destination differs from its originating annotation question.",
            )
        elif isinstance(native, dict) and key in native and "link" in native:
            require(
                native["link"] in questions and equal(native[key], native["link"][key]),
                "Unavailable annotation context lost its original question.",
            )
            basis = native[key]
            require(
                basis["state"] != "ready"
                and view._status == basis["state"]
                and view._reason == basis["reason"],
                "Unavailable annotation outcome differs from its recorded basis.",
            )

    if (
        view._request is not None
        and view._request.get("question") == "region_coverage"
        and view._selection._scientific is not None
    ):
        effective, status, _ = _v1_region_request(
            view._explorer, view._request["options"]
        )
        require(
            status == "ok"
            and view._request
            == {
                "question": "region_coverage",
                "topic": "structures",
                "options": effective,
            }
            and view._selection._scientific.options
            == {
                key: value for key, value in effective.items() if key != "sequence_ref"
            },
            "Saved canonical region request differs from its original scope.",
        )
    if (
        isinstance(native, dict)
        and native.get("question") == "region_coverage"
        and access._resolve(view._selection._target["location"])[1]["kind"] == "result"
    ):
        effective, status, reason = _v1_region_request(
            view._explorer, native["options"]
        )
        require(
            status != "ok"
            and equal(
                native,
                {
                    "question": "region_coverage",
                    "options": effective,
                    "outcome": {"status": status, "reason": reason},
                },
            ),
            "Saved region prerequisite decision differs.",
        )
        if view.request is not None:
            require(
                view.request
                == {
                    "question": "region_coverage",
                    "topic": "structures",
                    "options": effective,
                },
                "Saved region prerequisite request differs.",
            )
    if view._record_panel == "coverage":
        rows = native.get("native_payload", {}).get("rows", [])
        require(
            equal([entry.value for entry in view._selection._entries], rows),
            "Saved source/area row membership differs.",
        )
    if view._field_panel:
        from .card_annotation_regions_v1 import entries as annotation_entries
        from .card_exploration_profiles import PANELS, field_entries
        from .card_ligand_instances_v1 import entries as instance_entries
        from .card_protein_source_v1 import TOPICS, entries
        from .card_quaternary_source_v1 import entries as quaternary_entries

        if view._field_panel == "quaternary_structure":
            from .card_quaternary_source_v1 import SCOPE

            require(
                native.get("adapter") == "quaternary_structure_fields@1"
                and native.get("scope") == SCOPE,
                "Original quaternary adapter/scope differs.",
            )

        expected_entries, gaps = (
            (
                quaternary_entries(view._explorer)
                if view._field_panel == "quaternary_structure"
                else annotation_entries(view._explorer)
                if view._field_panel == "annotated_regions"
                else instance_entries(view._explorer)
                if view._field_panel == "ligand_instances"
                else entries(view._explorer, view._field_panel)
                if view._field_panel in TOPICS
                else field_entries(view._explorer, view._field_panel)
            )
            if access.profile == PANELS[view._field_panel][0]
            else ((), [])
        )
        require(
            equal(
                [entry.location for entry in view._selection._entries],
                [entry.location for entry in expected_entries],
            )
            and equal(native["field_gaps"], gaps),
            "Saved field membership/gaps differ from retained fields.",
        )
        require(
            equal(
                native["fields"],
                {entry.key: entry.value for entry in view._selection._entries},
            ),
            "Field presentation differs from original fields.",
        )
    if view._record_panel == "classification":
        identity = access._focal.data["meta"].get("card_id", "")
        subject = (
            identity.removeprefix("sabueso:disease:")
            if identity.startswith("sabueso:disease:")
            else None
        )
        expected = (
            [
                row
                for row in access._focal.data["relationship_store"]
                if row["predicate"] == "subclass_of" and row["subject_ref"] == subject
            ]
            if access.profile == "disease" and subject
            else []
        )
        expected = sorted(expected, key=lambda row: row["id"])
        require(
            equal(native["relationships"], expected),
            "Saved hierarchy membership differs from original relationships.",
        )
    if view._link_panel:
        _verify_links(view)


def _verify_support(bundle, nodes):
    from .card_exploration import CardItem
    from .card_exploration_history import _require_matches
    from .card_exploration_storage import operation_key, required_views

    root = nodes[bundle["root_navigation_ref"]]
    for view in required_views(root):
        for entry in view._selection._entries:
            binding = operation_key(CardItem(view, entry))
            require(
                all(
                    binding in bundle["navigation"][kind]
                    for kind in ("explanations", "links")
                ),
                "Required original explanation/link closure is missing.",
            )
    require(
        bundle["capabilities"]["root_machine_selection_ref"] == root._machine_ref,
        "Machine entry selection binding differs.",
    )
    if root._machine_ref is not None:
        require(
            root._machine_ref == root._selection.selection_ref,
            "Root machine selection is not the retained exact request.",
        )
    sources = {}
    for view in nodes.values():
        for entry in view._selection._entries:
            item = CardItem(view, entry)
            sources.setdefault((view._explorer.access._focal_key, item.item_ref), item)
    for operation, mappings in bundle["navigation"].items():
        for binding, key in mappings.items():
            focal, item_ref = __import__("json").loads(binding)
            source = sources.get((focal, item_ref))
            require(source is not None, "Saved support references a foreign item.")
            native = nodes[key].native_payload
            if operation == "links":
                require(
                    equal(
                        native.get("source_location"),
                        None if source._view._link_panel else source.payload_location,
                    ),
                    "Original related links belong to a different originating item.",
                )
            if operation == "explanations":
                if source._view._record_panel in (
                    "ligand_site_comparisons",
                    "quaternary_interpretation",
                    "assembly_generation",
                ):
                    wire = source._view._explorer.access._objects[
                        source._view.result_ref
                    ]
                    _require_matches(
                        native,
                        wire["explanations"][source._entry.key],
                        "site explanation actual item origin",
                    )
                elif source._view._selection._scientific is not None:
                    from .card_exploration_science import _encode

                    require(
                        equal(
                            _encode(native, "structure_explanation"),
                            _encode(
                                source._view._selection._scientific.explanations[
                                    source._entry.key
                                ],
                                "structure_explanation",
                            ),
                        ),
                        "Structural explanation belongs to a different original item.",
                    )
                if source._view._record_panel == "coverage":
                    params = native["rule"]["parameters"]
                    require(
                        params
                        == {
                            "knowledge_area": source._entry.value["area"],
                            "knowledge_source": source._entry.value["source"],
                        },
                        "Coverage explanation belongs to a different original row.",
                    )
                require(
                    native.get("basis") in ("stored_literal", None),
                    "Unsupported scientific explanation.",
                )
                if "support" in native:
                    require(
                        equal(native["support"], source.support),
                        "Explanation support differs from the original item.",
                    )
                if "stored_conflicts" in native:
                    require(
                        equal(native["stored_conflicts"], source._conflicts),
                        "Explanation conflict context differs.",
                    )
                if source._view._field_panel:
                    from .card_exploration_profiles import alternatives

                    for name, value in alternatives(
                        source._view._explorer, source._entry
                    ).items():
                        require(
                            name in native and equal(native[name], value),
                            "Explanation selected/alternative source context differs.",
                        )
                if source._view._link_panel:
                    require(
                        equal(native.get("link"), source._entry.value),
                        "Original link explanation differs.",
                    )
                if "selection_rules" in native:
                    require(
                        equal(
                            native["selection_rules"],
                            source._view._explorer.access._focal.data.get(
                                "selection_rules", {}
                            ),
                        ),
                        "Explanation selection rules differ.",
                    )


def verify_views(bundle, nodes):
    from .card_exploration_storage import admitted_view

    for key, view in nodes.items():
        record, access = bundle["views"][key], view._explorer.access
        from .card_structure_context_v2 import verify_destination

        verify_destination(view)
        from .card_exploration_quaternary import is_view as is_quaternary_view
        from .card_exploration_quaternary import verify_view as verify_quaternary_view
        from .card_exploration_sites import FORMAT as SITE_FORMAT
        from .card_exploration_sites import is_view, verify_view

        if is_assembly_view(view):
            require(
                bundle["format"] == "sabueso.card_exploration@6",
                "Assembly findings in this verifier need original format @6.",
            )
            require(
                view.result_ref in bundle["scientific_results"]
                and bundle["scientific_results"][view.result_ref]["focal"]
                == record["focal"],
                "Assembly result has no original focal manifest.",
            )
            verify_assembly_view(view, record)
            continue
        if is_quaternary_view(view):
            require(
                bundle["format"]
                in ("sabueso.card_exploration@4", "sabueso.card_exploration@6"),
                "Quaternary interpretation requires its original saved format.",
            )
            require(
                view.result_ref in bundle["scientific_results"]
                and bundle["scientific_results"][view.result_ref]["focal"]
                == record["focal"],
                "Quaternary result has no manifest or has a foreign capture.",
            )
            verify_quaternary_view(view, record)
            continue
        if is_view(view):
            require(
                bundle["format"]
                in (
                    SITE_FORMAT,
                    "sabueso.card_exploration@4",
                    "sabueso.card_exploration@6",
                ),
                "Site comparison requires its explicit saved format.",
            )
            require(
                view.result_ref in bundle["scientific_results"]
                and bundle["scientific_results"][view.result_ref]["focal"]
                == record["focal"],
                "Site view has no original scientific manifest or has a foreign focal capture.",
            )
            verify_view(view, record)
            continue
        from .card_exploration_science import _encode_view_payload, _encoding

        require(
            record.get("native_encoding", "json") == _encoding(view)
            and equal(record["native_payload"], _encode_view_payload(view)),
            "Saved native payload/quantity encoding differs.",
        )
        require(
            admitted_view(view),
            "A required scientific historical verifier is unavailable.",
        )
        require(
            view._field_panel
            in (
                None,
                "function",
                "chemistry",
                "properties",
                "definition",
                "identity",
                "sequence",
                "predicted_structures",
                "sites",
                "ligand_instances",
                "annotated_regions",
                "quaternary_structure",
            )
            and view._record_panel in (None, "classification", "coverage"),
            "Unsupported saved profile adapter.",
        )
        native = _verify_request(view, access)
        _verify_state(view, record, native, access)
        _verify_display(view, record)
        _verify_profile(view, native, access)
    _verify_support(bundle, nodes)
