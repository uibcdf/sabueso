"""LIVE molecule activity context over complete reviewed public target inputs."""

import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest
import pyunitwizard as puw
from pyunitwizard import QuantityRecord

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.core.measurements import record_source
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.card.small_molecule import build_molecule_cards
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.rcsb import FixtureRCSBClient

DATA = Path.cwd() / "temp_data"
if not (DATA / "chembl/CHEMBL5834.json").is_file():
    parents = Path(__file__).resolve().parents
    if len(parents) > 2:
        DATA = parents[2] / "temp_data"
TOPIC = "activity_context"
ADAPTER = "molecule_activity_context_exploration@1"
BTS, BENZ = "chembl:CHEMBL1161789", "chembl:CHEMBL110"
BTS_PAPER, BENZ_PAPER = "pubmed:35189560", "pubmed:20889239"
QUANTITY_FIELD = "relationships.has_bioactivity.measurement.normalized"
DEFAULTS = {
    "include_indirect": False,
    "thresholds": None,
    "classification_rule": "bioactivity_class@4",
    "measurement_rule": "measurement_identity@1",
    "target_scope_rule": "bioactivity_target_scope@1",
    "target_card_ref": None,
    "molecule_ref": None,
    "measurement_ref": None,
}


def forbidden(*args, **kwargs):
    pytest.fail(
        "Captured activity context cannot acquire sources or repeat forbidden native work"
    )


def serialized_native(value):
    """Serialize real quantities, preserving primitive source strings and types."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, dict):
        return {key: serialized_native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialized_native(item) for item in value]
    assert puw.is_quantity(value)
    number, unit = puw.get_value_and_unit(value)
    return {"value": float(number), "unit": str(unit)}


@pytest.fixture(scope="module")
def public_originals():
    """Prepare public inputs and independent native oracles exactly once."""
    with pytest.MonkeyPatch.context() as guard:
        guard.setattr(socket.socket, "connect", forbidden)
        guard.setattr(socket, "create_connection", forbidden)
        chembl = FixtureChEMBLClient(DATA)
        target = sabueso.resolve(
            "P52270",
            resolver=EntityResolver(
                FixtureUniProtClient(DATA), rcsb_client=FixtureRCSBClient(DATA)
            ),
            structures=["1SUX"],
            chembl={},
            chembl_client=chembl,
        )[0]
        unqueried = sabueso.resolve(
            "P52270", resolver=EntityResolver(FixtureUniProtClient(DATA))
        )[0]
        with pytest.warns(EnrichmentFailedWarning):
            failed = sabueso.resolve(
                "P52270",
                resolver=EntityResolver(FixtureUniProtClient(DATA)),
                chembl={},
                chembl_client=FixtureChEMBLClient(DATA, failing={"CHEMBL5834"}),
            )[0]

        class SyntheticEmptyClient(FixtureChEMBLClient):
            """Explicit synthetic successful-empty query, not a public source claim."""

            def bioactivities(self, target, limit=5000):
                return {
                    "query": {"target_chembl_id": target, "limit": limit},
                    "version": "synthetic-empty-control",
                    "retrieved_at": "synthetic fixture",
                    "total_count": 0,
                    "truncated": False,
                    "activities": [],
                    "assays": {},
                }

        empty = sabueso.resolve(
            "P52270",
            resolver=EntityResolver(FixtureUniProtClient(DATA)),
            chembl={},
            chembl_client=SyntheticEmptyClient(DATA),
        )[0]
        molecules, unanchored = build_molecule_cards(
            chembl=chembl.molecules(["CHEMBL1161789", "CHEMBL110"]),
            ccd=FixtureCCDClient(DATA).components(["BTS"]),
        )
        assert not unanchored and len(molecules) == 2
        bts = molecules["XBNHRNFODJOFRU-UHFFFAOYSA-N"]
        benz = molecules["CULUWZNBISUWAS-UHFFFAOYSA-N"]
        assert len(target.relationships("has_bioactivity")) == 493
        native = {"overview": serialized_native(target.bioactivities())}
        native["indirect_overview"] = serialized_native(
            target.bioactivities(include_indirect=True)
        )
        native["optin_overview"] = serialized_native(
            target.bioactivities(
                measurement_rule="measurement_identity@2",
                target_scope_rule="bioactivity_target_scope@2",
            )
        )
        native["molecules"] = {
            ref: serialized_native(target.explain_bioactivity(ref))
            for ref in (BTS, BENZ)
        }
        native["measurements"] = {
            row["group"]: serialized_native(target.explain_measurement(row["group"]))
            for original in native["molecules"].values()
            for row in original["item"]["measurements"]
        }
        native["publications"] = {
            ref: serialized_native(target.explain_literature(ref))
            for ref in (BTS_PAPER, BENZ_PAPER)
        }
        deck = Deck([bts, benz])
        native["ligands"] = serialized_native(target.ligands(deck))
        native["ligand_explanations"] = {
            name: serialized_native(target.explain_ligand(card.id, deck))
            for name, card in (("bts", bts), ("benz", benz))
        }
    return {
        "cards": {
            name: card.to_dict()
            for name, card in (
                ("target", target),
                ("bts", bts),
                ("benz", benz),
                ("unqueried", unqueried),
                ("failed", failed),
                ("empty", empty),
            )
        },
        "native": native,
    }


@pytest.fixture(autouse=True)
def retained_only(public_originals, monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    for client in (
        FixtureUniProtClient,
        FixtureChEMBLClient,
        FixtureCCDClient,
        FixtureRCSBClient,
    ):
        monkeypatch.setattr(client, "__init__", forbidden)
    monkeypatch.setattr(sabueso, "resolve", forbidden)
    monkeypatch.setattr(sabueso, "refresh_card", forbidden)


def restored(public, name):
    return Card.from_dict(deepcopy(public["cards"][name]))


def synthetic_alias(card, ref, *, anchor=None):
    """Declare a synthetic identity-control edge, never a real chemical claim."""
    anchor = anchor or card.id.split(":", 2)[2]
    value = {
        "record_ref": ref,
        "anchor": anchor,
        "synthetic_control": [False, 0, 0.0, None],
    }
    assertion = make_source_assertion(
        "relationships.same_as",
        value,
        "Synthetic identity control",
        ref,
        "synthetic fixture",
        subject_ref=ref,
    )
    card.source_assertion_store.add(assertion)
    rel = make_relationship(ref, "same_as", anchor, value, [assertion["id"]])
    card.relationship_store.add(rel)
    return assertion, rel


@pytest.fixture
def pair(public_originals):
    return restored(public_originals, "bts"), restored(public_originals, "target")


def test_complete_native_context_and_explicit_identity_are_retained(
    public_originals, pair
):
    molecule, target = pair
    before = molecule.to_dict(), target.to_dict()
    explorer = molecule.explore(related_cards=[target])
    view = explorer.answer("measured_targets")
    assert view.request == {
        "question": "measured_targets",
        "topic": TOPIC,
        "options": DEFAULTS,
    }
    assert view.context["card_ref"] == molecule.pinned_ref()
    assert view.context["molecule_card_ref"] == molecule.pinned_ref()
    assert len(view.items()) == 1
    row = view.items()[0]
    assert row.cells["target_card_ref"].value == target.pinned_ref()
    assert row.cells["class"].value == "weak"
    assert puw.get_value(row.cells["measurement"].value, to_unit="nanomolar") == 33000
    native = view.native_payload
    assert (
        native["targets"][target.pinned_ref()]["overview"]["wire"]["native_payload"]
        == public_originals["native"]["overview"]
    )
    assert {edge["record_ref"] for edge in native["identity"]["focal_edges"]} == {
        BTS,
        "pdb.ligand:BTS",
    }
    assert row.support[0]["identity_edges"]
    assert before == (molecule.to_dict(), target.to_dict())


@pytest.mark.parametrize(
    "molecule_name,paper,count", [("bts", BTS_PAPER, 9), ("benz", BENZ_PAPER, 459)]
)
def test_group_record_source_assay_full_publication_and_exact_back(
    public_originals, molecule_name, paper, count
):
    molecule = restored(public_originals, molecule_name)
    target = restored(public_originals, "target")
    explorer = molecule.explore(related_cards=[target])
    root = explorer.answer("measured_targets")
    groups = root.items()[0].open()
    assert groups.context["grain"] == "group"
    records = groups.items()[0].open()
    assert records.context["grain"] == "record"
    assert records.back().view_ref == groups.view_ref
    assert groups.back().view_ref == root.view_ref
    record = records.items()[0]
    assert record.open().native_payload == record._entry.value["item"]
    related = record.related()
    roles = {item._entry.value["role"] for item in related.items()}
    assert {
        "source",
        "assay_context",
        "citation_context",
        "publication_context",
        "identity_context",
        "molecule_root",
    } <= roles
    for role in ("source", "assay_context", "citation_context", "identity_context"):
        opened = next(
            item for item in related.items() if item._entry.value["role"] == role
        ).open()
        assert opened.explorer.access.context["card_ref"] == molecule.pinned_ref()
        assert opened.back().view_ref == related.view_ref
    publication = next(
        item
        for item in related.items()
        if item._entry.value["role"] == "publication_context" and paper in item.label
    ).open()
    assert (
        publication.native_payload == public_originals["native"]["publications"][paper]
    )
    assert len(publication.native_payload["links"]) == count
    assert publication.context["target_card_ref"] == target.pinned_ref()
    assert publication.explorer.context["card_ref"] == molecule.pinned_ref()
    assert publication.back().view_ref == related.view_ref
    assert (
        next(
            item
            for item in related.items()
            if item._entry.value["role"] == "molecule_root"
        )
        .open()
        .view_ref
        == root.view_ref
    )


def test_human_machine_projection_quantities_and_saved_roundtrip(pair, tmp_path):
    molecule, target = pair
    explorer = molecule.explore(related_cards=[target])
    human = explorer.view(TOPIC)
    machine = explorer.access.select(TOPIC)
    assert machine.result_ref == human.result_ref
    page = machine.page(max_bytes=65536)
    assert page["items"][0]["item_ref"] == human.items()[0].item_ref
    quantity = page["items"][0]["cells"]["measurement"]["value"]
    decoded = QuantityRecord.from_dict(quantity).to_quantity(
        field=QUANTITY_FIELD, unit="nanomolar", form="pint"
    )
    assert puw.get_value(decoded, to_unit="nanomolar") == 33000
    assert quantity["manifest"]["unit"] == "nanomolar"
    assert human.capabilities["save"] and machine.capabilities["save"]
    assert next(
        entry.value
        for entry in explorer.access.catalog()._entries
        if entry.key == TOPIC
    )["save"]
    path = tmp_path / "molecule-activity.json"
    with pytest.MonkeyPatch.context() as guard:
        for name in (
            "__init__",
            "from_dict",
            "bioactivities",
            "explain_bioactivity",
            "explain_measurement",
            "ligands",
            "explain_ligand",
            "literature",
            "explain_literature",
            "knowledge_state",
        ):
            guard.setattr(Card, name, forbidden)
        guard.setattr(Deck, "__init__", forbidden)
        human.save(path)
        saved = sabueso.read_exploration(path)
        assert saved.result_ref == human.result_ref
        assert saved.native_payload == human.native_payload
        assert saved.capabilities["save"]
        assert (
            saved.explorer.topics().native_payload[TOPIC]["availability"] == "retained"
        )
        assert (
            saved.explorer.access.select(TOPIC).selection_ref == machine.selection_ref
        )
        links = saved.items()[0].related()
        unvisited = next(
            item
            for item in links.items()
            if item._entry.value["role"] == "native_ligand_crossing"
        )
        assert unvisited.open().outcome["status"] == "not_saved"


@pytest.mark.parametrize(
    "case,status",
    [
        (None, "missing_prerequisite"),
        ("unqueried", "not_queried"),
        ("failed", "unavailable"),
    ],
)
def test_missing_unqueried_and_failed_context_are_not_inactivity(
    public_originals, case, status
):
    molecule = restored(public_originals, "bts")
    supplied = [] if case is None else [restored(public_originals, case)]
    explorer = molecule.explore(related_cards=supplied)
    view = explorer.view(TOPIC)
    assert view.outcome["status"] == status
    assert explorer.access.select(TOPIC).page()["outcome"]["status"] == status
    if supplied:
        item = view.items()[0]
        assert item.cells["record_count"].value is None
        assert item.cells["measurement"].state == "not_evaluated"
        assert item.cells["measurement"].state == "not_evaluated"
        empty = view.filter("label", equals="No matching display label")
        assert empty.outcome == view.outcome and not empty.items()
        assert empty.native_payload == view.native_payload
    else:
        with pytest.raises(ArgumentError, match="no retained rows"):
            view.filter("label", equals="x")


def test_wrong_focal_or_supplied_nature_never_runs_a_protein_reader(pair, monkeypatch):
    molecule, target = pair
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    assert target.explore().view(TOPIC).outcome["status"] == "not_applicable"
    assert (
        molecule.explore(related_cards=[molecule]).view(TOPIC).outcome["status"]
        == "missing_prerequisite"
    )
    other = Card(
        meta={
            "entity_type": "disease",
            "card_id": "sabueso:disease:mondo:MONDO:0001444",
        }
    )
    assert (
        molecule.explore(related_cards=[other]).view(TOPIC).outcome["status"]
        == "unsupported"
    )


def test_same_name_without_identity_edges_cannot_join(pair, monkeypatch):
    molecule, target = pair
    raw = molecule.to_dict()
    raw["relationship_store"] = [
        rel for rel in raw["relationship_store"] if rel["predicate"] != "same_as"
    ]
    named = Card.from_dict(raw)
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    view = named.explore(related_cards=[target]).view(TOPIC)
    assert view.outcome["status"] == "missing_prerequisite"
    assert "same_as" in view.outcome["reason"]
    assert not view.items()
    assert view.native_payload["identity"]["admitted_molecule_refs"] == []


def test_explicit_conflicting_anchor_refuses_merged_interpretation(
    public_originals, pair, monkeypatch
):
    molecule, target = pair
    contradictory = restored(public_originals, "benz")
    synthetic_alias(contradictory, BTS)
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    view = molecule.explore(related_cards=[target, contradictory]).view(TOPIC)
    assert view.outcome["status"] == "missing_prerequisite"
    assert "conflicting" in view.outcome["reason"]
    assert len(view.native_payload["identity"]["conflicting_record_anchors"][BTS]) == 2
    assert not view.items()


def test_missing_identity_support_is_partial_without_discarding_values(pair):
    molecule, target = pair
    raw = molecule.to_dict()
    raw["source_assertion_store"] = []
    view = Card.from_dict(raw).explore(related_cards=[target]).view(TOPIC)
    assert view.outcome["status"] == "partial"
    item = view.items()[0]
    assert item.cells["class"].value == "weak"
    assert any(
        source["state"] == "not_retained"
        for source in item.support[0]["source_assertions"]
    )
    links = item.related()
    missing = next(
        link
        for link in links.items()
        if link._entry.value["availability"] == "missing_prerequisite"
    )
    assert missing.open().outcome["status"] == "missing_prerequisite"


def test_explicit_unmatched_alias_is_scoped_and_source_values_remain_typed(pair):
    molecule, target = pair
    assertion, _ = synthetic_alias(molecule, "chembl:CHEMBL999999999")
    explorer = molecule.explore(related_cards=[target])
    view = explorer.view(TOPIC, options={"molecule_ref": "chembl:CHEMBL999999999"})
    assert view.outcome["status"] == "empty"
    assert len(view.items()) == 1
    assert view.items()[0].cells["record_count"].value == 0
    link = next(
        link
        for link in view.items()[0].related().items()
        if link._entry.value["role"] == "source"
        and link._entry.value["target_ref"] == assertion["id"]
    )
    values = link.open().native_payload["asserted_value"]["synthetic_control"]
    assert [type(value) for value in values] == [bool, int, float, type(None)]


def test_duplicate_inputs_share_evaluation_but_retain_occurrences(pair, monkeypatch):
    molecule, target = pair
    original, calls = Card.bioactivities, []

    def counted(card, *args, **kwargs):
        calls.append(card.id)
        return original(card, *args, **kwargs)

    monkeypatch.setattr(Card, "bioactivities", counted)
    explorer = molecule.explore(related_cards=[target, target])
    view = explorer.view(TOPIC)
    assert (
        view.native_payload["identity"]["input_multiplicity"][target.pinned_ref()] == 2
    )
    assert len(view.items()) == 1
    assert explorer.answer("measured_targets").result_ref == view.result_ref
    assert explorer.access.select(TOPIC).result_ref == view.result_ref
    assert calls == [target.id]


def test_same_target_id_different_snapshots_are_separate_contexts(pair):
    molecule, target = pair
    raw = target.to_dict()
    raw["meta"]["synthetic_snapshot_control"] = (
        "distinct supplied state, unchanged measurements"
    )
    second = Card.from_dict(raw)
    assert second.id == target.id and second.pinned_ref() != target.pinned_ref()
    explorer = molecule.explore(related_cards=[target, second])
    view = explorer.view(TOPIC)
    assert {item.cells["target_card_ref"].value for item in view.items()} == {
        target.pinned_ref(),
        second.pinned_ref(),
    }
    groups = explorer.view(TOPIC, options={"target_card_ref": second.pinned_ref()})
    assert groups.context["grain"] == "group"
    assert all(
        item.cells["target_card_ref"].value == second.pinned_ref()
        for item in groups.items()
    )
    with pytest.raises(ArgumentError):
        explorer.view(TOPIC, options={"target_card_ref": target.id})


def test_alias_aggregates_keep_native_grains_and_dimension_limits(
    public_originals, pair
):
    molecule, target = pair
    synthetic_alias(molecule, BENZ)
    explorer = molecule.explore(related_cards=[target])
    root = explorer.view(TOPIC)
    item = root.items()[0]
    assert (
        item.cells["class"].value is None
        and item.cells["class"].state == "not_applicable"
    )
    assert item.cells["measurement"].state == "not_applicable"
    groups = item.open()
    assert {member.cells["molecule_ref"].value for member in groups.items()} == {
        BTS,
        BENZ,
    }
    assert {member.cells["class"].value for member in groups.items()} == {
        "weak",
        "inconclusive",
        "not_determined",
    }
    with pytest.raises(ArgumentError, match="dimensions"):
        groups.sort("measurement", unit="nanomolar")
    selected = groups.filter("molecule_ref", equals=BTS).sort(
        "measurement", unit="nanomolar"
    )
    assert len(selected.items()) == 1
    machine = explorer.access.select(
        TOPIC,
        options={"target_card_ref": target.pinned_ref()},
        where={"molecule_ref": BTS, "measurement": {"value": 33, "unit": "micromolar"}},
        order_by={"column": "measurement", "unit": "nanomolar"},
    )
    assert machine.count == 1
    assert (
        machine.page(max_bytes=65536)["items"][0]["item_ref"]
        == selected.items()[0].item_ref
    )
    assert groups.native_payload == selected.native_payload


def test_target_identity_guard_refuses_unscoped_native_work(pair, monkeypatch):
    molecule, target = pair
    raw = target.to_dict()
    next(
        rel
        for rel in raw["relationship_store"]
        if rel["predicate"] == "has_bioactivity"
    )["subject_ref"] = "uniprot:P60174"
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    view = molecule.explore(related_cards=[Card.from_dict(raw)]).view(TOPIC)
    assert view.outcome["status"] == "missing_prerequisite"
    assert view.items()[0].cells["measurement"].state == "not_evaluated"


def test_public_native_crossing_is_lazy_complete_and_duplicate_aware(
    public_originals, pair, monkeypatch
):
    molecule, target = pair
    benz = restored(public_originals, "benz")
    explorer = molecule.explore(related_cards=[target, benz])
    item = explorer.view(TOPIC).items()[0]
    links = item.related()
    duplicate = (
        molecule.explore(related_cards=[target, molecule]).view(TOPIC).items()[0]
    )
    repeated_links = duplicate.related()
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    crossing = next(
        link
        for link in links.items()
        if link._entry.value["role"] == "native_ligand_crossing"
    ).open()
    assert (
        crossing.native_payload
        == public_originals["native"]["ligand_explanations"]["bts"]
    )
    assert crossing.back().view_ref == links.view_ref
    assert "False/None" in repr(crossing)
    repeated = next(
        link
        for link in repeated_links.items()
        if link._entry.value["role"] == "native_ligand_crossing"
    ).open()
    assert any(
        gap["reason"] == "multiple_deck_members"
        for gap in repeated.native_payload["gaps"]
    )


@pytest.mark.parametrize(
    "options",
    [
        {"unknown": True},
        {"include_indirect": 1},
        {"classification_rule": "bioactivity_class@999"},
        {"measurement_rule": "measurement_identity@999"},
        {"target_scope_rule": "bioactivity_target_scope@999"},
        {"thresholds": {"active": float("nan")}},
        {"target_card_ref": False},
        {"target_card_ref": "sabueso:protein:uniprot:P52270"},
        {"measurement_ref": "MG_fake"},
    ],
)
def test_invalid_policy_and_focus_arguments_fail_before_any_reader(
    pair, options, monkeypatch
):
    molecule, target = pair
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    with pytest.raises(ArgumentError):
        molecule.access(related_cards=[target]).select(TOPIC, options=options)


@pytest.mark.parametrize(
    "arguments",
    [
        {"fields": ["unknown"]},
        {"fields": ["class", "class"]},
        {"where": {"record_count": True}},
        {"where": {"measurement": 33000}},
        {"order_by": {"column": "measurement"}},
        {"order_by": {"column": "class", "unit": "nanomolar"}},
        {"item_refs": ["XI_foreign"]},
    ],
)
def test_invalid_display_requests_fail_before_materialization(
    pair, arguments, monkeypatch
):
    molecule, target = pair
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    with pytest.raises(ArgumentError):
        molecule.access(related_cards=[target]).select(TOPIC, **arguments)


def test_existing_saved_science_discovery_and_new_topic_unavailability(
    pair, tmp_path, monkeypatch
):
    molecule, _ = pair
    path = tmp_path / "literature.json"
    molecule.explore().view("literature").save(path)
    old = sabueso.read_exploration(path)
    assert "literature" in old.explorer.capabilities["scientific_topics"]
    import sabueso.core.card_molecule_activity_access as activity

    monkeypatch.setattr(activity, "materialize", forbidden)
    monkeypatch.setattr(activity, "options_for_activity_context", forbidden)
    assert old.explorer.view(TOPIC).outcome["status"] == "not_saved"
    assert old.explorer.answer("measured_targets").outcome["status"] == "not_saved"
    assert old.explorer.access.select(TOPIC).page()["outcome"]["status"] == "not_saved"
    original = (
        Path(__file__).with_name("data") / "bioactivity_saved_original17_sdk202.json.gz"
    )
    bio = sabueso.read_exploration(original)
    assert "bioactivities" in bio.explorer.capabilities["scientific_topics"]


def test_successful_scoped_empty_is_distinct_from_unqueried_or_failed(public_originals):
    molecule = restored(public_originals, "bts")
    empty = restored(public_originals, "empty")
    view = molecule.explore(related_cards=[empty]).view(TOPIC)
    assert view.outcome["status"] == "empty"
    assert view.items()[0].cells["record_count"].value == 0
    assert view.items()[0].cells["measurement"].state == "not_applicable"
    assert view.items()[0]._entry.value["interpretation"]["state"] == "empty"
    states = [
        row["state"] for row in view.coverage["rows"] if row["source"] == "ChEMBL"
    ]
    assert states and states[0] in ("known", "not_stated")
    assert "synthetic-empty-control" in {
        row.get("release") for row in view.coverage["rows"]
    }


@pytest.mark.parametrize(
    "options,oracle",
    [
        ({"include_indirect": True}, "indirect_overview"),
        (
            {
                "measurement_rule": "measurement_identity@2",
                "target_scope_rule": "bioactivity_target_scope@2",
            },
            "optin_overview",
        ),
    ],
)
def test_optin_policies_forward_exact_native_semantics_without_default_adoption(
    public_originals, pair, options, oracle
):
    molecule, target = pair
    explorer = molecule.explore(related_cards=[target])
    view = explorer.view(TOPIC, options=options)
    original = view.native_payload["targets"][target.pinned_ref()]["overview"]["wire"]
    assert original["native_payload"] == public_originals["native"][oracle]
    assert view.context["options"] == {**DEFAULTS, **options}
    assert view.native_payload["identity"]["focal_edges"]
    assert explorer.view(TOPIC).context["options"] == DEFAULTS


def test_record_focus_binds_exact_native_relationship_membership(pair):
    molecule, target = pair
    explorer = molecule.explore(related_cards=[target])
    groups = explorer.view(TOPIC).items()[0].open()
    records = groups.items()[0].open()
    record = records.items()[0]
    focused = explorer.view(
        TOPIC,
        options={
            "target_card_ref": target.pinned_ref(),
            "molecule_ref": BTS,
            "measurement_ref": record.cells["relationship_id"].value,
        },
    )
    assert [item.cells["relationship_id"].value for item in focused.items()] == [
        record.cells["relationship_id"].value
    ]
    assert focused.items()[0].open().native_payload == record.open().native_payload
    with pytest.raises(ArgumentError):
        explorer.view(
            TOPIC,
            options={
                "target_card_ref": target.pinned_ref(),
                "molecule_ref": BTS,
                "measurement_ref": "REL_synthetic_foreign",
            },
        )


def test_filtered_origin_machine_membership_and_paging_remain_exact(pair):
    molecule, target = pair
    second_raw = target.to_dict()
    second_raw["meta"]["synthetic_snapshot_control"] = "paging context two"
    second = Card.from_dict(second_raw)
    explorer = molecule.explore(related_cards=[target, second])
    root = explorer.answer("measured_targets").filter(
        "target_card_ref", equals=target.pinned_ref()
    )
    records = root.items()[0].open().items()[0].open()
    links = records.items()[0].related()
    returned = next(
        link for link in links.items() if link._entry.value["role"] == "molecule_root"
    ).open()
    assert returned.view_ref == root.view_ref
    assert returned.request == root.request and returned.outcome == root.outcome
    assert returned._display_request == root._display_request
    selection = explorer.access.select(
        TOPIC,
        fields=["target_card_ref", "record_count"],
        order_by={"column": "target_card_ref", "descending": True},
    )
    first = selection.page(limit=1, max_bytes=65536)
    assert first["page"]["total"] == 2 and first["page"]["next_cursor"]
    second_page = selection.page(
        limit=1, max_bytes=65536, cursor=first["page"]["next_cursor"]
    )
    assert second_page["items"][0]["item_ref"] != first["items"][0]["item_ref"]
    one = explorer.access.select(TOPIC, item_refs=[first["items"][0]["item_ref"]])
    assert one.count == 1
    assert (
        one.page(max_bytes=65536)["items"][0]["item_ref"]
        == first["items"][0]["item_ref"]
    )
    with pytest.raises(ArgumentError):
        one.page(cursor=first["page"]["next_cursor"])


def test_explicit_target_crossing_can_start_a_fresh_question_without_focal_confusion(
    pair,
):
    molecule, target = pair
    root = molecule.explore(related_cards=[target]).answer("measured_targets")
    links = root.items()[0].related()
    destination = next(
        link for link in links.items() if link._entry.value["role"] == "target_card"
    ).open()
    assert destination.explorer.context["card_ref"] == target.pinned_ref()
    assert destination.context["molecule_card_ref"] == molecule.pinned_ref()
    fresh = destination.explorer.answer("publications")
    assert fresh.request == {
        "question": "publications",
        "topic": "literature",
        "options": {"publication_ref": None},
    }
    assert fresh.explorer.context["card_ref"] == target.pinned_ref()
    assert destination.back().view_ref == links.view_ref


def test_capture_is_detached_and_repeated_requests_do_not_repeat_native_work(
    pair, monkeypatch
):
    molecule, target = pair
    explorer = molecule.explore(related_cards=[target])
    first = explorer.view(TOPIC)
    original = first.native_payload
    target.relationship_store.store.clear()
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    assert explorer.view(TOPIC).native_payload == original
    assert explorer.access.select(TOPIC).result_ref == first.result_ref
    with pytest.raises(ArgumentError):
        explorer.view(
            TOPIC,
            options={
                "target_card_ref": "sabueso:protein:uniprot:P52270@sha256:" + "0" * 64
            },
        )


def test_benznidazole_percentage_and_null_keep_native_group_record_states(
    public_originals,
):
    molecule = restored(public_originals, "benz")
    target = restored(public_originals, "target")
    explorer = molecule.explore(related_cards=[target])
    groups = explorer.view(TOPIC).items()[0].open()
    assert {item.cells["class"].value for item in groups.items()} == {
        "inconclusive",
        "not_determined",
    }
    percent = next(
        item for item in groups.items() if item.cells["measurement"].value is not None
    )
    null = next(
        item for item in groups.items() if item.cells["measurement"].value is None
    )
    assert puw.get_value(percent.cells["measurement"].value, to_unit="percent") == 18
    assert null.cells["measurement"].state == "unknown"
    for group in groups.items():
        options = {
            "target_card_ref": target.pinned_ref(),
            "molecule_ref": BENZ,
            "measurement_ref": group.cells["measurement_ref"].value,
        }
        records = group.open()
        original = public_originals["native"]["measurements"][
            group.cells["measurement_ref"].value
        ]
        assert [item.open().native_payload for item in records.items()] == original[
            "records"
        ]
        machine = explorer.access.select(
            TOPIC,
            options=options,
            fields=["measurement", "relation", "relationship_id"],
        )
        for human, frame in zip(
            records.items(), machine.page(max_bytes=65536)["items"], strict=True
        ):
            cell = frame["cells"]["measurement"]
            assert cell["state"] == human.cells["measurement"].state
            if cell["value"] is None:
                assert human.cells["measurement"].value is None
            else:
                quantity = QuantityRecord.from_dict(cell["value"]).to_quantity(
                    field=QUANTITY_FIELD, unit="percent", form="pint"
                )
                assert puw.get_value(quantity, to_unit="percent") == 18


def test_identity_and_native_support_locations_resolve_in_their_original_cards(pair):
    molecule, target = pair
    explorer = molecule.explore(related_cards=[target])
    item = explorer.view(TOPIC).items()[0]
    support = item.support[0]
    assert support["whole_card_context_location"]["card_ref"] == molecule.pinned_ref()
    assert support["target_card_location"]["card_ref"] == target.pinned_ref()
    source_pins = set()
    for statement in support["source_assertions"]:
        assert statement["state"] == "present"
        node, location = explorer.access._resolve(statement["location"])
        assert node["id"] == statement["id"]
        source_pins.add(location["card_ref"])
    assert source_pins == {molecule.pinned_ref(), target.pinned_ref()}
    for location in support["relationship_locations"]:
        node, resolved = explorer.access._resolve(location)
        assert node["predicate"] in ("same_as", "has_bioactivity")
        assert resolved["card_ref"] in source_pins


def test_record_source_text_is_escaped_without_changing_native_values(pair):
    molecule, target = pair
    raw = target.to_dict()
    marker = '<script>alert("synthetic source")</script>'
    for relation in raw["relationship_store"]:
        if relation["predicate"] == "has_bioactivity" and relation["object_ref"] == BTS:
            relation["qualifiers"]["assay"]["description"] = marker
    target = Card.from_dict(raw)
    view = molecule.explore(related_cards=[target]).view(TOPIC)
    record = view.items()[0].open().items()[0].open().items()[0].open()
    assert (
        record.native_payload["relationship"]["qualifiers"]["assay"]["description"]
        == marker
    )
    html = record._repr_html_()
    assert marker not in html and "&lt;script&gt;" in html


def test_bounded_page_defers_complete_scientific_values_and_retains_read_locations(
    pair,
):
    molecule, target = pair
    explorer = molecule.explore(related_cards=[target])
    selection = explorer.access.select(TOPIC, fields=["measurement"])
    page = selection.page(max_bytes=8192)
    assert (
        len(json.dumps(page, ensure_ascii=False, separators=(",", ":")).encode())
        <= 8192
    )
    assert page["items"]
    item = page["items"][0]
    assert item["value_included"] is False and item["inspection_required"] is True
    assert item["location"]
    assert (
        selection.page(max_bytes=65536)["items"][0]["cells"]["measurement"]["value"][
            "manifest"
        ]["field"]
        == QUANTITY_FIELD
    )


def synthetic_cross_alias_copy(target):
    """Retain the full public target plus one explicitly synthetic foreign-alias copy."""
    original = next(
        row
        for row in target.relationships("has_bioactivity")
        if row["object_ref"] == BTS
    )
    qualifiers = deepcopy(original["qualifiers"])
    qualifiers.update(
        source="Synthetic copy control",
        activity_id="SYN-COPY",
        copy_of={
            "source": record_source(qualifiers),
            "activity_id": qualifiers["activity_id"],
        },
    )
    assertion = make_source_assertion(
        "relationships.has_bioactivity",
        qualifiers,
        "Synthetic copy control",
        "SYN-COPY",
        "synthetic fixture",
        subject_ref="uniprot:P52270",
    )
    target.source_assertion_store.add(assertion)
    copied = make_relationship(
        "uniprot:P52270",
        "has_bioactivity",
        "chembl:CHEMBL999999997",
        qualifiers,
        [assertion["id"]],
    )
    target.relationship_store.add(copied)
    assert len(target.relationships("has_bioactivity")) == 494
    return original, copied


@pytest.mark.parametrize("grain", ("target", "group", "record"))
@pytest.mark.parametrize("skip_digestion", (False, True))
def test_quantity_display_filter_preserves_public_source_and_native_navigation(
    public_originals, monkeypatch, grain, skip_digestion
):
    molecule, target, benz = (
        restored(public_originals, name) for name in ("bts", "target", "benz")
    )
    before = [card.to_dict() for card in (molecule, target, benz)]
    original, calls = Card.bioactivities, []

    def counted(card, *args, **kwargs):
        calls.append(card.id)
        return original(card, *args, **kwargs)

    monkeypatch.setattr(Card, "bioactivities", counted)
    root = molecule.explore(related_cards=[target, benz]).answer("measured_targets")
    scope = root
    if grain in ("group", "record"):
        scope = scope.items()[0].open()
    if grain == "record":
        scope = scope.items()[0].open()
    node = {"value": 33, "unit": "micromolar"}
    node_selected = scope.filter("measurement", equals=node)
    quantity = puw.quantity(33, "micromolar", form="pint")
    selected = scope.filter(
        "measurement", equals=quantity, skip_digestion=skip_digestion
    )
    assert len(selected.items()) == len(node_selected.items()) == 1
    assert selected.view_ref == node_selected.view_ref
    links = selected.items()[0].related()
    control_links = node_selected.items()[0].related()
    assert selected._display_request["equals"] == {
        "value": 33.0,
        "unit": "micromolar",
    }
    assert type(node_selected._display_request["equals"]["value"]) is int
    assert node_selected._display_request["equals"] == node
    assert puw.get_value(quantity, to_unit="micromolar") == 33

    def link(view, role):
        return next(item for item in view.items() if item._entry.value["role"] == role)

    source = link(links, "source").open()
    source_context = source.context["molecule_activity_navigation"]
    assert (
        source_context["parent_selection"]["display_request"]
        == selected._display_request
    )
    assert source.back().view_ref == links.view_ref
    assert links.back().view_ref == selected.view_ref
    assert links.back()._display_request == selected._display_request
    control_source = link(control_links, "source").open()
    assert source.native_payload == control_source.native_payload
    publication = link(links, "publication_context").open()
    assert len(publication.native_payload["links"]) == 9
    crossing = link(links, "native_ligand_crossing").open()
    assert (
        crossing.native_payload
        == public_originals["native"]["ligand_explanations"]["bts"]
    )
    returned = link(links, "molecule_root").open()
    assert returned.view_ref == (selected if grain == "target" else root).view_ref
    assert calls == [target.id]
    assert before == [card.to_dict() for card in (molecule, target, benz)]


@pytest.mark.parametrize(
    "first_name,second_name",
    [("bts", "benz"), ("benz", "bts"), ("bts", "bts-snapshot")],
)
def test_native_crossing_cache_keeps_each_publicly_navigated_focal_molecule(
    public_originals, monkeypatch, first_name, second_name
):
    first, target = (
        restored(public_originals, name) for name in (first_name, "target")
    )
    if second_name == "bts-snapshot":
        raw = first.to_dict()
        raw["meta"]["synthetic_snapshot_control"] = (
            "Distinct molecule snapshot; unchanged source relationships."
        )
        second = Card.from_dict(raw)
        assert second.id == first.id and second.pinned_ref() != first.pinned_ref()
    else:
        second = restored(public_originals, second_name)
    before = [card.to_dict() for card in (first, target, second)]
    oracles = {
        card.pinned_ref(): serialized_native(
            target.explain_ligand(card.id, Deck([first, second]))
        )
        for card in (first, second)
    }
    original, calls = Card.bioactivities, []

    def counted(card, *args, **kwargs):
        calls.append(card.id)
        return original(card, *args, **kwargs)

    monkeypatch.setattr(Card, "bioactivities", counted)

    def link(view, role):
        return next(item for item in view.items() if item._entry.value["role"] == role)

    root = first.explore(related_cards=[target, second]).answer("measured_targets")
    first_links = root.items()[0].related()
    first_crossing = link(first_links, "native_ligand_crossing").open()
    assert first_crossing.native_payload == oracles[first.pinned_ref()]
    protein = link(first_links, "target_card").open()
    activity = protein.explorer.answer("measured_molecules")
    second_alias = BENZ if second_name == "benz" else BTS
    molecule = next(
        item
        for item in activity.items()
        if item.cells["molecule_ref"].value == second_alias
    )
    relationship = link(molecule.related(), "original_relationship").open()
    object_ref = next(
        item for item in relationship.items() if item._entry.key == "object_ref"
    )
    destinations = object_ref.related()
    destination = next(
        item
        for item in destinations.items()
        if any(
            candidate["capture"] == second.pinned_ref()
            for candidate in item._entry.value.get("candidates", [])
        )
    ).open()
    if destination.explorer.context["card_ref"] != second.pinned_ref():
        assert destination.outcome["status"] == "ambiguous"
        destination = next(
            item
            for item in destination.items()
            if any(
                candidate["capture"] == second.pinned_ref()
                for candidate in item._entry.value.get("candidates", [])
            )
        ).open()
    assert destination.explorer.context["card_ref"] == second.pinned_ref()
    second_root = destination.explorer.answer("measured_targets")
    second_links = second_root.items()[0].related()
    second_crossing = link(second_links, "native_ligand_crossing").open()
    assert second_crossing.native_payload["molecule_ref"] == second.id
    assert second_crossing.native_payload == oracles[second.pinned_ref()]
    _, location = second_crossing.explorer.access._resolve(
        second_crossing._selection._target["location"]
    )
    assert location["segments"] == [{"type": "Key", "value": "native_payload"}]
    wrapper = second_crossing.explorer.access._objects[location["result_ref"]]
    assert wrapper["molecule_card_ref"] == second.pinned_ref()
    assert second_crossing.explorer.context["card_ref"] == second.pinned_ref()
    assert second_crossing.back().view_ref == second_links.view_ref
    assert (
        link(first_links, "native_ligand_crossing").open().native_payload
        == oracles[first.pinned_ref()]
    )
    assert (
        link(second_links, "native_ligand_crossing").open().native_payload
        == oracles[second.pinned_ref()]
    )
    assert calls == [target.id]
    assert before == [card.to_dict() for card in (first, target, second)]


@pytest.mark.parametrize(
    "measurement_rule", ["measurement_identity@1", "measurement_identity@2"]
)
@pytest.mark.parametrize("admit_alias", [False, True])
def test_cross_alias_copy_requires_explicit_identity_and_preserves_complete_native_context(
    pair, measurement_rule, admit_alias
):
    molecule, target = pair
    original, copied = synthetic_cross_alias_copy(target)
    if admit_alias:
        synthetic_alias(molecule, copied["object_ref"])
    before = molecule.to_dict(), target.to_dict()
    options = {"measurement_rule": measurement_rule}
    native = serialized_native(target.bioactivities(**options))
    explorer = molecule.explore(related_cards=[target])
    root = explorer.view(TOPIC, options=options)
    assert (
        root.native_payload["targets"][target.pinned_ref()]["overview"]["wire"][
            "native_payload"
        ]
        == native
    )
    expected = {original["id"], copied["id"]} if admit_alias else {original["id"]}
    assert root.items()[0].cells["record_count"].value == len(expected)
    assert root.items()[0].cells["measurement_count"].value == 1
    assert root.items()[0].cells["measurement_ref"].state == "not_applicable"
    groups = root.items()[0].open()
    assert len(groups.items()) == 1
    group = groups.items()[0]
    assert group.cells["record_count"].value == len(expected)
    membership = group._entry.value["interpretation"]["identity_membership"]
    assert set(membership["included_relationship_ids"]) == expected
    assert set(membership["context_only_relationship_ids"]) == (
        {copied["id"]} if not admit_alias else set()
    )
    records = group.open()
    assert len(records.items()) == len(expected)
    assert {item.cells["relationship_id"].value for item in records.items()} == expected
    assert all(item.cells["class"].state == "present" for item in records.items())
    explanation = serialized_native(
        target.explain_measurement(group.cells["measurement_ref"].value, **options)
    )
    assert {row["relationship"]["id"] for row in explanation["records"]} == {
        original["id"],
        copied["id"],
    }
    for item in records.items():
        assert item.open().native_payload == next(
            row
            for row in explanation["records"]
            if row["relationship"]["id"] == item.cells["relationship_id"].value
        )
    for wire in records.native_payload["targets"][target.pinned_ref()][
        "focused_results"
    ].values():
        assert wire["native_payload"] == explanation
    page = explorer.access.select(
        TOPIC,
        options={
            **options,
            "target_card_ref": target.pinned_ref(),
            "measurement_ref": group.cells["measurement_ref"].value,
        },
        fields=["molecule_ref", "relationship_id", "measurement"],
    ).page(max_bytes=65536)
    assert {
        frame["cells"]["relationship_id"]["value"] for frame in page["items"]
    } == expected
    if not admit_alias:
        assert (
            group.cells["class"].value is None
            and group.cells["class"].state == "not_applicable"
        )
        assert "outside" in group.cells["class"].reason
        context_link = next(
            item
            for item in group.related().items()
            if item._entry.value["role"] == "original_relationship"
            and copied["id"] in item.label
        )
        assert "context only" in context_link.label.lower()
        assert context_link.open().native_payload["id"] == copied["id"]
    # A requested source-record focus remains narrower than all admitted aliases.
    focused = explorer.view(
        TOPIC,
        options={
            **options,
            "target_card_ref": target.pinned_ref(),
            "molecule_ref": BTS,
        },
    )
    assert focused.items()[0].cells["record_count"].value == 1
    assert {
        item.cells["relationship_id"].value
        for item in focused.items()[0].open().items()
    } == {original["id"]}
    if admit_alias:
        assert "multiple source-molecule contexts" in str(groups)
        copy_focus = explorer.view(
            TOPIC,
            options={
                **options,
                "target_card_ref": target.pinned_ref(),
                "molecule_ref": copied["object_ref"],
            },
        )
        assert copy_focus.items()[0].cells["record_count"].value == 1
        assert {
            item.cells["relationship_id"].value
            for item in copy_focus.items()[0].open().items()
        } == {copied["id"]}
    assert before == (molecule.to_dict(), target.to_dict())


@pytest.mark.parametrize(
    "measurement_rule", ["measurement_identity@1", "measurement_identity@2"]
)
def test_foreign_alias_record_focus_refuses_before_native_evaluation(
    pair, monkeypatch, measurement_rule
):
    molecule, target = pair
    _, copied = synthetic_cross_alias_copy(target)
    explorer = molecule.explore(related_cards=[target])
    monkeypatch.setattr(Card, "bioactivities", forbidden)
    monkeypatch.setattr(Card, "explain_measurement", forbidden)
    with pytest.raises(ArgumentError):
        explorer.view(
            TOPIC,
            options={
                "measurement_rule": measurement_rule,
                "target_card_ref": target.pinned_ref(),
                "measurement_ref": copied["id"],
            },
        )
