"""Original protein sequence changes: typed projection, support and uncertainty."""

import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.card_sequence_change_access import ADAPTER, materialize
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json
from sabueso.mappings.uniprot import map_protein

DATA = Path(__file__).resolve().parents[2] / "temp_data"
if not (DATA / "P60174.json").is_file():
    DATA = Path.cwd() / "temp_data"


def forbidden(*args, **kwargs):
    raise AssertionError("No acquisition or implicit scientific evaluation")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    for module in ("card_variant_access", "card_scientific_access"):
        monkeypatch.setattr(
            importlib.import_module("sabueso.core." + module), "materialize", forbidden
        )


def mapped(record):
    return build_card_from_mapping(
        map_protein(record, "offline public or labelled synthetic input"),
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:P60174",
    )


@pytest.fixture
def public():
    return mapped(json.loads((DATA / "P60174.json").read_text(encoding="utf-8")))


def feature(kind="Natural variant", **changes):
    return {
        "type": kind,
        "description": "explicit synthetic <change>",
        "location": {
            "start": {"value": 2, "modifier": "EXACT"},
            "end": {"value": 2, "modifier": "EXACT"},
        },
        "alternativeSequence": {
            "originalSequence": "M",
            "alternativeSequences": ["A", "G"],
        },
        **changes,
    }


def synthetic(features=None):
    return mapped(
        {
            "primaryAccession": "P60174",
            "sequence": {"value": "M" * 10, "length": 10},
            "entryAudit": {"sequenceVersion": 7},
            "features": [feature(), feature("Mutagenesis")]
            if features is None
            else features,
        }
    )


def frames(selection, **options):
    result, cursor = [], None
    while True:
        page = selection.page(cursor=cursor, **options)
        assert len(canonical_json(page).encode("utf-8")) <= options.get(
            "max_bytes", 65536
        )
        assert page["page"]["blocked"] is None
        result.extend(page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            return result


def test_public_original_substitutions_have_exact_human_machine_source_parity(public):
    before = public.to_dict()
    explorer = public.explore()
    human = explorer.answer("sequence_changes")
    machine = explorer.access.select("sequence_changes")
    assert (
        human.result_ref == machine.result_ref
        and len(human.items()) == machine.count == 8
    )
    assert human.result_ref == explorer.view("sequence_changes").result_ref
    wire = machine._scientific.wire
    assert (
        wire["native_payload"]["items"]
        == before["sections"]["features_positional"]["natural_variant"]["value"]
    )
    native = json.loads((DATA / "P60174.json").read_text(encoding="utf-8"))
    originals = [f for f in native["features"] if f["type"] == "Natural variant"]
    delivered = frames(machine, limit=1)
    assert [f["item_ref"] for f in delivered] == [
        item.item_ref for item in human.items()
    ]
    for item, frame, original in zip(human.items(), delivered, originals, strict=True):
        assert item.kind == frame["kind"] == "natural_variant"
        assert (
            item.cells["original"].value
            == original["alternativeSequence"]["originalSequence"]
        )
        assert (
            item.cells["alternatives"].value
            == original["alternativeSequence"]["alternativeSequences"]
        )
        assert item.cells["start"].value == original["location"]["start"]["value"]
        assert item.open().native_payload == item._entry.value["item"]
        assert item.open().back() is human
        assert (
            explorer.access._resolve(frame["payload_location"])[1]
            == item.payload_location
        )
        explanation = item.explain()
        assert explanation.back() is human and len(explanation.items()) == 1
        source = explanation.items()[0].open().native_payload
        assert source["normalized_value"] == item.open().native_payload
        assert source["source_metadata"]["uniprot_feature"] == original
        assert frame["support"]["source_assertions"][0]["id"] == source["id"]
        assert (
            explorer.access.explain(item.item_ref).page()["outcome"]["status"] == "ok"
        )
    assert public.to_dict() == before
    assert "Natural variants and mutagenesis" in repr(human)
    assert "clinical effect" in machine._scientific.wire["scope"]


def test_equal_positions_do_not_merge_natural_variants_and_mutagenesis():
    explorer = synthetic().explore()
    result = explorer.view("sequence_changes")
    assert {item.kind for item in result.items()} == {"natural_variant", "mutagenesis"}
    assert len({i.item_ref for i in result.items()}) == 2
    natural = result.filter("feature_type", equals="natural_variant")
    selected = explorer.access.select(
        "sequence_changes", where={"feature_type": "natural_variant"}
    )
    assert [i.item_ref for i in natural.items()] == [
        f["item_ref"] for f in frames(selected)
    ]
    assert len(natural._selection._entries) == 2
    assert (
        explorer.access.select(
            "sequence_changes", item_refs=[result.items()[1].item_ref]
        ).count
        == 1
    )
    assert result.item(result.items()[1].item_ref).open().back() is result


def test_original_duplicate_occurrences_keep_distinct_locations_and_refs():
    raw = synthetic([feature()]).to_dict()
    field = raw["sections"]["features_positional"]["natural_variant"]
    field["value"].append(deepcopy(field["value"][0]))
    result = Card.from_dict(raw).explore().view("sequence_changes")
    first, second = result.items()
    assert first.open().native_payload == second.open().native_payload
    assert (
        first.item_ref != second.item_ref
        and first.payload_location != second.payload_location
    )


@pytest.mark.parametrize(
    "missing,alternatives", [(True, None), (False, []), (None, None)]
)
def test_stated_deletion_false_and_unstated_are_distinct(missing, alternatives):
    raw = synthetic([feature()]).to_dict()
    value = raw["sections"]["features_positional"]["natural_variant"]["value"][0]
    value["substitution"] = {"original": "M"}
    if missing is not None:
        value["substitution"]["missing"] = missing
    if alternatives is not None:
        value["substitution"]["alternatives"] = alternatives
    explorer = Card.from_dict(raw).explore()
    item = explorer.view("sequence_changes").items()[0]
    assert item.cells["missing"].value is missing
    assert item.cells["missing"].state == ("unknown" if missing is None else "present")
    selected = explorer.access.select(
        "sequence_changes",
        fields=["missing", "alternatives"],
        where={"missing": missing},
    )
    delivered = frames(selected)[0]
    assert delivered["cells"]["missing"]["value"] is missing
    assert delivered["cells"]["alternatives"]["value"] == alternatives
    assert ("stated deletion" in repr(item._view)) is (missing is True)


@pytest.mark.parametrize(
    "column,operand",
    [
        ("start", True),
        ("start", 2.0),
        ("start", 0),
        ("missing", 1),
        ("alternatives", "A"),
        ("alternatives", [True]),
        ("unknown", "x"),
    ],
)
def test_invalid_typed_queries_fail_before_materialization(
    monkeypatch, column, operand
):
    explorer = synthetic().explore()
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_sequence_change_access"),
        "materialize",
        forbidden,
    )
    with pytest.raises(ArgumentError):
        explorer.access.select("sequence_changes", where={column: operand})


@pytest.mark.parametrize(
    "query",
    [
        {"fields": ["start", "start"]},
        {"fields": ["bogus"]},
        {"options": {"threshold": 0.1}},
        {"order_by": {"column": "alternatives"}},
        {"order_by": {"column": "start", "unit": "nm"}},
        {"item_refs": ["XI_foreign"]},
    ],
)
def test_unsupported_projection_order_options_and_foreign_membership(query):
    with pytest.raises(ArgumentError):
        synthetic().access().select("sequence_changes", **query)


def test_original_alternatives_are_one_typed_list_not_split_into_rows():
    explorer = synthetic([feature()]).explore()
    view = explorer.view("sequence_changes")
    assert len(view.items()) == 1
    selection = explorer.access.select(
        "sequence_changes", where={"alternatives": ["A", "G"]}
    )
    assert selection.count == 1
    assert (
        explorer.access.select(
            "sequence_changes", where={"alternatives": ["G", "A"]}
        ).count
        == 0
    )
    assert len(view.filter("alternatives", equals=["A", "G"]).items()) == 1
    assert "alternatives" not in view.capabilities["sort"]
    with pytest.raises(ArgumentError):
        view.sort("alternatives")


@pytest.mark.parametrize(
    "modifier,molecule",
    [("EXACT", None), ("LESS_THAN", None), ("UNKNOWN", None), ("EXACT", "P60174-2")],
)
def test_source_axis_and_uncertainty_reuse_original_structural_admission(
    modifier, molecule
):
    original = feature()
    original["location"]["start"]["modifier"] = modifier
    if molecule:
        original["molecule"] = molecule
    explorer = synthetic([original]).explore()
    item = explorer.view("sequence_changes").items()[0]
    links = item.related()
    assert links.back().back() is item._view
    question = links.filter("role", equals="question").items()[0]._entry.value
    expected = modifier == "EXACT" and molecule is None
    assert (question["annotation_context"]["state"] == "ready") is expected
    assert item.cells["context_state"].value == question["annotation_context"]["state"]
    if expected:
        assert question["annotation_context"]["request"]["options"]["region"] == [
            [2, 2]
        ]
    else:
        assert question["annotation_context"]["request"] is None


@pytest.mark.parametrize("mode", ["missing", "foreign", "mismatch", "conflict"])
def test_missing_wrong_subject_changed_values_and_conflicts_remain_visible(mode):
    raw = synthetic([feature()]).to_dict()
    field = raw["sections"]["features_positional"]["natural_variant"]
    ref = field["source_assertion_ids"][0]
    source = next(r for r in raw["source_assertion_store"] if r["id"] == ref)
    if mode == "missing":
        raw["source_assertion_store"].remove(source)
    elif mode == "foreign":
        source["subject_ref"] = "uniprot:P00000"
    elif mode == "mismatch":
        field["value"][0]["description"] = "synthetic modified normalized value"
    else:
        raw["quality"].setdefault("conflicts", []).append(
            {"field": "features_positional.natural_variant"}
        )
    result = Card.from_dict(raw).explore().view("sequence_changes")
    assert result.items()[0].cells["support_state"].value == (
        "retained" if mode == "conflict" else "partial"
    )
    assert result.items()[0].cells["context_state"].value != "ready"
    assert (
        result.coverage["conflicts"]
        if mode == "conflict"
        else result.items()[0].support[0]["state"] == "partial"
    )


def test_absent_retained_empty_and_malformed_fields_are_different():
    raw = synthetic([]).to_dict()
    explorer = Card.from_dict(raw).explore()
    missing = explorer.view("sequence_changes")
    assert not missing.items() and missing._status == "missing_prerequisite"
    raw["sections"].setdefault("features_positional", {}).update(
        natural_variant={"value": []}, mutagenesis={"value": []}
    )
    empty = Card.from_dict(raw).explore().view("sequence_changes")
    assert empty._status == "empty"
    raw["sections"]["features_positional"]["natural_variant"]["value"] = [
        "explicit malformed synthetic row"
    ]
    malformed = Card.from_dict(raw).explore().view("sequence_changes")
    assert malformed._status == "partial" and not malformed.items()
    assert malformed.coverage["gaps"][0]["state"] == "unrecognized_shape"


def test_atomic_budget_deferral_keeps_states_and_inspectable_originals():
    raw = synthetic([feature()]).to_dict()
    raw["sections"]["features_positional"]["natural_variant"]["value"][0][
        "description"
    ] = "synthetic large text " * 1000
    explorer = Card.from_dict(raw).explore()
    selection = explorer.access.select(
        "sequence_changes", fields=["description", "alternatives"]
    )
    page = selection.page(max_bytes=8000)
    item = page["items"][0]
    assert len(canonical_json(page).encode()) <= 8000
    assert item["value_included"] is False and item["inspection_required"] is True
    assert "interpretation" not in item and "support" not in item
    assert all(
        "value" not in cell and cell["value_included"] is False
        for cell in item["cells"].values()
    )


def test_detached_capture_and_escaped_human_presentation():
    card = synthetic()
    explorer = card.explore()
    before = explorer.view("sequence_changes").rows()
    card.sections["features_positional"]["natural_variant"]["value"].clear()
    result = explorer.view("sequence_changes")
    assert result.rows() == before and len(result.items()) == 2
    assert (
        "&lt;change&gt;" in result._repr_html_()
        and "synthetic <change>" not in result._repr_html_()
    )


def test_new_save_is_explicitly_unavailable_without_blocking_unrelated_literal(
    tmp_path,
):
    explorer = synthetic().explore()
    view = explorer.view("sequence_changes")
    selection = explorer.access.select("sequence_changes")
    assert not view.capabilities["save"] and not selection.capabilities["save"]
    for item in (
        view,
        view.items()[0].open(),
        view.items()[0].explain(),
        view.items()[0].related(),
        selection,
    ):
        with pytest.raises(StorageError):
            item.save(tmp_path / "unsupported.json")
    explorer.inspect("identifiers.uniprot").save(tmp_path / "literal.json")
    from sabueso import read_exploration

    restored = read_exploration(tmp_path / "literal.json")
    assert "sequence_changes" not in restored.explorer.capabilities["topics"]
    assert restored.explorer.access.select("sequence_changes").count == 0


def test_public_catalog_and_no_card_reconstruction_or_hidden_engines(
    public, monkeypatch
):
    explorer = public.explore()
    monkeypatch.setattr(Card, "__init__", forbidden)
    assert "sequence_changes" in explorer.capabilities["scientific_topics"]
    assert "sequence_changes" in explorer.access.capabilities["scientific_topics"]
    catalog = explorer.access.catalog()
    descriptor = explorer.access._resolve(catalog._target["location"])[0][
        "sequence_changes"
    ]
    assert (
        descriptor["save"] is False
        and descriptor["columns"]["alternatives"]["type"] == "array[string]|null"
    )
    result = materialize(explorer.access)
    assert result.wire["context"]["adapter"] == ADAPTER
    assert explorer.view("sequence_changes").result_ref == result.result_ref
    assert result.native["rule"]["rule"] == "sequence_change_projection@1"


@pytest.mark.parametrize(
    "column,value",
    [
        ("start", True),
        ("start", 2.0),
        ("original", {}),
        ("alternatives", [1]),
        ("missing", "false"),
        ("description", []),
    ],
)
def test_malformed_projected_values_keep_original_input_and_explicit_cell_state(
    column, value
):
    raw = synthetic([feature()]).to_dict()
    original = raw["sections"]["features_positional"]["natural_variant"]["value"][0]
    container = (
        original["location"]["sequence"]
        if column == "start"
        else original["substitution"]
        if column in ("original", "alternatives", "missing")
        else original
    )
    container[column] = value
    item = Card.from_dict(raw).explore().view("sequence_changes").items()[0]
    assert (
        item.cells[column].state == "unrecognized_shape"
        and item.cells[column].value is None
    )
    assert item.open().native_payload == original


def test_nonprotein_capture_does_not_advertise_sequence_changes():
    explorer = Card(meta={"entity_type": "small_molecule"}).explore()
    assert "sequence_changes" not in explorer.capabilities["topics"]
    assert "sequence_changes" not in explorer.access.capabilities["scientific_topics"]
    with pytest.raises(ArgumentError):
        explorer.access.select("sequence_changes")


def test_sorting_and_hidden_members_preserve_source_occurrence_identity(public):
    explorer = public.explore()
    all_items = explorer.view("sequence_changes")
    sorted_view = all_items.sort("start", descending=True)
    machine = explorer.access.select(
        "sequence_changes", order_by={"column": "start", "descending": True}
    )
    assert [i.item_ref for i in sorted_view.items()] == [
        f["item_ref"] for f in frames(machine)
    ]
    hidden = all_items.items()[0]
    filtered = sorted_view.filter("start", equals=999999)
    assert not filtered.items()
    assert (
        filtered.item(hidden.item_ref).open().native_payload
        == hidden.open().native_payload
    )
    assert filtered.back() is sorted_view and sorted_view.back() is all_items


def test_unrelated_annotation_gaps_do_not_change_this_explicit_scope():
    raw = synthetic([feature()]).to_dict()
    raw["sections"]["features_positional"]["natural_variant_other"] = {
        "value": ["unrelated malformed synthetic record"]
    }
    view = Card.from_dict(raw).explore().view("sequence_changes")
    assert view._status == "ok" and not view.coverage["gaps"]


def test_malformed_substitution_container_is_distinct_from_unstated_fields():
    raw = synthetic([feature()]).to_dict()
    row = raw["sections"]["features_positional"]["natural_variant"]["value"][0]
    row["substitution"] = ["synthetic malformed container"]
    item = Card.from_dict(raw).explore().view("sequence_changes").items()[0]
    assert all(
        item.cells[c].state == "unrecognized_shape"
        for c in ("original", "alternatives", "missing")
    )
    assert item.open().native_payload["substitution"] == row["substitution"]


def test_one_retained_value_preserves_multiple_native_contexts_without_unique_correspondence():
    first = feature()
    second = deepcopy(first)
    second["explicit_synthetic_source_context"] = "another original context"
    card = synthetic([first, second])
    field = card.get("features_positional.natural_variant")
    assert len(field["value"]) == 1 and len(field["source_assertion_ids"]) == 2
    explorer = card.explore()
    (item,) = explorer.view("sequence_changes").items()
    assert len(item.explain().items()) == 2
    assert [
        i.open().native_payload["asserted_value"] for i in item.explain().items()
    ] == [first, second]
    (delivered,) = frames(explorer.access.select("sequence_changes"))
    assert len(delivered["support"]["source_assertions"]) == 2
    assert (
        "without inventing unique feature correspondence"
        in delivered["interpretation"]["mapping_lineage"]
    )
