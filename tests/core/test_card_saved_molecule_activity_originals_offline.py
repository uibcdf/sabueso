"""Complete SDK205/SDK208 original file journeys over retained source values.

The writer reenacts the original operations with original retained facades.
It is not an original producer. Fresh receivers compare immutable observations;
no original expected payload is regenerated or rewritten.
"""

import importlib
import json
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_card_molecule_activity_history_offline import (
    ADAPTER,
    CASES,
    SUPPLEMENT_CASES,
    MultiFocalOriginal,
    Original,
    block_current,
    multifocal_original,
    original,
    retained_crossings,
    retained_keys,
)

from sabueso.core.card_access import AccessSelection, _Entry
from sabueso.core.card_exploration_storage import _access, _explorer
from sabueso.core.snapshot import canonical_json

# Literal original catalog meanings from SDK205 ddc1fc8, before clinical and B6
# routes. This retained writer is not a new LIVE producer or a source of oracles.
_ORIGINAL_CATALOGS = {
    "protein": {
        "nature_topics": (
            "function",
            "bioactivities",
            "structures",
            "sequence",
            "annotated_regions",
            "predicted_structures",
            "sites",
            "ligand_site_comparisons",
            "ligand_instances",
            "quaternary_structure",
            "quaternary_interpretation",
            "assembly_generation",
        ),
        "topics": {
            "function": (
                "Protein function",
                "Retained function, catalytic annotations and "
                "identity; no inferred function.",
            ),
            "bioactivities": (
                "Measured molecules and assay context",
                "Retained molecule, measurement-group and "
                "activity records with units, original "
                "assay/citation context and source support.",
            ),
            "structures": (
                "Experimental structures",
                "Existing inventory, original state rules and pinned support.",
            ),
            "sequence": (
                "Sequence and annotations",
                "Original sequence, units, checksums and source "
                "positional annotations.",
            ),
            "annotated_regions": (
                "Annotated regions and structural context",
                "Individual source annotations with "
                "their axes, original support and "
                "explicit structural questions.",
            ),
            "predicted_structures": (
                "Predicted models",
                "Source model versions, metrics, "
                "ranges and sequence context; "
                "separate from experiments.",
            ),
            "sites": (
                "Sites and contact statements",
                "Original functional-site fields and "
                "ligand/interface contacts with their numbering.",
            ),
            "ligand_site_comparisons": (
                "Ligand contacts and annotated-site comparisons",
                "Source-bound comparisons, partial "
                "findings and uncomputed "
                "coordinate context with original "
                "inputs.",
            ),
            "ligand_instances": (
                "Ligand instances in structures",
                "Original structure-local ligand "
                "instances, recorded chains and contact "
                "coordinates/distances.",
            ),
            "quaternary_structure": (
                "Subunits, assemblies and interfaces",
                "Original source declarations with "
                "structure-local assembly context, "
                "interface numbering and complete "
                "support.",
            ),
            "quaternary_interpretation": (
                "Interface classifications and family-site comparisons",
                "Source-bound interface findings "
                "and all family-site pairs, with "
                "original inputs and explicit "
                "uncomputed context.",
            ),
            "assembly_generation": (
                "Assembly components and operations",
                "Original assembly declarations, key "
                "binding and declared combination "
                "counts; physical copies and contacts "
                "remain uncomputed.",
            ),
            "literature": (
                "Publications and stored source links",
                "Original citations, ECO support, curated "
                "statements, mentions and source activity "
                "records, with complete publication context.",
            ),
            "sources": (
                "Source statements",
                "Original statements retained from sources.",
            ),
            "coverage": (
                "Knowledge coverage",
                "Original source/area knowledge states and their "
                "classification inputs.",
            ),
            "quality": (
                "Stored quality records",
                "Complete original quality, enrichment and selection records.",
            ),
            "content": ("Explore all content", "Complete retained Card content."),
        },
        "questions": {
            "function": {
                "label": "What do the sources state this protein does?",
                "topic": "function",
                "required_options": [],
                "scope": "Retained function and catalytic "
                "annotations, with original support.",
            },
            "region_coverage": {
                "label": "What do retained structures tell us about this region?",
                "topic": "structures",
                "required_options": ["sequence_ref", "region"],
                "scope": "Explicit canonical UniProt "
                "positions; sequence coverage "
                "alone does not establish "
                "coordinate completeness.",
            },
            "measured_molecules": {
                "label": "Which molecules have "
                "retained measurements, and "
                "what supports each result?",
                "topic": "bioactivities",
                "required_options": [],
                "scope": "Original molecule, "
                "measurement-group, "
                "activity-record and "
                "assay/citation context "
                "with units and support; "
                "concentration bands do not "
                "establish mechanism or "
                "efficacy.",
            },
            "assembly_generation": {
                "label": "Which components and "
                "operations are declared "
                "for each retained "
                "assembly?",
                "topic": "assembly_generation",
                "required_options": [],
                "scope": "Exact original generator "
                "contexts, key binding and "
                "declared combination "
                "counts; no physical copy, "
                "coordinate or contact "
                "inference.",
            },
            "quaternary_interpretation": {
                "label": "Which interface "
                "classifications and "
                "family-site "
                "comparisons are "
                "supported?",
                "topic": "quaternary_interpretation",
                "required_options": [],
                "scope": "All source-bound "
                "interface findings "
                "and individual "
                "family comparisons, "
                "including explicit "
                "uncertainty; no "
                "assembly geometry "
                "or biological "
                "relevance "
                "inferred.",
            },
            "quaternary_structure": {
                "label": "What do sources state "
                "about subunits, "
                "assemblies and "
                "interfaces?",
                "topic": "quaternary_structure",
                "required_options": [],
                "scope": "Original subunit field, "
                "structure-local assembly "
                "records and interface "
                "statements with exact "
                "support; source-declared "
                "contexts remain "
                "distinct.",
            },
            "ligand_site_comparisons": {
                "label": "Which retained ligand contacts overlap annotated sites?",
                "topic": "ligand_site_comparisons",
                "required_options": [],
                "scope": "Source-bound "
                "canonical comparisons "
                "with explicit "
                "unknowns; no atomic "
                "proximity, revision "
                "agreement or "
                "aggregate/instance "
                "merge.",
            },
            "annotated_regions": {
                "label": "Which individual annotations can I explore in structures?",
                "topic": "annotated_regions",
                "required_options": [],
                "scope": "Original annotations and "
                "exact source-supported "
                "canonical-region questions; "
                "unplaced and unsupported "
                "records stay visible.",
            },
            "structure_ligands": {
                "label": "Which ligand instances and "
                "contacts are declared in "
                "retained structures?",
                "topic": "ligand_instances",
                "required_options": [],
                "scope": "Original structure-local "
                "instances, recorded chains "
                "and contact "
                "coordinates/distances; no "
                "assembly or "
                "aggregated-contact join.",
            },
            "sequence_annotations": {
                "label": "Which sequence and positional annotations are retained?",
                "topic": "sequence",
                "required_options": [],
                "scope": "Original sequence fields "
                "and annotation "
                "locations; no coordinate "
                "projection or "
                "alignment.",
            },
            "predicted_models": {
                "label": "Which predicted models and "
                "source confidence metrics "
                "are retained?",
                "topic": "predicted_structures",
                "required_options": [],
                "scope": "Original model declarations, "
                "source metrics and recorded "
                "sequence/isoform context; "
                "separate from experimental "
                "structures.",
            },
            "retained_sites": {
                "label": "Which annotated sites and contact statements are retained?",
                "topic": "sites",
                "required_options": [],
                "scope": "Original active, binding and "
                "family-model sites plus "
                "ligand/interface contact "
                "statements; no new overlap or "
                "proximity calculation.",
            },
            "publications": {
                "label": "Which publications and original source links are retained?",
                "topic": "literature",
                "required_options": [],
                "scope": "Original citations, ECO support, "
                "curated statements, mentions and "
                "activity records; publication "
                "links are not project "
                "Evidence.",
            },
        },
    },
    "small_molecule": {
        "nature_topics": (
            "chemistry",
            "properties",
            "classification",
            "activity_context",
        ),
        "topics": {
            "chemistry": (
                "Chemical identity",
                "Retained chemical representations and source-stated identity links.",
            ),
            "properties": (
                "Physicochemical properties",
                "Stored values, units, source methods and alternatives.",
            ),
            "classification": (
                "Chemical classes and source-stated roles",
                "Retained classes, direct/inherited "
                "roles and original source support; "
                "no therapeutic inference.",
            ),
            "activity_context": (
                "Targets, measurements and assay context",
                "Exact molecule identity joins "
                "into explicitly supplied target "
                "captures, preserving original "
                "measurements and source/query "
                "scope.",
            ),
            "literature": (
                "Publications and stored source links",
                "Original citations, ECO support, "
                "curated statements, mentions and source "
                "activity records, with complete "
                "publication context.",
            ),
            "sources": (
                "Source statements",
                "Original statements retained from sources.",
            ),
            "coverage": (
                "Knowledge coverage",
                "Original source/area knowledge states and "
                "their classification inputs.",
            ),
            "quality": (
                "Stored quality records",
                "Complete original quality, enrichment and selection records.",
            ),
            "content": ("Explore all content", "Complete retained Card content."),
        },
        "questions": {
            "measured_targets": {
                "label": "Which supplied target "
                "contexts retain "
                "measurements for this "
                "exact molecule?",
                "topic": "activity_context",
                "required_options": [],
                "scope": "Explicit source "
                "identity edges and "
                "captured target pins; "
                "no target search, "
                "implicit identity "
                "merge or "
                "inactivity/efficacy "
                "inference.",
            },
            "chemical_identity": {
                "label": "Which chemical entity do these records describe?",
                "topic": "chemistry",
                "required_options": [],
                "scope": "Retained "
                "identifiers, "
                "representations and "
                "source-stated "
                "identity links; no "
                "computed chemistry.",
            },
            "property_context": {
                "label": "What properties are retained, and on what source basis?",
                "topic": "properties",
                "required_options": [],
                "scope": "Stored values, units, "
                "source methods and "
                "original "
                "alternatives.",
            },
            "classification": {
                "label": "Which chemical classes and source-stated roles are retained?",
                "topic": "classification",
                "required_options": [],
                "scope": "Original chemical "
                "classes, "
                "direct/inherited roles "
                "and exact source "
                "support; no target "
                "activity or therapeutic "
                "inference.",
            },
            "publications": {
                "label": "Which publications and original source links are retained?",
                "topic": "literature",
                "required_options": [],
                "scope": "Original citations, ECO "
                "support, curated "
                "statements, mentions and "
                "activity records; "
                "publication links are not "
                "project Evidence.",
            },
        },
    },
    "disease": {
        "nature_topics": ("definition", "classification", "identity"),
        "topics": {
            "definition": (
                "Disease definition",
                "Ontology definition, scoped synonyms and retained term metadata.",
            ),
            "classification": (
                "Disease classification",
                "Retained parent relationships; identity terminology is separate.",
            ),
            "identity": (
                "Identity terminology",
                "Equivalent identifiers and related xrefs, explicitly separated.",
            ),
            "literature": (
                "Publications and stored source links",
                "Original citations, ECO support, curated "
                "statements, mentions and source activity "
                "records, with complete publication context.",
            ),
            "sources": (
                "Source statements",
                "Original statements retained from sources.",
            ),
            "coverage": (
                "Knowledge coverage",
                "Original source/area knowledge states and their "
                "classification inputs.",
            ),
            "quality": (
                "Stored quality records",
                "Complete original quality, enrichment and selection records.",
            ),
            "content": ("Explore all content", "Complete retained Card content."),
        },
        "questions": {
            "meaning": {
                "label": "What does this disease term mean?",
                "topic": "definition",
                "required_options": [],
                "scope": "Ontology definition, scoped synonyms "
                "and retained term metadata; not a "
                "diagnosis.",
            },
            "classification": {
                "label": "Which broader terms are stated?",
                "topic": "classification",
                "required_options": [],
                "scope": "Retained parent relationships; "
                "equivalent and related "
                "identifiers have a separate "
                "identity route.",
            },
            "publications": {
                "label": "Which publications and original source links are retained?",
                "topic": "literature",
                "required_options": [],
                "scope": "Original citations, ECO support, "
                "curated statements, mentions and "
                "activity records; publication "
                "links are not project "
                "Evidence.",
            },
        },
    },
    "unknown": {
        "nature_topics": (),
        "topics": {
            "literature": (
                "Publications and stored source links",
                "Original citations, ECO support, curated "
                "statements, mentions and source activity "
                "records, with complete publication context.",
            ),
            "sources": (
                "Source statements",
                "Original statements retained from sources.",
            ),
            "coverage": (
                "Coverage and quality records",
                "Original stored quality records; source "
                "knowledge coverage is not evaluated.",
            ),
            "content": ("Explore all content", "Complete retained Card content."),
        },
        "questions": {
            "publications": {
                "label": "Which publications and original source links are retained?",
                "topic": "literature",
                "required_options": [],
                "scope": "Original citations, ECO support, "
                "curated statements, mentions and "
                "activity records; publication "
                "links are not project "
                "Evidence.",
            }
        },
    },
}


@pytest.fixture(scope="module")
def sdk205_original(tmp_path_factory, request):
    generator = original.__wrapped__(tmp_path_factory, request)
    yield next(generator)
    try:
        next(generator)
    except StopIteration:
        pass


@pytest.fixture(scope="module")
def sdk208_original(tmp_path_factory, request):
    generator = multifocal_original.__wrapped__(tmp_path_factory, request)
    yield next(generator)
    try:
        next(generator)
    except StopIteration:
        pass


def _hydrate(control, name):
    case = control.case(name)
    first_label = "first/root" if isinstance(control, MultiFocalOriginal) else "root"
    first = case["human"][first_label]["focal"]
    states = case["access_states"]
    captures, objects, locations, metadata = {}, {}, {}, set()
    for state in states.values():
        for key, record in state["captures"].items():
            data = control.value(record["data_ref"])
            if key in captures:
                assert captures[key].pin == record["pin"]
                assert canonical_json(captures[key].data) == canonical_json(data)
            else:
                captures[key] = SimpleNamespace(
                    pin=record["pin"], snapshot=record["snapshot"], data=data
                )
        for key, record in state["objects"].items():
            value = control.value(record)
            if key in objects:
                assert canonical_json(objects[key]) == canonical_json(value)
            else:
                objects[key] = value
        for key, value in state["locations"].items():
            if key in locations:
                assert canonical_json(locations[key]) == canonical_json(value)
            locations[key] = deepcopy(value)
        metadata.update(state["metadata_refs"])
    accesses = {}
    recorded_objects = set(objects)
    for focal, state in states.items():
        access = _access(captures, state["inputs"], objects, locations, focal)
        access._mode = "live"
        accesses[focal] = access
    # A native result can have been calculated through a target facade without
    # a named human destination there. Recreate that literal access ownership,
    # using the exact supplied captures/order, without constructing a Card.
    for key in captures:
        if key not in accesses:
            access = _access(captures, states[first]["inputs"], objects, locations, key)
            access._mode = "live"
            accesses[key] = access
    metadata.update(set(objects) - recorded_objects)
    cache = {}
    for access in accesses.values():
        access._objects, access._locations = objects, locations
        access._metadata_refs, access._scientific_cache = metadata, cache
    by_pin = {access._focal.pin: access for access in accesses.values()}
    results = {}
    for ref, value in list(objects.items()):
        if ref in metadata or not isinstance(value, dict):
            continue
        adapter = value.get("context", {}).get("adapter")
        if adapter not in (
            ADAPTER,
            "bioactivity_exploration@1",
            "literature_exploration@1",
        ):
            continue
        access = by_pin[value["context"]["card_ref"]]
        if adapter == ADAPTER:
            from sabueso.core.card_molecule_activity_history_v1 import restore_result

            result = restore_result(
                access,
                ref,
                value,
                entry_keys=retained_keys(control, name, ref, value),
                native_crossings=retained_crossings(control, name, ref),
            )
        elif adapter == "bioactivity_exploration@1":
            from sabueso.core.card_bioactivity_history_v2 import restore_result

            result = restore_result(ref, value)
        else:
            from sabueso.core.card_literature_history_v1 import restore_result

            result = restore_result(ref, value)
        key = (adapter, access._focal_key, canonical_json(result.options))
        if adapter == ADAPTER:
            key = (adapter, access._focal_key, tuple(access._inputs), key[-1])
        cache[key], results[ref] = result, result
    for state in states.values():
        for record in state["native_cache"]:
            key, payload = tuple(record["key"]), control.value(record["payload_ref"])
            if key in cache:
                assert canonical_json(cache[key]) == canonical_json(payload)
            cache[key] = payload
    machine_requests = []
    for query in case["machine"]:
        observed, request = query["selection"], query["selection"]["request"]
        access = accesses[query.get("focal", first)]
        selection = AccessSelection(
            access,
            observed["result_ref"],
            observed["selection_ref"],
            tuple(
                _Entry(
                    row["location"],
                    row["key"],
                    control.value(row["value_ref"]),
                    row["ordinal"],
                )
                for row in observed["entries"]
            ),
            observed["context_location"],
            request["target"],
            request["operation"],
            observed["slice"],
            results[observed["scientific_result_ref"]],
            tuple(request["fields"]),
            observed["outcome_override"],
        )
        access._selections[selection.selection_ref] = selection
        machine_requests.append(selection)
    session = {
        "views": {},
        "links": {},
        "explanations": {},
        "molecule_activity_root_policy": (
            "molecule_activity_root_selection_python_equality@1"
        ),
        "retained_original_machine_requests": tuple(machine_requests),
    }
    for access in accesses.values():
        access._exploration_session = session
    explorer = _explorer(accesses[first], session)
    from sabueso.core.card_context_presentation_v1 import LEGACY_POLICIES

    # These original producers predate the capability-aware action policy.
    session["presentation_metadata"]["molecule_activity_actions"] = LEGACY_POLICIES[
        "molecule_activity_actions"
    ]
    return explorer


def _bind_original_machine_requests(explorer):
    """Put executed original requests on each actually visited focal facade."""
    session = explorer._session
    accesses = {
        id(view._explorer.access): view._explorer.access
        for view in session["views"].values()
    }
    bound = set()
    for retained in session["retained_original_machine_requests"]:
        for access in accesses.values():
            if (
                access._focal_key == retained._access._focal_key
                and access._inputs == retained._access._inputs
            ):
                rebound = replace(retained, _access=access)
                access._selections[rebound.selection_ref] = rebound
                bound.add(retained.selection_ref)
    assert bound == {
        selection.selection_ref
        for selection in session["retained_original_machine_requests"]
    }


@contextmanager
def _retained_writer():
    # Import LIVE aliases before guards; temporary forbidden providers must not
    # become permanent aliases in a module imported later.
    presentations = {}
    for module in (
        "card_molecule_activity_exploration",
        "card_bioactivity_exploration",
        "card_literature_exploration",
    ):
        presentations[module] = importlib.import_module("sabueso.core." + module).view
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        # Reenact presentation over retained results only. Scientific providers
        # stay forbidden; the cache-only adapters below reject unretained calls.
        for module, view in presentations.items():
            guard.setattr(
                importlib.import_module("sabueso.core." + module), "view", view
            )
        from sabueso.core.card_exploration import CardExplorer

        def catalog(explorer):
            return _ORIGINAL_CATALOGS.get(
                explorer.profile, _ORIGINAL_CATALOGS["unknown"]
            )

        # Freeze the historical input/routing vocabulary for every destination.
        # Current LIVE menus remain available after this reenactment scope exits.
        for attribute, field in (
            ("_nature_topics", "nature_topics"),
            ("_topics", "topics"),
            ("_questions", "questions"),
        ):
            guard.setattr(
                CardExplorer,
                attribute,
                property(
                    lambda explorer, field=field: deepcopy(catalog(explorer)[field])
                ),
            )
        guard.setattr(
            CardExplorer,
            "_topic_label",
            lambda explorer, topic: catalog(explorer)["topics"][topic][0],
        )
        # Historical reenactment only: retain the SDK216 root-return branch from
        # a759b1d, before exact-origin LIVE navigation. Immutable original files
        # remain the oracle; this branch never supplies expected observations.
        from sabueso.core import card_molecule_activity_exploration as live

        current_follow = live.follow

        def original_follow(item):
            parent, explorer, link = item._view, item._view._explorer, item._entry.value
            navigation, role = link["molecule_activity_navigation"], link["role"]
            if role == "molecule_root":
                matches = [
                    candidate
                    for candidate in explorer._session["views"].values()
                    if candidate.view_ref == navigation["molecule_root_view_ref"]
                    and live._selection_binding(candidate)
                    == navigation["molecule_root_selection"]
                ]
                if not matches:
                    from sabueso.core.errors import ArgumentError

                    raise ArgumentError(
                        "The originating molecule selection is not retained."
                    )
                return replace(matches[0], _origin=parent, _request=parent.request)
            return current_follow(item)

        guard.setattr(live, "follow", original_follow)
        from sabueso.core._molecule_activity_history_v1.selection import normalize
        from sabueso.core.card_bioactivity_history_v2 import options_for_bioactivities
        from sabueso.core.card_literature_history_v1 import options_for_literature
        from sabueso.core.card_molecule_activity_history_v1 import (
            options_for_activity_context,
        )

        guard.setattr(
            importlib.import_module("sabueso.core.card_molecule_activity_selection_v1"),
            "normalize",
            normalize,
        )

        def retained(adapter, normalize):
            def lookup(access, options=None):
                key = (adapter, access._focal_key, canonical_json(normalize(options)))
                if adapter == ADAPTER:
                    key = (adapter, access._focal_key, tuple(access._inputs), key[-1])
                assert key in access._scientific_cache, (
                    "Unretained source request",
                    key,
                )
                return access._scientific_cache[key]

            return lookup

        for module, adapter, normalize_options in (
            (
                "card_molecule_activity_exploration",
                ADAPTER,
                options_for_activity_context,
            ),
            (
                "card_bioactivity_exploration",
                "bioactivity_exploration@1",
                options_for_bioactivities,
            ),
            (
                "card_literature_exploration",
                "literature_exploration@1",
                options_for_literature,
            ),
        ):
            guard.setattr(
                importlib.import_module("sabueso.core." + module),
                "materialize",
                retained(adapter, normalize_options),
            )

        def retained_native(adapter):
            def lookup(access, method, *args, **kwargs):
                arguments = (
                    [args, kwargs] if adapter == "bioactivity_exploration@1" else args
                )
                key = (
                    adapter,
                    "native",
                    access._focal_key,
                    method,
                    canonical_json(arguments),
                )
                assert key in access._scientific_cache, (
                    "Unretained native request",
                    key,
                )
                return access._scientific_cache[key]

            return lookup

        for module, adapter in (
            ("card_bioactivity_access", "bioactivity_exploration@1"),
            ("card_literature_access", "literature_exploration@1"),
        ):
            guard.setattr(
                importlib.import_module("sabueso.core." + module),
                "_native",
                retained_native(adapter),
            )
        yield


def _observer(control, name, mode):
    case, named = control.case(name), {}

    def remember(label, view):
        expected = case["human"][label]
        named[label] = view
        for key, actual in (
            ("view_ref", view.view_ref),
            ("result_ref", view.result_ref),
            ("request", view.request),
            ("schema", view.schema),
            ("outcome", view.outcome),
            ("display_request", view._display_request),
            ("title", view.title),
            ("presentation", view.presentation),
            ("record_panel", view._record_panel),
            ("focal", view.explorer.access._focal_key),
        ):
            assert canonical_json(actual) == canonical_json(expected[key]), (
                name,
                mode,
                label,
                key,
            )
        context = deepcopy(expected["context"])
        if "mode" in context:
            context["mode"] = mode
        assert canonical_json(view.context) == canonical_json(context), (
            name,
            mode,
            label,
            "context",
        )
        explorer_context = deepcopy(expected["explorer_context"])
        explorer_context["mode"] = mode
        assert canonical_json(view.explorer.context) == canonical_json(
            explorer_context
        ), (name, mode, label, "explorer_context")
        assert canonical_json(view.native_payload) == canonical_json(
            control.value(expected["native_payload_ref"])
        ), (name, mode, label, "native")
        assert [item.item_ref for item in view.items()] == [
            row["item_ref"] for row in expected["items"]
        ], (name, mode, label, "items")
        assert view.at_root == expected["at_root"], (name, mode, label, "at_root")
        assert (view.back().view_ref if not view.at_root else None) == expected[
            "back_view_ref"
        ], (name, mode, label, "back")
        from sabueso.core.card_exploration_storage import _cell_record

        for item, observed in zip(view.items(), expected["items"], strict=True):
            assert item.label == observed["label"] and item.kind == observed["kind"], (
                name,
                mode,
                label,
                "label/kind",
            )
            assert canonical_json(item.support) == canonical_json(
                control.value(observed["support_ref"])
            ), (name, mode, label, "support")
            for column, recorded in observed["cells"].items():
                expected_cell = {
                    k: v for k, v in recorded.items() if k != "support_ref"
                }
                expected_cell["support"] = control.value(recorded["support_ref"])
                assert canonical_json(
                    _cell_record(item, column, item.cells[column])
                ) == canonical_json(expected_cell), (name, mode, label, column)
        return view

    return named, remember


def _replay_sdk205(explorer, control, name, mode):
    case = control.case(name)
    named, remember = _observer(control, name, mode)
    options = case["human"]["root"]["context"].get("options", {})
    root = remember(
        "root", explorer.view("activity_context", options=options, skip_digestion=True)
    )
    if name != "wrong-focal-nature":
        remember(
            "question",
            explorer.answer("measured_targets", options=options, skip_digestion=True),
        )
    for label in ("topics", "questions"):
        recorded = case["human"][label]
        if mode == "live":
            catalog = (
                explorer.questions() if label == "questions" else explorer.topics()
            )
        else:
            # Fresh catalogs can advertise later delivered routes or availability.
            # Compare the actual retained original menu, without rewriting it.
            retained = [
                view
                for view in explorer._session["original_nodes"].values()
                if view.view_ref == recorded["view_ref"]
                and view.explorer.access._focal_key == recorded["focal"]
            ]
            assert len(retained) == 1, (name, label, "original menu instances")
            catalog = retained[0]
        remember(label, catalog)
    for ti, target_item in enumerate(root.items()):
        pin, prefix = target_item.cells["target_card_ref"].value, f"target/{ti}"
        filtered = remember(
            prefix + "/filtered-root",
            root.filter("target_card_ref", equals=pin, skip_digestion=True),
        )
        if filtered.items():
            fg = remember(prefix + "/filtered-groups", filtered.items()[0].open())
            if fg.items():
                fr = remember(prefix + "/filtered-records", fg.items()[0].open())
                if fr.items():
                    fl = remember(
                        prefix + "/filtered-record-links", fr.items()[0].related()
                    )
                    ret = next(
                        link
                        for link in fl.items()
                        if link._entry.value.get("role") == "molecule_root"
                    )
                    remember(prefix + "/filtered-return", ret.open())
        groups = remember(prefix + "/groups", target_item.open())
        remember(prefix + "/explain", target_item.explain())
        levels = [(prefix, target_item)]
        for gi, group in enumerate(groups.items()):
            gp = prefix + f"/group/{gi}"
            records = remember(gp + "/records", group.open())
            levels.append((gp, group))
            for ri, record in enumerate(records.items()):
                rp = gp + f"/record/{ri}"
                remember(rp + "/open", record.open())
                remember(rp + "/explain", record.explain())
                levels.append((rp, record))
                focus = dict(
                    groups._selection._scientific.options,
                    molecule_ref=record.cells["molecule_ref"].value,
                    measurement_ref=record.cells["relationship_id"].value,
                )
                remember(
                    rp + "/exact-source-focus",
                    explorer.view(
                        "activity_context", options=focus, skip_digestion=True
                    ),
                )
        for lp, item in levels:
            links = remember(lp + "/links", item.related())
            for li, link in enumerate(links.items()):
                role = link._entry.value.get("role")
                label = lp + f"/link/{li}/{role}"
                if label not in case["human"]:
                    continue
                opened = remember(label, link.open())
                if role == "target_card" and lp == prefix and name in ("bts", "benz"):
                    remember(
                        lp + "/fresh-publications",
                        opened.explorer.answer("publications", skip_digestion=True),
                    )
                    remember(
                        lp + "/fresh-measured-molecules",
                        opened.explorer.answer(
                            "measured_molecules", skip_digestion=True
                        ),
                    )
        if groups.items():
            fg = remember(
                prefix + "/bts-groups",
                groups.filter(
                    "molecule_ref", equals="chembl:CHEMBL1161789", skip_digestion=True
                ),
            )
            remember(
                prefix + "/ordered-bts-groups",
                fg.sort("measurement", unit="nanomolar", skip_digestion=True),
            )
            remember(
                prefix + "/null-measurement-groups",
                groups.filter("measurement", equals=None, skip_digestion=True),
            )
    assert set(named) == set(case["human"])
    return root, len(named)


def _machine_replay(root, control, name):
    case = control.case(name)

    def normalized(value, resolve):
        if isinstance(value, dict):
            if (
                value.get("format") == "card_access_location@1"
                and value.get("kind") == "lookup"
            ):
                return resolve(value)
            return {key: normalized(child, resolve) for key, child in value.items()}
        if isinstance(value, list):
            return [normalized(child, resolve) for child in value]
        return value

    total = 0
    for query in case["machine"]:
        focal = query.get("focal", root.explorer.access._focal_key)
        state = case["access_states"][focal]
        access = root.explorer.access._for_capture(focal)
        selection = access.select(
            "activity_context", **query["query"], skip_digestion=True
        )
        assert selection.selection_ref == query["selection"]["selection_ref"]
        cursor, seen = None, set()
        pages = control.value(query["pages_ref"])
        for expected in pages:
            actual = selection.page(
                limit=1, max_bytes=65536, cursor=cursor, skip_digestion=True
            )
            actual = deepcopy(actual)
            expected = deepcopy(expected)
            expected["context"]["mode"] = "saved"
            cursor = actual["page"]["next_cursor"]
            assert (cursor is None) == (expected["page"]["next_cursor"] is None)
            if cursor is not None:
                assert cursor not in seen
                seen.add(cursor)
                # Session-authenticated cursor bytes are not original scientific
                # content; retain/check all offsets, scope and page values.
                actual["page"]["next_cursor"] = "<session-cursor>"
                expected["page"]["next_cursor"] = "<session-cursor>"
            assert canonical_json(
                normalized(actual, lambda loc: selection._access._resolve(loc)[1])
            ) == canonical_json(
                normalized(
                    expected, lambda loc: state["locations"][loc["location_ref"]]
                )
            ), (name, query["name"], "machine page")
            total += 1
        assert cursor is None
    return len(case["machine"]), total


def _replay_sdk208(explorer, control, name, mode):
    case = control.case(name)
    named, remember = _observer(control, name, mode)

    def role(view, value):
        return next(
            item for item in view.items() if item._entry.value.get("role") == value
        )

    first = remember(
        "first/root", explorer.answer("measured_targets", skip_digestion=True)
    )
    first_links = remember("first/links", first.items()[0].related())
    first_native = remember(
        "first/native", role(first_links, "native_ligand_crossing").open()
    )
    protein = remember("target/destination", role(first_links, "target_card").open())
    activity = remember(
        "target/measured-molecules",
        protein.explorer.answer("measured_molecules", skip_digestion=True),
    )
    alias = "chembl:CHEMBL110" if name == "bts-to-benz" else "chembl:CHEMBL1161789"
    molecule = next(
        item for item in activity.items() if item.cells["molecule_ref"].value == alias
    )
    molecule_links = remember("target/second-molecule-links", molecule.related())
    relationship = remember(
        "target/original-relationship",
        role(molecule_links, "original_relationship").open(),
    )
    reference = next(
        item for item in relationship.items() if item._entry.key == "object_ref"
    )
    destinations = remember("target/declared-object-destinations", reference.related())
    second_pin = case["crossings"]["second"]["molecule_pin"]

    def candidate(view):
        return next(
            item
            for item in view.items()
            if any(
                value["capture"] == second_pin
                for value in item._entry.value.get("candidates", [])
            )
        )

    destination = candidate(destinations).open()
    if destination.explorer.context["card_ref"] != second_pin:
        remember("second/ambiguous-candidates", destination)
        destination = candidate(destination).open()
    remember("second/destination", destination)
    assert destination.explorer.context["card_ref"] == second_pin
    second = remember(
        "second/root",
        destination.explorer.answer("measured_targets", skip_digestion=True),
    )
    second_links = remember("second/links", second.items()[0].related())
    second_native = remember(
        "second/native", role(second_links, "native_ligand_crossing").open()
    )
    for prefix, root, links, native in (
        ("first", first, first_links, first_native),
        ("second", second, second_links, second_native),
    ):
        remember(
            prefix + "/native-repeat", role(links, "native_ligand_crossing").open()
        )
        remember(prefix + "/native-back", native.back())
        groups = remember(prefix + "/groups", root.items()[0].open())
        for gi, group in enumerate(groups.items()):
            records = remember(prefix + f"/group/{gi}/records", group.open())
            for ri, item in enumerate(records.items()):
                rp = prefix + f"/group/{gi}/record/{ri}"
                remember(rp + "/open", item.open())
                remember(rp + "/explain", item.explain())
                links = remember(rp + "/links", item.related())
                for li, link in enumerate(links.items()):
                    label = rp + f"/link/{li}/" + link._entry.value["role"]
                    if label in case["human"]:
                        remember(label, link.open())
    publications = remember(
        "target/publications",
        protein.explorer.answer("publications", skip_digestion=True),
    )
    for ref in ("pubmed:35189560", "pubmed:20889239"):
        item = next(
            item
            for item in publications.items()
            if item.cells["publication_ref"].value == ref
        )
        remember("target/publication/" + ref, item.open())
    assert set(named) == set(case["human"])
    return first, len(named)


def _receive(original_path, source, name, file_path, report_path):
    from test_card_molecule_activity_binding_offline import block_current as block_ui

    from sabueso.core.card_exploration_storage import read_exploration

    control = (
        Original(original_path)
        if source == "sdk205"
        else MultiFocalOriginal(original_path)
    )
    recipe = _replay_sdk205 if source == "sdk205" else _replay_sdk208
    with pytest.MonkeyPatch.context() as guard:
        block_ui(guard)
        root = read_exploration(
            file_path,
            max_encoded_bytes=None,
            max_decoded_bytes=None,
            max_logical_bytes=None,
        )
        _, count = recipe(root.explorer, control, name, "saved")
        queries, pages = _machine_replay(root, control, name)
        assert root.capabilities["save"]
    report = {
        "source": source,
        "case": name,
        "original_named_views": count,
        "original_machine_queries": queries,
        "original_machine_pages": pages,
        "cards_science_clients_digesters_and_molecule_ui_forbidden": True,
        "cwd": str(Path.cwd()),
        "actual_file": str(file_path),
    }
    Path(report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    control.close()


@pytest.mark.parametrize(
    "source,name",
    [("sdk208", name) for name in SUPPLEMENT_CASES]
    + [("sdk205", name) for name in CASES],
)
def test_complete_original_human_and_machine_file_journey(
    source, name, request, tmp_path
):
    control = request.getfixturevalue(
        "sdk205_original" if source == "sdk205" else "sdk208_original"
    )
    explorer = _hydrate(control, name)
    recipe = _replay_sdk205 if source == "sdk205" else _replay_sdk208
    path = tmp_path / "original-molecule.json"
    with _retained_writer():
        root, count = recipe(explorer, control, name, "live")
        _bind_original_machine_requests(explorer)
        root.save(
            path,
            max_encoded_bytes=None,
            max_decoded_bytes=None,
            max_logical_bytes=None,
            skip_digestion=True,
        )
    assert path.is_file()
    report_path = tmp_path / "reader-report.json"
    script = "import sys\nsys.path.insert(0, sys.argv[1])\nfrom test_card_saved_molecule_activity_originals_offline import _receive\n_receive(*sys.argv[2:])\n"
    with tempfile.TemporaryDirectory(
        prefix="sabueso-original-molecule-reader-",
        dir=None if sys.platform == "win32" else "/tmp",
    ) as directory:
        child = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                script,
                str(Path(__file__).resolve().parent),
                str(control.archive.name),
                source,
                name,
                str(path.resolve()),
                str(report_path.resolve()),
            ],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=1200,
        )
    assert child.returncode == 0, child.stdout + child.stderr
    assert not child.stderr, child.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["original_named_views"] == count == len(control.case(name)["human"])
    assert report["original_machine_queries"] == len(control.case(name)["machine"])


@pytest.mark.parametrize("change", ("origin", "question_scope", "focal"))
def test_incoming_molecule_question_requires_its_exact_target_transition(
    sdk208_original, change
):
    from sabueso.core import card_exploration_molecule_activity as binding
    from sabueso.core.errors import StorageError

    explorer = _hydrate(sdk208_original, "bts-to-benz")
    with _retained_writer():
        _replay_sdk208(explorer, sdk208_original, "bts-to-benz", "live")
        view = next(
            view
            for view in explorer._session["views"].values()
            if view._record_panel == "bioactivities"
            and view.request is not None
            and view.request["question"] == "measured_targets"
        )
        if change == "origin":
            altered = replace(view, _origin=None)
        elif change == "question_scope":
            request = deepcopy(view.request)
            request["options"]["include_indirect"] = not request["options"][
                "include_indirect"
            ]
            altered = replace(view, _request=request)
        else:
            altered = replace(view, _explorer=explorer)
        # Each refusal must happen at the incoming transition, before a missing
        # frozen view record could cause an unrelated validation failure.
        with pytest.raises(StorageError, match="[Ii]ncoming|incoming"):
            binding.verify_bioactivity_view(altered, {})


@pytest.mark.parametrize("change", ("origin", "question_scope", "focal", "candidate"))
def test_incoming_protein_question_requires_its_exact_molecule_transition(
    sdk208_original, change
):
    from sabueso.core import card_exploration_molecule_activity as binding
    from sabueso.core.errors import StorageError

    explorer = _hydrate(sdk208_original, "bts-to-benz")
    with _retained_writer():
        _replay_sdk208(explorer, sdk208_original, "bts-to-benz", "live")
        view = next(
            view
            for view in explorer._session["views"].values()
            if binding.is_view(view)
            and isinstance(view.request, dict)
            and view.request["question"] == "measured_molecules"
        )
        binding._question(view)
        if change == "origin":
            altered = replace(view, _origin=None)
        elif change == "question_scope":
            request = deepcopy(view.request)
            request["options"]["include_indirect"] = not request["options"][
                "include_indirect"
            ]
            altered = replace(view, _request=request)
        elif change == "focal":
            altered = replace(view, _explorer=explorer)
        else:
            # Keep the valid protein panel but omit the actually selected
            # molecule. No missing frozen-view record participates in this check.
            parent = view._origin
            rows = tuple(
                entry
                for entry in parent._selected
                if not any(
                    candidate["capture"] == view._explorer.access._focal_key
                    for candidate in entry.value["candidates"]
                )
            )
            assert rows != parent._selected
            altered = replace(view, _origin=replace(parent, _selected=rows))
        with pytest.raises(StorageError):
            binding._question(altered)


def test_equal_label_molecule_endpoints_keep_their_exact_original_locations(
    sdk205_original,
):
    from sabueso.core import card_exploration_molecule_activity as binding
    from sabueso.core import card_molecule_activity_operations_v1 as operations
    from sabueso.core.card_exploration_storage import _freeze_view
    from sabueso.core.errors import StorageError

    explorer = _hydrate(sdk205_original, "multiple-aliases")
    with _retained_writer():
        _replay_sdk205(explorer, sdk205_original, "multiple-aliases", "live")
        views = list(explorer._session["views"].values())
        ids = {id(view): f"N{index}" for index, view in enumerate(views)}
        checked = 0
        for view in views:
            parent = view._origin
            if (
                not binding.is_context(view)
                or parent is None
                or not parent._link_panel
                or not binding.is_context(parent)
                or view._context_override["activity_context"]
                not in ("assay_context", "citation_context")
            ):
                continue
            role = view._context_override["activity_context"]
            choices = [
                entry
                for entry in parent._selected
                if entry.value["role"] == role and entry.value["label"] == view.title
            ]
            if len(choices) < 2:
                continue
            exact = binding._endpoint_entries(view, parent, role)
            assert len(exact) == 1
            assert operations._edge(view) == (parent, "open", exact[0].key)
            record = _freeze_view(view, ids)
            binding.verify_context(view, record)
            foreign = replace(
                view._selection,
                _target={
                    **view._selection._target,
                    "location": view._explorer.access.root_location,
                },
            )
            with pytest.raises(StorageError, match="unique exact original destination"):
                binding._endpoint_entries(
                    replace(view, _selection=foreign), parent, role
                )
            other = next(entry for entry in choices if entry.key != exact[0].key)
            swapped = replace(
                view._selection,
                _target={
                    **view._selection._target,
                    "location": other.value["candidates"][0]["location"],
                },
            )
            with pytest.raises(StorageError):
                binding.verify_context(replace(view, _selection=swapped), record)
            checked += 1
        assert checked == 4


@pytest.mark.parametrize("kind", ("bioactivity", "literature"))
def test_incoming_anchor_verification_is_scoped_to_one_graph(
    sdk208_original, monkeypatch, kind
):
    from sabueso.core import card_exploration_molecule_activity as binding
    from sabueso.core.card_exploration_storage import _freeze_view
    from sabueso.core.errors import StorageError

    explorer = _hydrate(sdk208_original, "bts-to-benz")
    with _retained_writer():
        _replay_sdk208(explorer, sdk208_original, "bts-to-benz", "live")
        panel = "bioactivities" if kind == "bioactivity" else "literature"
        anchor = next(
            view
            for view in explorer._session["views"].values()
            if view._record_panel == panel
            and isinstance(view.request, dict)
            and view.request["question"] == "measured_targets"
        )
        ids = {key: f"N{index}" for index, key in enumerate(explorer._session["views"])}
        probe = replace(anchor, _saved_state=_freeze_view(anchor, ids)["state"])
        verifier = getattr(binding, "verify_" + kind + "_view")
        calls = []

        def checked(view, record):
            calls.append(view)
            return verifier(view, record)

        monkeypatch.setattr(binding, "verify_" + kind + "_view", checked)
        bridge = getattr(binding, "_" + kind + "_bridge")
        with binding.verification_scope():
            bridge(probe)
            bridge(probe)
        assert len(calls) == 1
        with binding.verification_scope():
            bridge(probe)
        assert len(calls) == 2
        # Reuse the same object identity with an altered request after the first
        # graph closes: a cached proof must not survive into another verification.
        request = deepcopy(probe.request)
        request["options"]["include_indirect"] = not request["options"][
            "include_indirect"
        ]
        object.__setattr__(probe, "_request", request)
        with binding.verification_scope(), pytest.raises(StorageError):
            bridge(probe)


def test_recorded_molecule_destination_requires_exact_candidate_and_back_history(
    sdk208_original,
):
    from sabueso.core import card_exploration_molecule_activity as binding
    from sabueso.core.card_exploration_storage import _freeze_view

    explorer = _hydrate(sdk208_original, "bts-to-benz")
    with _retained_writer():
        _replay_sdk208(explorer, sdk208_original, "bts-to-benz", "live")
        nodes = {
            f"N{index}": view
            for index, view in enumerate(explorer._session["views"].values())
        }
        destination = next(
            view
            for view in nodes.values()
            if view._route_catalog
            and view.title == "Card overview"
            and view._explorer.access.profile == "small_molecule"
            and view._origin is not None
            and view._origin._link_panel
            and view._origin._explorer.access.profile == "protein"
        )
        ids = {id(view): key for key, view in nodes.items()}
        stored = replace(
            destination, _saved_state=_freeze_view(destination, ids)["state"]
        )
        nodes[ids[id(destination)]] = stored
        parent = destination._origin
        candidate = next(
            candidate
            for entry in parent._selected
            for candidate in entry.value["candidates"]
            if candidate["capture"] == destination._explorer.access._focal_key
        )
        session = explorer._session
        session.update(format=binding.FORMAT, original_nodes=nodes)
        for view in nodes.values():
            view._explorer.access._mode = "saved"
        opened = binding.saved_declared_destination(parent._explorer, candidate, parent)
        assert opened is not None and opened.view_ref == stored.view_ref
        assert (
            opened._origin is parent and opened.native_payload == stored.native_payload
        )
        wrong_candidate = {**candidate, "capture": explorer.access._focal_key}
        assert (
            binding.saved_declared_destination(
                parent._explorer, wrong_candidate, parent
            )
            is None
        )
        request = deepcopy(parent.request)
        request["options"]["include_indirect"] = not request["options"][
            "include_indirect"
        ]
        for altered in (
            replace(parent, _origin=None),
            replace(parent, _request=request),
        ):
            assert (
                binding.saved_declared_destination(parent._explorer, candidate, altered)
                is None
            )


def test_original_bioactivity_literal_child_keeps_its_exact_selected_parent(
    sdk208_original,
):
    from sabueso.core import card_exploration_bioactivity_v2 as bioactivity
    from sabueso.core import card_exploration_molecule_activity as binding
    from sabueso.core.card_exploration_storage import _freeze_view
    from sabueso.core.errors import StorageError

    explorer = _hydrate(sdk208_original, "bts-to-benz")
    with _retained_writer():
        _replay_sdk208(explorer, sdk208_original, "bts-to-benz", "live")
        view = next(
            view
            for view in explorer._session["views"].values()
            if bioactivity.is_context(view)
            and view._origin is not None
            and bioactivity.is_context(view._origin)
            and not view._origin._link_panel
            and not view._link_panel
            and view._context_override["bioactivity_context"] == "original_relationship"
            and view.request is not None
            and view.request["question"] == "measured_molecules"
        )
        ids = {key: f"N{index}" for index, key in enumerate(explorer._session["views"])}
        record = _freeze_view(view, ids)
        binding.verify_bioactivity_context(view, record)
        wrong_location = replace(
            view._selection,
            _target={
                **view._selection._target,
                "location": view._explorer.access.root_location,
            },
        )
        wrong_context = {
            **view._context_override,
            "bioactivity_context": "assay_context",
        }
        for altered in (
            replace(view, _selection=wrong_location),
            replace(view, _context_override=wrong_context),
        ):
            with pytest.raises(StorageError):
                binding.verify_bioactivity_context(altered, record)
