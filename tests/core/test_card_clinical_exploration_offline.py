"""Clinical human/agent navigation retains exact public source and query scope."""

import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso._private.smonitor.warnings import (
    EnrichmentFailedWarning,
    EnrichmentTruncatedWarning,
)
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.clinicaltrials import FixtureClinicalTrialsClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"
if not (DATA / "chembl/molecules.json").is_file():
    DATA = Path.cwd() / "temp_data"


def forbidden(*args, **kwargs):
    pytest.fail("Captured clinical exploration must not acquire sources")


@pytest.fixture(scope="module")
def originals():
    def resolve(**options):
        return sabueso.resolve(
            "chembl:CHEMBL110",
            chembl_client=FixtureChEMBLClient(DATA),
            clinicaltrials_client=FixtureClinicalTrialsClient(DATA),
            ccd_client=FixtureCCDClient(DATA),
            unichem_client=FixtureUniChemClient(DATA),
            **options,
        )[0]

    with pytest.MonkeyPatch.context() as guard:
        guard.setattr(socket.socket, "connect", forbidden)
        guard.setattr(socket, "create_connection", forbidden)
        cards = {
            "bare": resolve(),
            "indications": resolve(indications=True),
            "trials": resolve(trials={}),
        }
        with pytest.warns(EnrichmentTruncatedWarning):
            cards["limited"] = resolve(trials={"limit": 2})
        with pytest.warns(EnrichmentFailedWarning):
            cards["failed"] = sabueso.resolve(
                "chembl:CHEMBL110",
                trials={},
                chembl_client=FixtureChEMBLClient(DATA),
                clinicaltrials_client=FixtureClinicalTrialsClient(
                    DATA, failing={"NCT00123916"}
                ),
                ccd_client=FixtureCCDClient(DATA),
                unichem_client=FixtureUniChemClient(DATA),
            )[0]
    return {key: card.to_dict() for key, card in cards.items()}


@pytest.fixture(autouse=True)
def no_acquisition(originals, monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    for client in (
        FixtureChEMBLClient,
        FixtureClinicalTrialsClient,
        FixtureCCDClient,
        FixtureUniChemClient,
    ):
        monkeypatch.setattr(client, "__init__", forbidden)
    monkeypatch.setattr(sabueso, "resolve", forbidden)
    monkeypatch.setattr(sabueso, "refresh_card", forbidden)


def card(originals, key="trials"):
    return Card.from_dict(deepcopy(originals[key]))


def frames(selection, **options):
    cursor, result, seen = None, [], set()
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
        assert cursor not in seen
        seen.add(cursor)


def test_human_question_and_agent_share_unchanged_native_view(originals):
    molecule = card(originals)
    before = molecule.to_dict()
    native = molecule.clinical()
    explorer = molecule.explore()
    human = explorer.view("clinical")
    machine = explorer.access.select("clinical")
    assert (
        explorer.answer("clinical_context").result_ref
        == human.result_ref
        == machine.result_ref
    )
    assert human.native_payload == native
    assert human.outcome["status"] == "ok"
    assert "clinical" in explorer.capabilities["scientific_topics"]
    assert "clinical_context" in explorer.capabilities["question_keys"]
    assert len(human.filter("kind", equals="clinical_indication").items()) == 4
    assert len(human.filter("kind", equals="clinical_registry_record").items()) == 16
    assert len(human.filter("kind", equals="clinical_trial_citation").items()) == sum(
        len(i["trials"]) for i in native["indications"]
    )
    assert len(frames(machine)) == len(human.items()) == machine.count
    assert molecule.to_dict() == before
    assert "efficacy" in repr(human).lower()
    assert "clinical" in human._repr_html_().lower()


def test_native_indication_order_distinct_terms_and_each_citation_are_preserved(
    originals,
):
    native = card(originals).clinical()
    view = card(originals).explore().view("clinical")
    indications = view.filter("kind", equals="clinical_indication")
    assert [item.open().native_payload for item in indications.items()] == native[
        "indications"
    ]
    same_heading = [
        item
        for item in indications.items()
        if item.open().native_payload["mesh_heading"] == "Chagas Disease"
    ]
    assert len(same_heading) == 2
    assert len({item.cells["disease_ref"].value for item in same_heading}) == 2
    citations = view.filter("kind", equals="clinical_trial_citation").filter(
        "trial_ref", equals="nct:NCT00123916"
    )
    assert len(citations.items()) == 2
    assert len({item.item_ref for item in citations.items()}) == 2
    assert len({item.cells["disease_ref"].value for item in citations.items()}) == 2


def test_registry_support_roles_keep_molecule_and_nct_subjects(originals):
    view = card(originals).explore().view("clinical")
    item = view.filter("kind", equals="clinical_registry_record").items()[0]
    records = item.support[0]["source_assertions"]
    assert {r["role"] for r in records} == {"indication_citation", "registry_record"}
    assert {r["state"] for r in records} == {"present"}
    explanation = item.explain()
    assert explanation.back() is item._view
    assert explanation.native_payload["item"] == item.open().native_payload
    subjects = {row.open().native_payload["subject_ref"] for row in explanation.items()}
    assert subjects == {"chembl:CHEMBL110", item.cells["trial_ref"].value}


def test_each_source_and_registry_link_returns_to_exact_filtered_question(originals):
    explorer = card(originals).explore()
    question = explorer.answer("clinical_context")
    selected = question.filter("kind", equals="clinical_trial_citation").filter(
        "trial_ref", equals="nct:NCT00123916"
    )
    for item in selected.items():
        links = item.related()
        assert links.back() is selected
        assert links.request == question.request
        for link in links.items():
            opened = link.open()
            assert opened.back() is links
            assert opened.request == question.request
            if link.cells["role"].value == "registry_record":
                assert opened.native_payload["trial"] == item.cells["trial_ref"].value
            if link.cells["role"].value == "source":
                assert opened.native_payload["subject_ref"] == "chembl:CHEMBL110"
        assert item.open().back() is selected


@pytest.mark.parametrize(
    "name,state,count",
    [
        ("bare", "not_queried", 0),
        ("indications", "not_queried", 16),
        ("limited", "partial", 14),
        ("failed", "unavailable", 16),
    ],
)
def test_unqueried_limited_and_failed_registry_scope_stays_distinct(
    originals, name, state, count
):
    molecule = card(originals, name)
    explorer = molecule.explore()
    view = explorer.view("clinical")
    assert view.native_payload == molecule.clinical()
    assert len(view.native_payload["not_fetched"]) == count
    registry = next(
        row for row in view.coverage["rows"] if row["area"] == "relationships.tested_in"
    )
    assert registry["state"] == state
    assert view.outcome["status"] == "partial"
    selected = view.filter("kind", equals="no_such_row")
    assert not selected.items()
    assert selected.outcome == view.outcome
    machine = explorer.access.select("clinical", where={"kind": "no_such_row"}).page()
    assert machine["outcome"] == view.outcome


def test_source_retrieval_not_found_keeps_original_citation(originals):
    data = deepcopy(originals["trials"])
    trial = next(r for r in data["relationship_store"] if r["predicate"] == "tested_in")
    trial["qualifiers"] = {"basis": "chembl_drug_indication", "registry": "not_found"}
    source_ids = {
        r["id"]
        for r in data["source_assertion_store"]
        if r["source"]["name"] == "ClinicalTrials.gov"
    }
    trial["source_assertion_ids"] = [
        ref for ref in trial["source_assertion_ids"] if ref not in source_ids
    ]
    explorer = Card.from_dict(data).explore()
    view = (
        explorer.view("clinical")
        .filter("kind", equals="clinical_registry_record")
        .filter("trial_ref", equals=trial["object_ref"])
    )
    (item,) = view.items()
    assert item.cells["registry_state"].value == "not_found"
    assert item.cells["registry_status"].value is None
    assert item.cells["registry_status"].state == "not_applicable"
    assert item.open().native_payload["registry"] == "not_found"
    assert {r["role"] for r in item.support[0]["source_assertions"]} == {
        "indication_citation"
    }


@pytest.mark.parametrize("change", ["subject", "field", "source", "missing"])
def test_misbound_or_missing_registry_support_remains_explicit(originals, change):
    data = deepcopy(originals["trials"])
    source = next(
        r
        for r in data["source_assertion_store"]
        if r["source"]["name"] == "ClinicalTrials.gov"
    )
    if change == "subject":
        source["subject_ref"] = "nct:NCT00000000"
    elif change == "field":
        source["field_path"] = "relationships.investigated_for"
    elif change == "source":
        source["source"]["name"] = "Synthetic other provider"
    else:
        data["source_assertion_store"].remove(source)
    view = Card.from_dict(data).explore().view("clinical")
    item = next(
        item
        for item in view.filter("kind", equals="clinical_registry_record").items()
        if any(r["id"] == source["id"] for r in item.support[0]["source_assertions"])
    )
    assert item.cells["registry_state"].value == "unverified"
    assert item.cells["state"].value == "partial"
    support = next(
        r for r in item.support[0]["source_assertions"] if r["id"] == source["id"]
    )
    assert support["state"] == (
        "not_retained" if change == "missing" else "role_mismatch"
    )
    assert view.outcome["status"] == "partial"
    assert any(link.cells["role"].value == "source" for link in item.related().items())


def test_projection_membership_and_order_match_human_subset(originals):
    explorer = card(originals).explore()
    human = (
        explorer.view("clinical")
        .filter("kind", equals="clinical_indication")
        .sort("disease_term", descending=True)
    )
    selected = explorer.access.select(
        "clinical",
        fields=["disease_term", "chembl_max_phase"],
        where={"kind": "clinical_indication"},
        order_by={"column": "disease_term", "descending": True},
    )
    rows = frames(selected, limit=2)
    assert [row["cells"]["disease_term"]["value"] for row in rows] == [
        item.cells["disease_term"].value for item in human.items()
    ]
    refs = [row["item_ref"] for row in rows[:2]]
    members = explorer.access.select("clinical", item_refs=refs)
    assert {row["item_ref"] for row in frames(members)} == set(refs)
    for row in rows:
        assert set(row["cells"]) == {"disease_term", "chembl_max_phase"}
        assert (
            explorer.inspect(locator=row["interpretation_location"]).native_payload
            == row["interpretation"]
        )
        assert explorer.access.explain(row["item_ref"]).count > 0


@pytest.mark.parametrize("operand", [4, 4.0, None])
def test_phase_equality_keeps_operand_types(originals, operand):
    explorer = card(originals).explore()
    human = explorer.view("clinical")
    expected_refs = {
        item.item_ref
        for item in human.items()
        if type(item.cells["chembl_max_phase"].value) is type(operand)
        and item.cells["chembl_max_phase"].value == operand
    }
    selected = explorer.access.select("clinical", where={"chembl_max_phase": operand})
    assert {row["item_ref"] for row in frames(selected)} == expected_refs
    assert {
        item.item_ref
        for item in human.filter("chembl_max_phase", equals=operand).items()
    } == expected_refs


@pytest.mark.parametrize(
    "kwargs",
    [
        {"where": {"chembl_max_phase": True}},
        {"where": {"chembl_max_phase": float("nan")}},
        {"where": {"citation_count": 1.0}},
        {"where": {"registry_phases": "PHASE3"}},
        {"where": {"trial_ref": 1}},
        {"where": {"other": None}},
        {"order_by": {"column": "registry_phases"}},
        {"order_by": {"column": "chembl_max_phase", "unit": "nM"}},
        {"fields": ["kind", "kind"]},
        {"options": {"fetch": True}},
    ],
)
def test_invalid_machine_requests_fail_before_native_read(
    originals, monkeypatch, kwargs
):
    explorer = card(originals).explore()
    monkeypatch.setattr(Card, "clinical", forbidden)
    with pytest.raises(ArgumentError):
        explorer.access.select("clinical", **kwargs)


def test_cached_navigation_never_rereads_science_and_remains_captured(
    originals, monkeypatch
):
    molecule = card(originals)
    explorer = molecule.explore()
    view = explorer.view("clinical")
    expected = deepcopy(view.native_payload)
    monkeypatch.setattr(Card, "clinical", forbidden)
    monkeypatch.setattr(Card, "knowledge_state", forbidden)
    molecule.relationship_store = type(molecule.relationship_store)()
    assert explorer.answer("clinical_context").native_payload == expected
    assert len(frames(explorer.access.select("clinical"))) == len(view.items())
    for item in view.items()[:3]:
        assert item.open().back() is view
        assert item.explain().back() is view
        assert item.related().back() is view


def test_foreign_capture_item_membership_and_cursors_are_refused(originals):
    first = card(originals).explore()
    second = card(originals, "limited").explore()
    selected = first.access.select("clinical")
    row = frames(selected)[0]
    with pytest.raises(ArgumentError):
        second.access.select("clinical", item_refs=[row["item_ref"]])
    cursor = selected.page(limit=1)["page"]["next_cursor"]
    with pytest.raises(ArgumentError):
        second.access.select("clinical").page(cursor=cursor)


def test_deferred_machine_values_keep_exact_paths_and_interpretation(originals):
    explorer = card(originals).explore()
    selected = explorer.access.select("clinical")
    rows = frames(selected, limit=1, max_bytes=7000)
    assert any(not row["value_included"] for row in rows)
    for row in rows:
        if not row["value_included"]:
            assert "interpretation" not in row
            recovered = explorer.inspect(locator=row["value_location"]).native_payload
            assert recovered["interpretation"]["scope"]
            assert recovered["kind"] == row["kind"]


def test_live_saving_is_truthfully_deferred_until_independent_reader(
    originals, tmp_path
):
    explorer = card(originals).explore()
    view = explorer.view("clinical")
    selection = explorer.access.select("clinical")
    assert not view.capabilities["save"]
    assert not selection.capabilities["save"]
    for output, operation in [
        ("human.json", view.save),
        ("machine.json", selection.save),
        ("detail.json", view.items()[0].open().save),
    ]:
        with pytest.raises(StorageError):
            operation(tmp_path / output)
        assert not (tmp_path / output).exists()


def test_nonmolecule_profile_refuses_clinical_native_reader(monkeypatch):
    explorer = Card(
        meta={"card_id": "sabueso:protein:uniprot:P60174", "entity_type": "protein"}
    ).explore()
    monkeypatch.setattr(Card, "clinical", forbidden)
    with pytest.raises(ArgumentError):
        explorer.access.select("clinical")


def test_missing_request_ledger_is_unknown_and_native_coverage_is_unchanged(originals):
    data = deepcopy(originals["bare"])
    data["quality"].pop("enrichments")
    molecule = Card.from_dict(data)
    native_rows = [
        r
        for r in molecule.knowledge_state()["rows"]
        if r["area"]
        in (
            "clinical.max_phase",
            "relationships.investigated_for",
            "relationships.tested_in",
        )
    ]
    view = molecule.explore().view("clinical")
    assert view.coverage["native_rows"] == native_rows
    requests = [
        r for r in view.coverage["rows"] if r["area"].startswith("relationships.")
    ]
    assert {r["state"] for r in requests} == {"not_recorded"}
    assert {r["count"] for r in requests} == {None}
    assert view.coverage["request_scope_rule"] == "clinical_query_scope@1"
    assert view.outcome["status"] == "partial"


def test_citation_does_not_project_registry_status_as_an_unknown_source_value(
    originals,
):
    view = card(originals).explore().view("clinical")
    citation = view.filter("kind", equals="clinical_trial_citation").items()[0]
    assert citation.cells["registry_state"].value == "received"
    assert citation.cells["registry_status"].state == "not_applicable"
    assert citation.cells["registry_phases"].state == "not_applicable"


@pytest.mark.parametrize("descending", [False, True])
def test_sort_keeps_unknowns_last_and_preserves_exact_back_origin(
    originals, descending
):
    view = card(originals).explore().view("clinical")
    ordered = view.sort("chembl_max_phase", descending=descending)
    values = [item.cells["chembl_max_phase"].value for item in ordered.items()]
    native = view.native_payload
    phase_count = (
        1
        + len(native["indications"])
        + sum(len(i["trials"]) for i in native["indications"])
    )
    assert values[:phase_count] == [4.0] * phase_count
    assert all(value is None for value in values[phase_count:])
    assert ordered.back() is view
    assert ordered.result_ref == view.result_ref
    assert ordered.native_payload == view.native_payload


def test_source_locators_and_explanations_preserve_full_original_bytes(originals):
    molecule = card(originals)
    data = molecule.to_dict()
    expected_sources = {r["id"]: r for r in data["source_assertion_store"]}
    expected_relationships = {r["id"]: r for r in data["relationship_store"]}
    explorer = molecule.explore()
    view = explorer.view("clinical")
    for item in view.items():
        for record in item.support[0]["source_assertions"]:
            assert (
                explorer.inspect(locator=record["location"]).native_payload
                == expected_sources[record["id"]]
            )
        for record in item.support[0]["relationships"]:
            assert (
                explorer.inspect(locator=record["location"]).native_payload
                == expected_relationships[record["id"]]
            )
    assert molecule.to_dict() == data


def test_each_citation_links_its_complete_indication_without_copying_the_trial_list(
    originals,
):
    view = card(originals).explore().view("clinical")
    for citation in view.filter("kind", equals="clinical_trial_citation").items():
        item = citation.open().native_payload
        assert "indication" not in item and "trials" not in item
        original_link = next(
            link
            for link in citation.related().items()
            if link.cells["role"].value == "original_indication"
        )
        original = original_link.open().native_payload
        assert original["disease"] == citation.cells["disease_ref"].value
        assert original["trials"][item["citation_position"]] == item["nct_id"]


def test_missing_indication_phase_is_unknown_on_its_citation_occurrences(originals):
    data = deepcopy(originals["indications"])
    for relationship in data["relationship_store"]:
        if relationship["predicate"] == "investigated_for":
            relationship["qualifiers"].pop("max_phase", None)
    # Explicit synthetic missing-field control; original public bytes stay fixed.
    view = Card.from_dict(data).explore().view("clinical")
    for citation in view.filter("kind", equals="clinical_trial_citation").items():
        assert citation.cells["chembl_max_phase"].value is None
        assert citation.cells["chembl_max_phase"].state == "unknown"


def test_large_integer_phase_operand_is_a_typed_nonmatching_selection(originals):
    explorer = card(originals).explore()
    value = 10**400
    assert (
        explorer.access.select("clinical", where={"chembl_max_phase": value}).count == 0
    )
    assert (
        not explorer.view("clinical").filter("chembl_max_phase", equals=value).items()
    )
