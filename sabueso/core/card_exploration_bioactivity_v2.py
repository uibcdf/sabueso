"""SDK202 bioactivity predicates for semantic exploration @19.

The whole original wire and on-demand publication contexts use the separately
frozen SDK202 facade. Unchanged original row, literal, selection and navigation
predicates are reused from immutable @17; its reader and saved meanings remain
unchanged. File format @19 selects this binding explicitly, never payload or
producer-version guessing.
"""

from ._bioactivity_history_v1.selection import FORMAT as SELECTION_FORMAT
from ._bioactivity_history_v1.selection import sorted_entries
from .card_access import _handle
from .card_bioactivity_history_v2 import (
    expected_publication,
    expected_result,
    options_for_bioactivities,
    restore_result,
)
from .card_exploration_bioactivity import ADAPTER as ADAPTER
from .card_exploration_bioactivity import ADAPTERS as ADAPTERS
from .card_exploration_bioactivity import LINK_RULE as LINK_RULE
from .card_exploration_bioactivity import SCHEMA as SCHEMA
from .card_exploration_bioactivity import TOPIC as TOPIC
from .card_exploration_bioactivity import (
    _filter_result,
    _literal_context,
    _literal_selection,
    _literal_state,
    _machine,
    _view_state,
    require,
    same,
)
from .card_exploration_bioactivity import display_filter as display_filter
from .card_exploration_bioactivity import display_sort as display_sort
from .card_exploration_bioactivity import follow as follow
from .card_exploration_bioactivity import is_context as is_context
from .card_exploration_bioactivity import is_explanation as is_explanation
from .card_exploration_bioactivity import is_result as is_result
from .card_exploration_bioactivity import is_view as is_view
from .card_exploration_bioactivity import open_item as open_item
from .card_exploration_bioactivity import result_location as result_location
from .card_exploration_bioactivity import retain_machine_views as retain_machine_views
from .card_exploration_bioactivity import saved_selection as saved_selection
from .card_exploration_bioactivity import saved_topic as saved_topic
from .card_exploration_bioactivity import validate_filters as validate_filters
from .card_exploration_bioactivity import verify_explanation as verify_explanation
from .card_exploration_bioactivity import verify_links as verify_links
from .errors import StorageError

FORMAT = "sabueso.card_exploration@19"
VERIFIER = "bioactivity_exploration_binding@2"


def verify_objects(bundle, accesses):
    from .card_exploration_chemical import verify_objects as older_objects

    older = {}
    for ref, record in bundle["scientific_results"].items():
        require(
            ref in bundle["objects"] and isinstance(record, dict),
            "Missing scientific result or manifest.",
        )
        wire = bundle["objects"][ref]
        require(
            isinstance(wire, dict)
            and isinstance(wire.get("context"), dict)
            and wire["context"].get("adapter") in ADAPTERS,
            "Unsupported SDK202 bioactivity manifest adapter.",
        )
        if wire["context"]["adapter"] != ADAPTER:
            older[ref] = record
            continue
        require(
            set(record) == {"focal"} and record["focal"] in accesses,
            "Unknown SDK202 bioactivity manifest member or focal capture.",
        )
        options = options_for_bioactivities(wire["context"]["options"])
        same(
            wire["context"]["options"], options, "SDK202 bioactivity effective options"
        )
        expected = expected_result(accesses[record["focal"]], options, original=wire)
        require(
            ref == expected.result_ref,
            "SDK202 bioactivity result identity differs from its original inputs/options.",
        )
        same(
            wire,
            expected.wire,
            "SDK202 whole bioactivity wire, records, grouping, quantities, classifications and complete literature context",
        )
    older_objects({**bundle, "scientific_results": older}, accesses)


def verify_context(view, record):
    access, anchor, seen = view._explorer.access, view, set()
    require(
        not any(
            (
                view._record_panel,
                view._field_panel,
                view._link_panel,
                view._route_catalog,
                view._question_catalog,
                view._focus,
                view._component_navigation,
            )
        )
        and view._selection._scientific is None,
        "Foreign bioactivity destination presentation flags.",
    )
    while anchor._display_request is not None:
        require(
            id(anchor) not in seen
            and anchor._origin is not None
            and is_context(anchor._origin),
            "Bioactivity destination display has a cyclic/foreign origin.",
        )
        seen.add(id(anchor))
        require(
            anchor._selection.selection_ref == anchor._origin._selection.selection_ref
            and anchor.result_ref == anchor._origin.result_ref,
            "Bioactivity destination display changed its original request.",
        )
        anchor = anchor._origin
    parent = anchor._origin
    require(
        parent is not None
        and parent._link_panel
        and parent.native_payload.get("rule") == LINK_RULE,
        "Bioactivity destination lost its original link/back context.",
    )
    verify_links(parent)
    role = anchor._context_override.get("bioactivity_context")
    choices = [
        link
        for link in parent.native_payload["links"]
        if link["role"] == role and link["label"] == anchor.title
    ]
    require(
        len(choices) == 1, "Bioactivity destination has no unique exact retained link."
    )
    link = choices[0]
    require(
        len(link["candidates"]) <= 1, "Unsupported bioactivity destination ambiguity."
    )
    if link["candidates"]:
        require(
            not anchor._context_only
            and link["candidates"][0]["capture"] == access._focal_key,
            "Bioactivity context switched to a foreign capture.",
        )
        full = link["candidates"][0]["location"]
        native = access._resolve(full)[0]
        if role == "publication_context":
            actual, full = access._resolve(anchor._selection._target["location"])
            expected = expected_publication(
                access, native["publication_ref"], original=actual
            )
            same(
                actual,
                expected,
                "full original publication summary, links and source support",
            )
            require(
                full["kind"] == "result"
                and full["result_ref"] in access._metadata_refs,
                "Publication context lost its retained literal metadata owner.",
            )
            native = expected["original_explanation"]
        expected_context = {
            **_literal_context(access),
            "adapter": LINK_RULE,
            "bioactivity_context": role,
        }
        expected_status = "ok" if anchor._selection.count else "empty"
        expected_reason = (
            None if anchor._selection.count else "This retained container is empty."
        )
    else:
        require(
            anchor._context_only and link["availability"] == "missing_prerequisite",
            "Unavailable source context acquired a false focal identity.",
        )
        native = {"link": link}
        _, full = access._resolve(anchor._selection._target["location"])
        same(access._resolve(full)[0], native, "unavailable source context")
        require(
            full["kind"] == "result" and full["result_ref"] in access._metadata_refs,
            "Unavailable source context has no literal metadata owner.",
        )
        expected_context = {
            "card_ref": None,
            "snapshot_id": None,
            "subject_ref": link["target_ref"],
            "profile": None,
            "mode": "live",
            "adapter": LINK_RULE,
            "bioactivity_context": role,
            "captures": access.context["captures"],
        }
        expected_status = "missing_prerequisite"
        expected_reason = "The referenced original source statement is not retained; no replacement or attribution is inferred."
    _literal_selection(anchor, full)
    if view is not anchor:
        _literal_selection(view, full)
    require(
        view._context_only == anchor._context_only
        and view._machine_ref is None
        and anchor._machine_ref is None,
        "Bioactivity destination display changed its retained availability/operation kind.",
    )
    require(
        anchor._status == expected_status and anchor._reason == expected_reason,
        "Bioactivity destination changed its literal availability.",
    )
    same(
        anchor._context_override,
        expected_context,
        "bioactivity destination original focal/role context",
    )
    same(
        view._context_override,
        expected_context,
        "bioactivity destination display context",
    )
    same(
        anchor.native_payload, native, "bioactivity destination complete native payload"
    )
    same(
        record["native_payload"],
        native,
        "bioactivity destination recorded native payload",
    )
    require(
        record.get("native_encoding", "json") == "json",
        "Unknown bioactivity destination encoding.",
    )
    context = record["state"]["context"]
    require(
        context.get("mode") in ("live", "saved"),
        "Unknown saved bioactivity context mode.",
    )
    same(
        context,
        {**expected_context, "mode": context["mode"]},
        "bioactivity destination saved focal context",
    )
    _question(view)
    _literal_state(view, record)
    return native


def _question(view, result=None):
    request, parent = view.request, view._origin
    inherited = parent is not None and (
        is_view(parent)
        or is_context(parent)
        or (parent._link_panel and parent.native_payload.get("rule") == LINK_RULE)
    )
    if inherited:
        require(
            parent._explorer.access._focal_key == view._explorer.access._focal_key,
            "SDK202 bioactivity inherited navigation has a foreign focal capture.",
        )
        same(request, parent.request, "SDK202 bioactivity original question continuity")
    if request is None:
        return
    require(
        isinstance(request, dict)
        and set(request) == {"question", "topic", "options"}
        and request["question"] == "measured_molecules"
        and request["topic"] == TOPIC,
        "Unsupported SDK202 bioactivity human question.",
    )
    same(
        request["options"],
        options_for_bioactivities(request["options"]),
        "SDK202 bioactivity question options",
    )
    if result is not None and not inherited:
        same(
            request["options"],
            result.options,
            "SDK202 bioactivity question/result scope",
        )
        if parent is not None and parent._link_panel:
            require(
                any(
                    candidate["capture"] == view._explorer.access._focal_key
                    for link in parent.native_payload["links"]
                    for candidate in link["candidates"]
                ),
                "SDK202 bioactivity question has no retained originating Card destination.",
            )


def verify_view(view, record):
    access, selection = view._explorer.access, view._selection
    require(
        view._record_panel == TOPIC
        and is_result(selection._scientific)
        and not any(
            (
                view._field_panel,
                view._link_panel,
                view._route_catalog,
                view._question_catalog,
                view._context_only,
                view._focus,
                view._component_navigation,
            )
        ),
        "Foreign bioactivity presentation flags.",
    )
    result = restore_result(view.result_ref, access._objects[view.result_ref])
    require(
        result.wire["context"]["card_ref"] == access._focal.pin
        and result.wire["context"]["snapshot_id"] == access._focal.snapshot,
        "Bioactivity view has a foreign focal capture.",
    )
    require(
        selection._slice is None
        and selection._outcome_override is None
        and view.presentation in SCHEMA["presentations"],
        "Unsupported bioactivity selection/presentation options.",
    )
    if selection._operation.startswith("select:"):
        entries = _machine(selection, access, result)
    else:
        entries = result.entries
        human_ref = _handle(
            "XA_",
            {
                "format": "bioactivity_human_selection@1",
                "result_ref": result.result_ref,
            },
        )
        _literal_selection(
            view, result.location(), entries=entries, result_override=human_ref
        )
    same(
        [vars(entry) for entry in selection._entries],
        [vars(entry) for entry in entries],
        "bioactivity original row membership",
    )
    same(view._context_override, result.wire["context"], "bioactivity context override")
    _view_state(view, record, result, entries)
    _question(view, result)
    require(
        view._machine_ref
        == (
            selection.selection_ref
            if selection._operation.startswith("select:")
            else None
        ),
        "Foreign bioactivity machine-origin binding.",
    )
    operation, parent = view._display_request, view._origin
    native = result.wire["native_payload"]
    if operation is not None:
        require(
            parent is not None
            and parent.result_ref == view.result_ref
            and parent._record_panel == TOPIC
            and parent._selection.selection_ref == selection.selection_ref,
            "Bioactivity display crossed its original result/request.",
        )
        if operation.get("operation") == "filter":
            require(
                set(operation) == {"operation", "column", "equals", "filter_policy"}
                and operation["filter_policy"] == SELECTION_FORMAT,
                "Unsupported bioactivity filter policy.",
            )
            expected_entries, expected_outcome = _filter_result(
                parent, operation["column"], operation["equals"]
            )
        elif operation.get("operation") == "sort":
            require(
                set(operation)
                == {"operation", "column", "descending", "unit", "selection_policy"}
                and operation["selection_policy"] == SELECTION_FORMAT,
                "Unsupported bioactivity ordering policy.",
            )
            expected_entries = sorted_entries(
                parent._selected,
                result,
                operation["column"],
                descending=operation["descending"],
                unit=operation["unit"],
            )
            expected_outcome = parent.outcome
        else:
            require(
                operation == {"operation": "presentation"},
                "Unsupported bioactivity display operation.",
            )
            expected_entries, expected_outcome = parent._selected, parent.outcome
        same(
            [vars(entry) for entry in view._selected],
            [vars(entry) for entry in expected_entries],
            "bioactivity display order/membership",
        )
        same(view.outcome, expected_outcome, "bioactivity display outcome")
        base, seen = view, set()
        while base._display_request is not None and base._origin is not None:
            require(id(base) not in seen, "Cyclic bioactivity display origin.")
            seen.add(id(base))
            base = base._origin
            require(
                base.result_ref == view.result_ref
                and base._selection.selection_ref == selection.selection_ref,
                "Bioactivity display lost its original request.",
            )
        if base.presentation == "detail" and len(base._selected) == 1:
            native = base._selected[0].value["item"]
    elif view.presentation == "detail":
        require(
            parent is not None
            and is_view(parent)
            and parent.result_ref == view.result_ref
            and len(view._selected) == 1
            and view._selected[0] in parent._selection._entries
            and view._selected[0].value["kind"] == "bioactivity_record",
            "Bioactivity detail is not an original selected source record.",
        )
        same(view.outcome, parent.outcome, "bioactivity detail outcome")
        native = view._selected[0].value["item"]
    else:
        same(
            [vars(entry) for entry in view._selected],
            [vars(entry) for entry in entries],
            "bioactivity unrestricted selection",
        )
        same(view.outcome, result.wire["outcome"], "bioactivity original outcome")
        _verify_focus_origin(view, result)
    require(
        record.get("native_encoding", "json") == "json",
        "Unsupported bioactivity native encoding.",
    )
    same(
        record["native_payload"], native, "complete original bioactivity native payload"
    )


def _verify_focus_origin(view, result):
    parent = view._origin
    if parent is None or not is_view(parent):
        return
    require(
        parent._explorer.access._focal_key == view._explorer.access._focal_key,
        "SDK202 bioactivity drill-down has a foreign focal capture.",
    )
    same(
        {
            key: value
            for key, value in parent._selection._scientific.wire["context"].items()
            if key not in ("options", "grain", "focus_membership")
        },
        {
            key: value
            for key, value in result.wire["context"].items()
            if key not in ("options", "grain", "focus_membership")
        },
        "SDK202 bioactivity drill-down original capture context",
    )
    if parent.result_ref == view.result_ref:
        return
    old = parent._selection._scientific.options
    same(
        {
            key: value
            for key, value in old.items()
            if key not in ("molecule_ref", "measurement_ref")
        },
        {
            key: value
            for key, value in result.options.items()
            if key not in ("molecule_ref", "measurement_ref")
        },
        "bioactivity drill-down scientific policies",
    )
    grain = result.wire["context"]["grain"]
    if grain == "group":
        require(
            result.options["measurement_ref"] is None
            and any(
                entry.value["kind"] == "bioactivity_molecule"
                and entry.value["molecule_ref"] == result.options["molecule_ref"]
                for entry in parent._selection._entries
            ),
            "Bioactivity molecule drill-down lost its selected original member.",
        )
    elif grain == "record":
        require(
            any(
                entry.value["kind"] == "bioactivity_group"
                and entry.value["molecule_ref"] == result.options["molecule_ref"]
                and entry.value["measurement_ref"] == result.options["measurement_ref"]
                for entry in parent._selection._entries
            ),
            "Bioactivity group drill-down lost its selected original group.",
        )
    else:
        raise StorageError("Unsupported bioactivity drill-down origin.")
