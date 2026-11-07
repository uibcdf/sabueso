"""Live measured-activity exploration over reviewed public ChEMBL originals."""

import socket
from copy import deepcopy
from pathlib import Path

import pytest
import pyunitwizard as puw
from pyunitwizard import QuantityRecord

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"
if not (DATA / "chembl/CHEMBL5834.json").is_file():
    DATA = Path.cwd() / "temp_data"
TOPIC = "bioactivities"
BTS = "chembl:CHEMBL1161789"
BENZ = "chembl:CHEMBL110"
DEFAULTS = {
    "include_indirect": False,
    "thresholds": None,
    "classification_rule": "bioactivity_class@4",
    "measurement_rule": "measurement_identity@1",
    "target_scope_rule": "bioactivity_target_scope@1",
}


def forbidden(*args, **kwargs):
    pytest.fail("A retained exploration must not query sources or repeat native work")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def public_original():
    card = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(FixtureUniProtClient(DATA)),
        chembl={},
        chembl_client=FixtureChEMBLClient(DATA),
    )[0]
    assert len(card.relationships(predicate="has_bioactivity")) == 493
    return card.to_dict()


@pytest.fixture
def card(public_original):
    return Card.from_dict(deepcopy(public_original))


def serialized_native(value):
    """Normalize native quantities independently of the exploration adapter."""
    if isinstance(value, dict):
        return {key: serialized_native(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [serialized_native(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    assert puw.is_quantity(value)
    number, unit = puw.get_value_and_unit(value)
    return {"value": float(number), "unit": str(unit)}


def frames(selection, **kwargs):
    cursor, result, seen = None, [], set()
    while True:
        page = selection.page(cursor=cursor, **kwargs)
        assert len(canonical_json(page).encode("utf-8")) <= kwargs.get(
            "max_bytes", 65536
        )
        result.extend(page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            return result
        assert cursor not in seen
        seen.add(cursor)


def molecule(view, ref):
    return next(
        item for item in view.items() if item.cells["molecule_ref"].value == ref
    )


def relationship(card, activity_id):
    return next(
        row
        for row in card.relationships(predicate="has_bioactivity")
        if row["qualifiers"]["activity_id"] == activity_id
    )


def add_synthetic_declared_copy(card, qualifiers, source, activity, target=BTS):
    qualifiers = deepcopy(qualifiers)
    qualifiers.update(
        source=source,
        activity_id=activity,
        parent_molecule=target,
        copy_of={"source": "ChEMBL", "activity_id": 24815542},
    )
    assertion = make_source_assertion(
        "relationships.has_bioactivity", qualifiers, source, activity, "2026-11-06"
    )
    card.source_assertion_store.add(assertion)
    return card.relationship_store.add(
        make_relationship(
            "uniprot:P52270", "has_bioactivity", target, qualifiers, [assertion["id"]]
        )
    )


def test_full_original_scope_and_independent_native_interpretation_are_preserved(card):
    before = card.to_dict()
    native = card.bioactivities()
    explorer = card.explore()
    human = explorer.view(TOPIC)
    selected = explorer.access.select(TOPIC)
    assert (
        human.result_ref
        == explorer.answer("measured_molecules").result_ref
        == selected.result_ref
    )
    assert human.native_payload == serialized_native(native)
    assert sum(row["record_count"] for row in native["items"]) == 493
    assert native["excluded"] == []
    assert human.native_payload["classification"]["rule"] == "bioactivity_class@4"
    assert selected.count == len(native["items"]) == len(human.items())
    assert {row["cells"]["molecule_ref"]["value"] for row in frames(selected)} == {
        item["molecule_ref"] for item in native["items"]
    }
    assert card.to_dict() == before


def test_bts_original_potency_context_and_exact_source_support(card):
    original = relationship(card, 24815542)
    native = card.explain_bioactivity(BTS)
    (measurement,) = native["item"]["measurements"]
    assert measurement["type"] == "IC50" and measurement["relation"] == "="
    assert measurement["value"] == 33000 and measurement["units"] == "nM"
    assert measurement["class"] == native["item"]["class"] == "weak"
    assert measurement["assay"] == "CHEMBL5138431"
    assert measurement["document"] == "CHEMBL5137001"
    assert puw.get_value(measurement["normalized"], to_unit="nanomolar") == 33000
    assert original["qualifiers"]["document"]["doi"] == "10.1016/j.bmc.2021.116577"
    assertions = [
        card.source_assertion_store.get(key) for key in original["source_assertion_ids"]
    ]
    assert {a["field_path"] for a in assertions} == {
        "relationships.has_bioactivity",
        "relationships.has_bioactivity.assay",
    }
    activity = next(
        a for a in assertions if a["field_path"] == "relationships.has_bioactivity"
    )
    assert activity["asserted_value"]["activity"]["activity_id"] == 24815542
    assert not any(
        a["source"]["record_id"] == "CHEMBL5137001"
        for a in card.source_assertion_store.to_list()
    )
    explorer = card.explore()
    groups = molecule(explorer.view(TOPIC), BTS).open()
    assert groups.native_payload == serialized_native(native)
    selected = explorer.access.select(TOPIC, options={"molecule_ref": BTS})
    assert selected.result_ref == groups.result_ref and selected.count == 1
    assert {
        row["id"] for row in frames(selected)[0]["support"]["source_assertions"]
    } == set(original["source_assertion_ids"])


def test_molecule_group_record_navigation_retains_context_and_back(card):
    explorer = card.explore()
    root = explorer.view(TOPIC)
    bts = molecule(root, BTS)
    groups = bts.open()
    assert groups.back() is root and bts.back() is root
    group = groups.items()[0]
    group_ref = group.cells["measurement_ref"].value
    records = group.open()
    assert records.back() is groups
    assert records.native_payload == serialized_native(
        card.explain_measurement(group_ref)
    )
    record = records.items()[0]
    original = relationship(card, 24815542)
    assert record.cells["relationship_id"].value == original["id"]
    detail = record.open()
    assert detail.back() is records
    assert detail.native_payload["relationship"] == original
    assert "10.1016/j.bmc.2021.116577" in str(detail)
    related = record.related()
    assert related.back() is records
    assert {"assay_context", "citation_context", "original_relationship", "source"} <= {
        link.cells["role"].value for link in related.items()
    }
    for link in related.items():
        opened = link.open()
        assert opened.back() is related
        assert opened.outcome["status"] in {"ok", "empty"}
    assert record.explain().back() is records


def test_benznidazole_keeps_percentage_and_unknown_without_inferred_dose(card):
    native = card.explain_bioactivity(BENZ)
    measurements = {row["activity_id"]: row for row in native["item"]["measurements"]}
    observed, unknown = measurements[5108414], measurements[5108641]
    assert observed["value"] == 18 and observed["units"] == "%"
    assert observed["class"] == "inconclusive"
    assert observed["test_concentration_state"] == "not_interpreted"
    assert "test_concentration" not in observed
    assert unknown["value"] is None and unknown["normalized"] is None
    assert unknown["class"] == "not_determined"
    explorer = card.explore()
    benz = molecule(explorer.view(TOPIC), BENZ)
    assert benz.cells["measurement"].state == "not_applicable"
    assert benz.cells["measurement_ref"].state == "not_applicable"
    aggregate = frames(
        explorer.access.select(
            TOPIC, fields=["measurement"], where={"molecule_ref": BENZ}
        )
    )[0]["cells"]["measurement"]
    assert aggregate["state"] == "not_applicable" and aggregate["value"] is None
    groups = benz.open()
    assert groups.native_payload == serialized_native(native)
    unknown_group = next(
        item for item in groups.items() if item.cells["measurement"].value is None
    )
    assert unknown_group.cells["measurement"].state == "unknown"
    record = unknown_group.open().items()[0]
    assert record.cells["measurement"].state == "unknown"
    selected = explorer.access.select(
        TOPIC,
        fields=["measurement"],
        options={
            "molecule_ref": BENZ,
            "measurement_ref": unknown_group.cells["measurement_ref"].value,
        },
    )
    cell = frames(selected)[0]["cells"]["measurement"]
    assert cell["state"] == "unknown" and cell["value"] is None


def test_publication_context_keeps_all_459_links_outside_two_selected_records(
    card, monkeypatch
):
    expected = serialized_native(card.explain_literature("pubmed:20889239"))
    assert len(expected["links"]) == 459
    original, calls = Card.explain_literature, []

    def counted(captured, ref, *args, **kwargs):
        calls.append(ref)
        return original(captured, ref, *args, **kwargs)

    monkeypatch.setattr(Card, "explain_literature", counted)
    root = card.explore().view(TOPIC)
    groups = molecule(root, BENZ).open()
    assert groups.native_payload["item"]["record_count"] == 2
    record = groups.items()[0].open().items()[0]
    related = record.related()
    link = next(
        item
        for item in related.items()
        if item.cells["role"].value == "publication_context"
    )
    opened = link.open()
    assert opened.native_payload == expected and opened.back() is related
    assert link.open().native_payload == expected
    assert calls == ["pubmed:20889239"]


@pytest.mark.parametrize("first", ["human", "agent"])
def test_exact_requests_share_one_detached_native_capture(card, monkeypatch, first):
    expected = serialized_native(card.bioactivities())
    original, calls = Card.bioactivities, []

    def counted(captured, *args, **kwargs):
        calls.append(captured)
        return original(captured, *args, **kwargs)

    monkeypatch.setattr(Card, "bioactivities", counted)
    explorer = card.explore()
    card.relationship_store.store.clear()
    if first == "human":
        explorer.answer("measured_molecules")
    else:
        explorer.access.select(TOPIC)
    human = explorer.view(TOPIC)
    selected = explorer.access.select(TOPIC, options=DEFAULTS)
    assert len(calls) == 1 and calls[0] is not card
    assert human.native_payload == expected and human.result_ref == selected.result_ref
    returned = human.native_payload
    returned["items"].clear()
    assert human.native_payload == expected
    explorer.access.select(TOPIC, options={"include_indirect": True})
    assert len(calls) == 2
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    assert explorer.access.select(TOPIC).result_ref == selected.result_ref


@pytest.mark.parametrize(
    "query",
    [
        {"where": {"record_count": True}},
        {"where": {"molecule_ref": 1}},
        {"where": {"missing": "weak"}},
        {"where": {"measurement": 33000}},
        {"where": {"measurement": {"value": 1, "unit": "angstrom"}}},
        {"fields": ["class", "class"]},
        {"fields": ["missing"]},
        {"options": {"include_indirect": 1}},
        {"options": {"thresholds": {"active_max": 10}}},
        {"options": {"guess_target": True}},
        {"order_by": {"column": "record_count", "descending": 1}},
        {"order_by": {"column": "measurement"}},
        {"item_refs": ["XI_" + "0" * 64]},
    ],
)
def test_invalid_selection_is_rejected_before_native_work(card, query, monkeypatch):
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    monkeypatch.setattr(Card, "explain_bioactivity", forbidden)
    monkeypatch.setattr(Card, "explain_measurement", forbidden)
    with pytest.raises(ArgumentError):
        card.access().select(TOPIC, skip_digestion=True, **query)


def test_projection_filter_membership_and_empty_selection_preserve_native_scope(card):
    explorer = card.explore()
    full = explorer.view(TOPIC)
    bts = molecule(full, BTS)
    selected = explorer.access.select(
        TOPIC,
        fields=["molecule_ref", "class"],
        where={"molecule_ref": BTS},
        item_refs=[bts.item_ref],
        order_by={"column": "molecule_ref"},
    )
    (frame,) = frames(selected)
    assert frame["item_ref"] == bts.item_ref
    assert set(frame["cells"]) == {"molecule_ref", "class"}
    assert frame["interpretation"] and frame["support"]
    assert selected.result_ref == full.result_ref
    human = full.filter("molecule_ref", equals=BTS).sort("molecule_ref")
    assert [item.item_ref for item in human.items()] == [frame["item_ref"]]
    empty = explorer.access.select(
        TOPIC, fields=[], where={"molecule_ref": "chembl:ABSENT"}
    )
    assert empty.count == 0 and empty.result_ref == full.result_ref
    assert empty.page()["outcome"] == explorer.access.select(TOPIC).page()["outcome"]
    assert full.native_payload["items"] and full.native_payload["excluded"] == []
    with pytest.raises(ArgumentError):
        explorer.access.select(TOPIC, item_refs=["XI_" + "0" * 64])


def test_paging_is_bounded_ordered_and_cursors_belong_to_the_selection(card):
    explorer = card.explore()
    selected = explorer.access.select(TOPIC, fields=["molecule_ref"])
    collected = frames(selected, limit=3, max_bytes=8192)
    assert len(collected) == selected.count
    assert len({row["item_ref"] for row in collected}) == selected.count
    assert [row["item_ref"] for row in collected] == [
        item.item_ref for item in explorer.view(TOPIC).items()
    ]
    first = selected.page(limit=1)
    foreign = explorer.access.select(TOPIC, fields=[])
    with pytest.raises(ArgumentError):
        foreign.page(cursor=first["page"]["next_cursor"])


def test_quantities_keep_units_and_do_not_sort_percent_as_potency(card):
    explorer = card.explore()
    options = {"molecule_ref": BTS}
    selected = explorer.access.select(
        TOPIC,
        options=options,
        where={"measurement": {"value": 33, "unit": "micromolar"}},
        order_by={"column": "measurement", "unit": "nanomolar"},
    )
    assert selected.count == 1
    quantity = QuantityRecord.from_dict(
        frames(selected)[0]["cells"]["measurement"]["value"]
    ).to_quantity(
        field="relationships.has_bioactivity.measurement.normalized",
        unit="nanomolar",
        form="pint",
    )
    assert puw.get_value(quantity, to_unit="nanomolar") == 33000
    human = explorer.view(TOPIC, options=options)
    assert (
        puw.get_value(human.items()[0].cells["measurement"].value, to_unit="nanomolar")
        == 33000
    )
    assert human.filter(
        "measurement", equals=puw.quantity(33, "micromolar", form="pint")
    ).items()
    with pytest.raises(ArgumentError):
        explorer.access.select(
            TOPIC,
            options={"molecule_ref": BENZ},
            order_by={"column": "measurement", "unit": "nanomolar"},
        )


def test_machine_quantity_predicates_use_the_same_candidate_subset_as_human_filters(
    card,
):
    explorer = card.explore()
    root = explorer.view(TOPIC)
    native = root.native_payload
    units = {
        str(puw.get_unit(item.cells["measurement"].value))
        for item in root.items()
        if item.cells["measurement"].value is not None
    }
    assert {"nanomolar", "percent"} <= units
    quantity = {"value": 33, "unit": "micromolar"}
    human = root.filter("molecule_ref", equals=BTS).filter(
        "measurement", equals=quantity
    )
    (item,) = human.items()
    selections = (
        explorer.access.select(
            TOPIC, where={"molecule_ref": BTS, "measurement": quantity}
        ),
        explorer.access.select(
            TOPIC, item_refs=[item.item_ref], where={"measurement": quantity}
        ),
    )
    for selected in selections:
        assert selected.count == 1 and selected.result_ref == root.result_ref
        assert [frame["item_ref"] for frame in frames(selected)] == [item.item_ref]
    assert human.native_payload == root.native_payload == native


def test_mixed_percentage_and_concentration_rows_require_separate_dimensions(card):
    # Explicit synthetic pairing: this is not a claim about the original molecule.
    qualifiers = deepcopy(relationship(card, 5108414)["qualifiers"])
    qualifiers.update(activity_id="synthetic-mixed-unit", parent_molecule=BTS)
    assertion = make_source_assertion(
        "relationships.has_bioactivity",
        qualifiers,
        "ChEMBL",
        "synthetic-mixed-unit",
        "2026-11-06",
    )
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(
        make_relationship(
            "uniprot:P52270", "has_bioactivity", BTS, qualifiers, [assertion["id"]]
        )
    )
    explorer = card.explore()
    options = {"molecule_ref": BTS}
    view = explorer.view(TOPIC, options=options)
    assert {
        str(puw.get_unit(item.cells["measurement"].value)) for item in view.items()
    } == {"nanomolar", "percent"}
    with pytest.raises(ArgumentError):
        view.sort("measurement", unit="nanomolar")
    with pytest.raises(ArgumentError):
        explorer.access.select(
            TOPIC,
            options=options,
            where={"measurement": {"value": 33, "unit": "micromolar"}},
        )


def test_explicit_indirect_scope_keeps_original_exclusions_and_full_context(card):
    # Deliberate synthetic assignment change; the public original stays fixed.
    relationship(card, 24815542)["qualifiers"]["assay"]["relationship_type"] = "H"
    before = card.to_dict()
    narrow_native = card.bioactivities()
    wide_native = card.bioactivities(include_indirect=True)
    explorer = card.explore()
    narrow = explorer.view(TOPIC)
    wide = explorer.view(TOPIC, options={"include_indirect": True})
    assert narrow.native_payload == serialized_native(narrow_native)
    assert wide.native_payload == serialized_native(wide_native)
    assert {row["activity_id"] for row in narrow.native_payload["excluded"]} == {
        24815542
    }
    assert sum(row["record_count"] for row in narrow.native_payload["items"]) == 492
    assert sum(row["record_count"] for row in wide.native_payload["items"]) == 493
    assert card.to_dict() == before


def test_declared_copy_adds_a_record_without_an_independent_measurement_vote(card):
    original = relationship(card, 24815542)
    qualifiers = deepcopy(original["qualifiers"])
    qualifiers.update(
        source="PubChem",
        activity_id="explicit-synthetic-copy",
        copy_of={"source": "ChEMBL", "activity_id": 24815542},
    )
    assertion = make_source_assertion(
        "relationships.has_bioactivity",
        qualifiers,
        "PubChem",
        "explicit-synthetic-copy",
        "2026-11-06",
    )
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(
        make_relationship(
            "uniprot:P52270", "has_bioactivity", BTS, qualifiers, [assertion["id"]]
        )
    )
    options = {"molecule_ref": BTS, "measurement_rule": "measurement_identity@2"}
    native = card.explain_bioactivity(BTS, measurement_rule="measurement_identity@2")
    groups = card.explore().view(TOPIC, options=options)
    assert groups.native_payload == serialized_native(native)
    assert (
        native["item"]["record_count"] == 2 and native["item"]["measurement_count"] == 1
    )
    assert native["item"]["independence_status"] == "not_established"
    assert native["groups"][0]["voters"] == [original["id"]]


@pytest.mark.parametrize(
    "context,state",
    [("missing", "unknown"), ("same", "present"), ("different", "not_applicable")],
)
def test_aggregate_context_does_not_turn_missing_members_into_known_ids(
    card, context, state
):
    # Synthetic copies isolate context completeness without changing the potency.
    qualifiers = deepcopy(relationship(card, 24815542)["qualifiers"])
    if context == "missing":
        qualifiers["assay"]["id"] = None
        qualifiers["document"] = {}
    elif context == "different":
        qualifiers["assay"]["id"] = "synthetic:other-assay"
        qualifiers["document"] = {"id": "synthetic:other-document"}
    add_synthetic_declared_copy(
        card, qualifiers, "PubChem", "synthetic-context-" + context
    )
    before = card.to_dict()
    native = card.explain_bioactivity(BTS)
    assert (
        native["item"]["record_count"] == 2 and native["item"]["measurement_count"] == 1
    )
    explorer = card.explore()
    item = molecule(explorer.view(TOPIC), BTS)
    group = item.open().items()[0]
    for options, human in (({}, item), ({"molecule_ref": BTS}, group)):
        selected = explorer.access.select(
            TOPIC,
            options=options,
            fields=["assay_ref", "document_ref"],
            where={"molecule_ref": BTS},
        )
        cells = frames(selected)[0]["cells"]
        for column, known in (
            ("assay_ref", "CHEMBL5138431"),
            ("document_ref", "CHEMBL5137001"),
        ):
            value = known if context == "same" else None
            assert human.cells[column].state == cells[column]["state"] == state
            assert human.cells[column].value == cells[column]["value"] == value
    assert item.open().native_payload == serialized_native(native)
    assert card.to_dict() == before


def test_group_drill_down_keeps_broader_context_outside_selected_molecule_and_scope(
    card,
):
    # Explicit copy-family controls do not assert real cross-molecule activity.
    original = relationship(card, 24815542)
    indirect = deepcopy(original["qualifiers"])
    indirect["assay"]["relationship_type"] = "H"
    indirect_id = add_synthetic_declared_copy(
        card, indirect, "PubChem", "synthetic-indirect-copy"
    )
    foreign_id = add_synthetic_declared_copy(
        card,
        original["qualifiers"],
        "BindingDB",
        "synthetic-foreign-molecule-copy",
        target=BENZ,
    )
    before = card.to_dict()
    full = card.explain_measurement(original["id"])
    family = {original["id"], indirect_id, foreign_id}
    assert {record["relationship"]["id"] for record in full["records"]} == family
    explorer = card.explore()
    for focus in (full["group"]["id"], original["id"]):
        expected_native = serialized_native(card.explain_measurement(focus))
        for include_indirect in (False, True):
            options = {
                "molecule_ref": BTS,
                "measurement_ref": focus,
                "include_indirect": include_indirect,
            }
            expected_rows = (
                {original["id"], indirect_id} if include_indirect else {original["id"]}
            )
            human = explorer.view(TOPIC, options=options)
            assert human.native_payload == expected_native
            assert {
                item.cells["relationship_id"].value for item in human.items()
            } == expected_rows
            assert {item.cells["molecule_ref"].value for item in human.items()} == {BTS}
            selected = explorer.access.select(
                TOPIC, fields=["relationship_id", "molecule_ref"], options=options
            )
            assert selected.result_ref == human.result_ref
            assert {
                frame["cells"]["relationship_id"]["value"] for frame in frames(selected)
            } == expected_rows
            membership = human.context["focus_membership"]
            assert set(membership["included_relationship_ids"]) == expected_rows
            assert (
                set(membership["context_only_relationship_ids"])
                == family - expected_rows
            )
            assert foreign_id in membership["context_only_relationship_ids"]
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "status,expected",
    [(None, "not_queried"), ("error", "unavailable"), ("added", "empty")],
)
def test_unrequested_failed_and_scoped_empty_remain_distinct(card, status, expected):
    card.relationship_store.store.clear()
    card.quality["enrichments"] = (
        []
        if status is None
        else [
            {
                "source": "ChEMBL",
                "identifier": "CHEMBL5834",
                "status": status,
                "count": 0,
                "detail": "Explicit synthetic coverage control",
            }
        ]
    )
    before = card.to_dict()
    view = card.explore().view(TOPIC)
    assert view.outcome["status"] == expected and not view.items()
    assert card.to_dict() == before
    with pytest.raises(ArgumentError):
        card.access().select(TOPIC, where={"unrecognized": "x"})


def test_uncertain_source_coverage_with_retained_rows_stays_filterable(card):
    card.quality["enrichments"] = [
        {
            "source": "ChEMBL",
            "identifier": "CHEMBL5834",
            "status": "error",
            "detail": "Explicit synthetic failed later request; original records remain retained",
        }
    ]
    view = card.explore().view(TOPIC)
    assert view.outcome["status"] == "partial" and view.items()
    selected = view.filter("molecule_ref", equals=BTS)
    assert len(selected.items()) == 1 and selected.outcome == view.outcome
    assert selected.native_payload == view.native_payload


@pytest.mark.parametrize(
    "change", ["missing_pin", "conflicting_identity", "foreign_relationship"]
)
def test_incoherent_identity_never_invokes_unscoped_reader_and_filter_refuses(
    card, change, monkeypatch
):
    if change == "missing_pin":
        card.meta.pop("card_id", None)
    elif change == "conflicting_identity":
        card.meta["card_id"] = "sabueso:protein:uniprot:P60174"
    else:
        relationship(card, 24815542)["subject_ref"] = "uniprot:P60174"
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    monkeypatch.setattr(Card, "explain_bioactivity", forbidden)
    monkeypatch.setattr(Card, "explain_measurement", forbidden)
    view = card.explore().view(TOPIC)
    assert view.outcome["status"] == "missing_prerequisite" and not view.items()
    with pytest.raises(ArgumentError):
        view.filter("class", equals="weak")
    with pytest.raises(ArgumentError):
        view.filter("unrecognized", equals=True)


def test_labels_and_source_text_are_escaped_in_html(card):
    marker = '<script>alert("synthetic source text")</script>'
    relationship(card, 24815542)["qualifiers"]["molecule_name"] = marker
    before = card.to_dict()
    full = card.explore().view(TOPIC)
    original_native = full.native_payload
    selected = full.filter("molecule_ref", equals=BTS)
    assert len(selected.items()) == 1 and selected.items()[0].label == marker
    assert marker in str(selected)
    html = selected._repr_html_()
    assert marker not in html and "&lt;script&gt;" in html
    assert selected.native_payload == full.native_payload == original_native
    assert card.to_dict() == before


def test_live_bioactivity_saving_uses_independent_saved_handshake(card, tmp_path):
    before = card.to_dict()
    explorer = card.explore()
    options = {"molecule_ref": BTS}
    human = explorer.view(TOPIC, options=options)
    records = human.items()[0].open()
    record_ref = records.items()[0].item_ref
    hidden = records.filter("relationship_id", equals="synthetic:absent")
    assert not hidden.items()
    explicit = hidden.item(record_ref)
    detail = explicit.open()
    explicit.explain()
    explicit.related()
    selected = explorer.access.select(TOPIC, options=options)
    assert selected.count == 1
    assert human.capabilities["save"] and selected.capabilities["save"]
    path = tmp_path / "bts-groups.json"
    receipt = selected.save(path)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert saved.capabilities["save"]
    assert saved.native_payload == human.native_payload
    reopened_records = saved.items()[0].open()
    reopened_hidden = reopened_records.filter(
        "relationship_id", equals="synthetic:absent"
    )
    reopened = reopened_hidden.item(record_ref)
    assert reopened.open().native_payload == detail.native_payload
    assert reopened.related().back().view_ref == reopened_hidden.view_ref
    again = tmp_path / "hidden-record.json"
    reopened.open().save(again)
    assert sabueso.read_exploration(again).native_payload == detail.native_payload
    restored = saved.explorer.access.select(TOPIC, options=options)
    assert restored.capabilities["save"]
    assert restored.result_ref == selected.result_ref == human.result_ref
    assert restored.selection_ref == selected.selection_ref

    def semantic_frame(access, value):
        if isinstance(value, dict):
            if (
                set(value) == {"format", "kind", "location_ref"}
                and value["format"] == "card_access_location@1"
                and value["kind"] == "lookup"
            ):
                _, location = access._resolve(value)
                # Session-owned lookup handles differ; their exact targets must read.
                access.read(value).page(limit=1)
                return location
            return {key: semantic_frame(access, item) for key, item in value.items()}
        if isinstance(value, list):
            return [semantic_frame(access, item) for item in value]
        return value

    assert semantic_frame(
        saved.explorer.access, restored.page()["items"]
    ) == semantic_frame(explorer.access, selected.page()["items"])
    with pytest.raises(StorageError):
        sabueso.read_exploration(path, expected_digest="sha256:" + "0" * 64)
    assert card.to_dict() == before
