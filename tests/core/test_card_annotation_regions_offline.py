"""Individual original annotations and explicit structural navigation, offline."""

import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.card_annotation_regions_v1 import context
from sabueso.core.card_exploration_storage import _seal, operation_key
from sabueso.core.card_exploration_verification import _verify_links
from sabueso.core.errors import StorageError
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.rcsb import FixtureRCSBClient

PUBLIC = Path("temp_data/frozen_cards/schema_0.3.9__P52270.json")


def forbidden(*a, **k):
    raise AssertionError("No acquisition, live scientific interpretation or recapture")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def synthetic(*, kind="Active site", molecule=None, begin=2, end=4, modifier="EXACT"):
    record = {
        "primaryAccession": "P52270",
        "sequence": {"value": "M" * 10, "length": 10},
        "entryAudit": {"sequenceVersion": 7},
        "features": [
            {
                "type": kind,
                "description": "explicit synthetic annotation",
                "molecule": molecule,
                "location": {
                    "start": {"value": begin, "modifier": modifier},
                    "end": {"value": end, "modifier": "EXACT"},
                },
            }
        ],
    }
    return build_card_from_mapping(
        map_protein(record, "synthetic"),
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:P52270",
    )


def annotation(card):
    return card.explore().view("annotated_regions").items()[0]


def question(item):
    return item.related().filter("role", equals="question").items()[0]


@pytest.fixture
def public_card():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    return sabueso.resolve("P52270", resolver=resolver, structures=["1SUX"])[0]


def test_public_annotations_keep_individual_support_and_share_the_existing_structural_result(
    public_card,
):
    original = public_card.to_dict()
    explorer = public_card.explore()
    view = explorer.answer("annotated_regions")
    assert view.result_ref == explorer.view("annotated_regions").result_ref
    active = view.filter("feature_type", equals="active_site")
    assert len(active.items()) == 2
    assert "start" in view.capabilities["filter"]
    first = active.items()[0]
    assert first.kind == "annotation" and first.cells["start"].value == 96
    refs = first.support[0]["source_assertion_ids"]
    assert len(refs) == 1
    source = first.explain().items()[0]
    assert source.label.startswith("Annotation item support")
    assert source.open().native_payload["asserted_value"] == first.open().native_payload
    assert first.explain().back() is active
    link = question(first)
    basis = link._entry.value["annotation_context"]
    assert (
        basis["rule"] == "annotation_structure_request@1" and basis["state"] == "ready"
    )
    assert basis["source_assertion_ids"]["annotation"] == refs
    links = first.related().filter("role", equals="source")
    assert {item.open().native_payload["id"] for item in links.items()} == {
        ref for refs in basis["source_assertion_ids"].values() for ref in refs
    }
    assert basis["sequence_revisions"]["state"] == "matching"
    structures = link.open()
    assert structures.back() is link.back()
    assert structures.back().back().back().back() is active
    assert structures.request["options"]["region"] == [96]
    assert (
        structures.result_ref
        == explorer.answer(
            "region_coverage",
            options={"sequence_ref": "uniprot:P52270", "region": [96]},
        ).result_ref
    )
    assert (
        structures.result_ref
        == explorer.access.select("structures", options={"region": [96]}).result_ref
    )
    assert public_card.to_dict() == original


def test_preparing_annotation_links_does_not_materialize_structural_science(
    monkeypatch,
):
    explorer = synthetic().explore()
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_scientific_access"),
        "materialize",
        forbidden,
    )
    item = explorer.view("annotated_regions").items()[0]
    assert question(item)._entry.value["availability"] == "available"
    literal = explorer.inspect("features_positional.active_site.value").items()[0]
    assert question(literal)._entry.value["annotation_context"] == context(
        explorer, item.payload_location
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"molecule": "P52270-2"},
        {"molecule": "Isoform 2"},
        {"modifier": "LESS_THAN"},
        {"modifier": "UNKNOWN"},
        {"begin": None},
        {"end": None},
        {"begin": 0},
        {"end": 11},
    ],
)
def test_unplaced_or_uncertain_annotations_remain_visible_without_inferred_positions(
    kwargs, monkeypatch
):
    item = annotation(synthetic(**kwargs))
    assert item.open().native_payload["location"]
    monkeypatch.setattr(Card, "structures", forbidden)
    link = question(item)
    assert link._entry.value["availability"] == "unsupported"
    assert link._entry.value["annotation_context"]["request"] is None
    assert link.open().outcome["status"] == "unsupported"


def test_disulfide_bonds_request_only_the_two_declared_endpoints():
    link = question(annotation(synthetic(kind="Disulfide bond")))
    basis = link._entry.value["annotation_context"]
    assert basis["position_scope"] == "declared_bond_endpoints"
    assert basis["request"]["options"]["region"] == [2, 4]
    assert link.open().request["options"]["region"] == [2, 4]


def test_legacy_recorded_positions_do_not_invent_missing_native_mapping_inputs():
    original = PUBLIC.read_bytes()
    card = Card.from_dict(json.loads(original))
    item = (
        card.explore()
        .view("annotated_regions")
        .filter("feature_type", equals="active_site")
        .items()[0]
    )
    assert item.cells["start"].value == 96
    link = question(item)
    assert link._entry.value["availability"] == "missing_prerequisite"
    assert (
        "native UniProt feature scope was not retained" in link.open().outcome["reason"]
    )
    assert len(item.explain().items()) == 1
    assert PUBLIC.read_bytes() == original


@pytest.mark.parametrize(
    "change",
    ["unbacked", "foreign", "missing", "conflict", "revision", "native", "type"],
)
def test_exact_original_support_scope_and_revisions_are_required(change):
    card = synthetic()
    node = card.get("features_positional.active_site")
    source = card.source_assertion_store.get(node["source_assertion_ids"][0])
    if change == "unbacked":
        node["value"][0] = {
            **deepcopy(node["value"][0]),
            "description": "not the source value",
        }
    elif change == "foreign":
        source["subject_ref"] = "uniprot:P60174"
    elif change == "missing":
        node["source_assertion_ids"] = ["SA_SYNTHETIC_MISSING"]
    elif change == "conflict":
        card.quality["conflicts"] = [
            {"field": "features_positional.active_site", "values": [2, 3]}
        ]
    elif change == "revision":
        source["source_metadata"]["sequence_version"] = 8
    elif change == "native":
        source["source_metadata"]["uniprot_feature"]["location"]["start"]["value"] = 3
    else:
        source["source_metadata"]["uniprot_feature"]["type"] = "Domain"
    basis = question(annotation(card))._entry.value["annotation_context"]
    assert basis["state"] == "missing_prerequisite" and basis["request"] is None


def test_unstated_revision_stays_explicit_and_does_not_become_matching():
    card = synthetic()
    source = card.source_assertion_store.get(
        card.get("features_positional.active_site")["source_assertion_ids"][0]
    )
    source["source_metadata"].pop("sequence_version")
    basis = question(annotation(card))._entry.value["annotation_context"]
    assert basis["state"] == "ready"
    assert basis["sequence_revisions"]["state"] == "partially_stated"
    assert (
        source["id"]
        in basis["sequence_revisions"]["unstated_source_assertion_ids"]["annotation"]
    )


def test_some_matching_sources_with_unstated_revisions_do_not_establish_full_agreement():
    card = synthetic()
    node = card.get("features_positional.active_site")
    source = deepcopy(card.source_assertion_store.get(node["source_assertion_ids"][0]))
    source["id"] += "_SYNTHETIC_UNSTATED"
    source["source_metadata"].pop("sequence_version")
    card.source_assertion_store.add(source)
    node["source_assertion_ids"].append(source["id"])
    basis = question(annotation(card))._entry.value["annotation_context"]
    assert (
        basis["state"] == "ready"
        and basis["sequence_revisions"]["state"] == "partially_stated"
    )


def test_the_current_card_cannot_replace_the_captured_annotation_or_sequence():
    card = synthetic()
    explorer = card.explore()
    card.sections.clear()
    item = explorer.view("annotated_regions").items()[0]
    assert item.cells["start"].value == 2
    assert question(item).open().request["options"]["region"] == [2, 3, 4]


def test_matching_value_and_subject_do_not_override_a_contradictory_source_record_identity():
    card = synthetic()
    identity = card.get("identifiers.uniprot")
    source = card.source_assertion_store.get(identity["source_assertion_ids"][0])
    source["source"]["record_id"] = "P60174"
    assert (
        question(annotation(card))._entry.value["annotation_context"]["state"]
        == "missing_prerequisite"
    )


@pytest.mark.parametrize("nature", ["small_molecule", "disease", "custom"])
def test_other_natures_do_not_receive_protein_annotation_science(nature):
    explorer = Card(meta={"entity_type": nature}).explore()
    assert "annotated_regions" not in explorer.capabilities["question_keys"]
    result = explorer.view("annotated_regions")
    assert result.outcome["status"] == "not_applicable" and not result.items()


@pytest.mark.parametrize(
    "field,value",
    [("quality", None), ("conflicts", None), ("references", "unrecognized")],
)
def test_malformed_prerequisites_stay_inspectable_without_false_empty_results(
    field, value
):
    card = synthetic()
    if field == "quality":
        card.quality = value
    elif field == "conflicts":
        card.quality["conflicts"] = value
    else:
        card.get("features_positional.active_site")["source_assertion_ids"] = value
    item = annotation(card)
    assert item.open().native_payload
    assert (
        question(item)._entry.value["annotation_context"]["state"]
        == "missing_prerequisite"
    )


def test_unknown_native_compound_locations_are_not_projected_as_bounding_intervals():
    card = synthetic()
    node = card.get("features_positional.active_site")
    source = card.source_assertion_store.get(node["source_assertion_ids"][0])
    source["source_metadata"]["uniprot_feature"]["location"]["fragments"] = [
        [2, 2],
        [4, 4],
    ]
    assert (
        question(annotation(card))._entry.value["annotation_context"]["state"]
        == "unsupported"
    )


def test_migration_reports_missing_native_history_without_backfilling_the_original():
    from sabueso.core.migration import _has

    original = json.loads(PUBLIC.read_bytes())
    before = deepcopy(original)
    path = "source_assertion_store[].source_metadata.uniprot_feature"
    assert not _has(original, path)
    migrated = sabueso.migrate_card(original)
    gaps = [
        gap
        for step in migrated.quality["migration"][0]["steps"]
        for gap in step["gaps"]
    ]
    assert any(gap["path"] == path and gap["kind"] == "missing" for gap in gaps)
    assert original == before and not _has(migrated.to_dict(), path)
    assert _has(Card(meta={"entity_type": "protein"}).to_dict(), path)


def test_refresh_records_a_new_native_basis_while_the_original_pin_stays_fixed(
    tmp_path,
):
    from sabueso.core.migration import _has

    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    original = sabueso.resolve("P52270", resolver=resolver)[0]
    for source in original.source_assertion_store.to_list():
        if source["field_path"].startswith("features_positional."):
            source.get("source_metadata", {}).pop("uniprot_feature", None)
    original.meta["schema_version"] = "0.3.13"
    before = original.to_dict()
    store = sabueso.KnowledgeStore(tmp_path / "refresh.db")
    pin = store.save(original)
    refreshed, _ = sabueso.refresh_card(original, store=store, resolver=resolver)
    assert _has(
        refreshed.to_dict(), "source_assertion_store[].source_metadata.uniprot_feature"
    )
    assert (
        question(annotation(refreshed))._entry.value["annotation_context"]["state"]
        == "ready"
    )
    assert store.load(pin).to_dict() == before == original.to_dict()


@pytest.mark.parametrize("change", ["positions", "support", "state", "native_path"])
def test_frozen_navigation_verifier_rejects_semantically_rebound_questions(change):
    view = annotation(synthetic()).related()
    payload = view.native_payload
    link = next(row for row in payload["links"] if row["role"] == "question")
    basis = link["annotation_context"]
    if change == "positions":
        basis["request"]["options"]["region"] = [[5, 6]]
    elif change == "support":
        basis["source_assertion_ids"]["annotation"] = []
    elif change == "state":
        basis["state"] = "unsupported"
    else:
        basis["native_feature_inputs"][0]["path"] = ["asserted_value"]
    with pytest.raises(StorageError, match="original source/axis basis"):
        _verify_links(replace(view, _native_override=payload))


def test_saved_structural_journey_reopens_inertly_with_original_question_and_return(
    public_card, tmp_path, monkeypatch
):
    item = (
        public_card.explore()
        .view("annotated_regions")
        .filter("feature_type", equals="active_site")
        .items()[0]
    )
    view = question(item).open()
    path = tmp_path / "original.json"
    receipt = view.save(path)
    original = path.read_bytes()
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(Card, "structures", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_scientific_access"),
        "materialize",
        forbidden,
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_protein_exploration"),
        "region_request",
        forbidden,
    )
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert saved.request == view.request and saved.view_ref == view.view_ref
    original_question = saved.back().items()[0]
    assert original_question.kind == "link"
    assert original_question.open().view_ref == saved.view_ref
    assert original_question.explain().native_payload["link"]["annotation_context"][
        "native_feature_inputs"
    ]
    assert saved.back().back().back().back().items()[0].label == item.label
    assert path.read_bytes() == original


def test_unfollowed_saved_question_stays_not_saved_instead_of_running_science(
    tmp_path, monkeypatch
):
    view = annotation(synthetic()).back()
    path = tmp_path / "unfollowed.json"
    view.save(path)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(Card, "structures", forbidden)
    saved = sabueso.read_exploration(path)
    assert question(saved.items()[0]).open().outcome["status"] == "not_saved"


@pytest.mark.parametrize("topic", ["function", "annotated_regions"])
def test_resealed_related_operation_swaps_are_rejected_against_the_originating_item(
    topic, tmp_path
):
    card = synthetic()
    if topic == "annotated_regions":
        node = card.get("features_positional.active_site")
        source = deepcopy(
            card.source_assertion_store.get(node["source_assertion_ids"][0])
        )
        source["id"] += "_SYNTHETIC_SECOND"
        source["asserted_value"] = deepcopy(node["value"][0])
        source["asserted_value"]["description"] = "second explicit synthetic annotation"
        node["value"].append(deepcopy(source["asserted_value"]))
        node["source_assertion_ids"].append(source["id"])
        card.source_assertion_store.add(source)
    view = card.explore().view(topic)
    first, second = view.items()[:2]
    path = tmp_path / "swapped.json"
    view.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    links = bundle["navigation"]["links"]
    a, b = operation_key(first), operation_key(second)
    links[a], links[b] = links[b], links[a]
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError, match="different originating item"):
        sabueso.read_exploration(path)


def test_blocked_journey_reopens_in_an_independent_process(tmp_path):
    view = question(annotation(synthetic(molecule="P52270-2"))).open()
    path = tmp_path / "unplaced.json"
    view.save(path)
    script = """
import sys,socket,sabueso
from sabueso.core.card import Card
def fail(*a,**k): raise AssertionError('No fixtures/reconstruction/queries/science')
Card.from_dict=fail
Card.structures=fail
socket.socket.connect=fail
def audit(event,args):
    if event=='open' and 'temp_data' in str(args[0]):fail()
sys.addaudithook(audit)
saved=sabueso.read_exploration(sys.argv[1])
assert saved.outcome['status']=='unsupported'
assert saved.back().items()[0].open().outcome['status']=='unsupported'
"""
    with TemporaryDirectory() as cwd:
        subprocess.run(
            [sys.executable, "-c", script, str(path.resolve())], cwd=cwd, check=True
        )


def test_literal_lookalikes_do_not_create_scientific_navigation():
    card = synthetic()
    card.sections["extra"] = {
        "features_positional": card.sections["features_positional"]
    }
    item = (
        card.explore().inspect("extra.features_positional.active_site.value").items()[0]
    )
    assert not item.related().filter("role", equals="question").items()


def test_html_previews_are_escaped_bounded_and_complete_values_stay_readable():
    card = synthetic()
    node = card.get("features_positional.active_site")
    row = deepcopy(node["value"][0])
    row["description"] = "<script>x</script>" + "x" * 3000
    node["value"][0] = row
    view = card.explore().view("annotated_regions")
    html = view.table()._repr_html_()
    assert (
        "<script>" not in html and "&lt;script&gt;" in html and "x" * 3000 not in html
    )
    assert view.items()[0].open().native_payload["description"] == row["description"]
