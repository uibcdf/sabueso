"""Molecular request counts and clinical scopes never invent evaluated absence (#122)."""

from copy import deepcopy

import ackredit
import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.clinicaltrials import FixtureClinicalTrialsClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

ANCHOR = "sabueso:small_molecule:inchikey:XBNHRNFODJOFRU-UHFFFAOYSA-N"


def synthetic(*records):
    return Card(
        meta={"card_id": ANCHOR, "entity_type": "small_molecule"},
        quality={"enrichments": deepcopy(list(records))},
    )


def rows(card):
    return {(r["area"], r["source"]): r for r in card.knowledge_state()["rows"]}


@pytest.fixture(scope="module")
def molecules():
    clients = {
        "chembl_client": FixtureChEMBLClient("temp_data"),
        "ccd_client": FixtureCCDClient("temp_data"),
        "unichem_client": FixtureUniChemClient("temp_data"),
        "clinicaltrials_client": FixtureClinicalTrialsClient("temp_data"),
    }
    return {
        "bts": sabueso.resolve("chembl:CHEMBL1161789", **clients)[0],
        "pga": sabueso.resolve("pdb.ligand:PGA", **clients)[0],
        "benznidazole": sabueso.resolve(
            "chembl:CHEMBL110", indications=True, trials={}, **clients
        )[0],
    }


def test_public_received_identity_is_known_and_missing_batch_members_stay_partial(
    molecules,
):
    bts = molecules["bts"]
    original = bts.to_dict()
    state = rows(bts)
    for source in ("PDB CCD", "UniChem"):
        row = state[("records", source)]
        assert (row["state"], row["count"], row["release"]) == ("known", 1, None)
        answer = bts.explain_knowledge_state("records", source)
        (explained,) = answer["rows"]
        assert explained["row"] == row
        (count_input,) = explained["classification_inputs"]["count_inputs"]
        assert count_input["basis"] == (
            "native_compound_id" if source == "UniChem" else "native_record_ids"
        )
        assert count_input["count"] == 1
        assert explained["stored_knowledge_context"]["relationships"]
        assert (
            explained["stored_knowledge_context"]["request_membership"]
            == "not_recorded"
        )
    assert bts.to_dict() == original
    pga = rows(molecules["pga"])[("records", "PDB CCD")]
    assert (pga["state"], pga["count"], pga["basis"]["missing"]) == (
        "partial",
        1,
        ["2PL"],
    )


@pytest.mark.parametrize(
    "source,report,state,count,basis",
    [
        (
            "PDB CCD",
            {"status": "added", "records": ["BTS", "BTS"]},
            "known",
            1,
            "native_record_ids",
        ),
        (
            "PDB CCD",
            {"status": "added", "records": []},
            "not_stated",
            0,
            "native_record_ids",
        ),
        (
            "PDB CCD",
            {"status": "added", "records": ["BTS"], "missing": ["2PL"]},
            "partial",
            1,
            "native_record_ids",
        ),
        (
            "PDB CCD",
            {"status": "partial", "records": [], "missing": ["BTS"]},
            "partial",
            0,
            "native_record_ids",
        ),
        (
            "UniChem",
            {
                "status": "added",
                "uci": 336651,
                "linked": {"chembl": ["CHEMBL1161789"], "pubchem": ["162569"]},
            },
            "known",
            1,
            "native_compound_id",
        ),
        (
            "UniChem",
            {"status": "added", "linked": {"pubchem": ["162569"]}},
            "known",
            None,
            "count_not_reported",
        ),
        ("ChEMBL", {"status": "added"}, "known", None, "count_not_reported"),
        (
            "ChEMBL",
            {"status": "added", "count": None},
            "known",
            None,
            "count_not_reported",
        ),
        ("ChEMBL", {"status": "partial"}, "partial", None, "count_not_reported"),
        (
            "ChEMBL",
            {"status": "added", "count": 0, "truncated": True},
            "partial",
            0,
            "reported_count",
        ),
        (
            "ChEMBL",
            {"status": "not_found", "records": [], "missing": ["CHEMBL_SYNTHETIC"]},
            "not_stated",
            0,
            "request_not_counted",
        ),
        (
            "PDB CCD",
            {"status": "error", "detail": "request failed"},
            "unavailable",
            None,
            "request_not_counted",
        ),
    ],
)
def test_reported_scope_and_count_basis_are_preserved(
    source, report, state, count, basis
):
    report = {"source": source, **report}
    card = synthetic(report)
    answer = card.explain_knowledge_state("records", source)
    assert answer["state_rule"]["rule"] == "knowledge_state@5"
    assert answer["rule"]["rule"] == "knowledge_state_explanation@2"
    (explained,) = answer["rows"]
    assert (explained["row"]["state"], explained["row"]["count"]) == (state, count)
    assert explained["classification_inputs"]["reports"][0]["record"] == report
    assert explained["classification_inputs"]["count_inputs"][0]["basis"] == basis
    assert not card.source_assertion_store.to_list()
    if count is None and state != "unavailable":
        assert explained["row"]["basis"]["count_unknown_for"] == [0]
    if report.get("missing"):
        assert explained["row"]["basis"]["missing"] == report["missing"]


@pytest.mark.parametrize("bad_count", [True, -1, float("nan"), float("inf"), "3"])
def test_unusable_counts_do_not_become_evaluated_empty(bad_count):
    row = rows(synthetic({"source": "ChEMBL", "status": "added", "count": bad_count}))[
        ("records", "ChEMBL")
    ]
    assert (row["state"], row["count"]) == ("known", None)


def test_mixed_unknown_counts_failures_and_subtotals_are_not_silent_zeroes():
    card = synthetic(
        {"source": "ChEMBL", "status": "added", "count": 2},
        {"source": "ChEMBL", "status": "added"},
        {"source": "ChEMBL", "status": "error", "identifier": "unavailable-batch"},
    )
    row = rows(card)[("records", "ChEMBL")]
    assert (row["state"], row["count"]) == ("partial", None)
    assert row["basis"]["reported_count_subtotal"] == 2
    assert row["basis"]["count_unknown_for"] == [1]
    assert row["basis"]["unavailable_for"] == ["unavailable-batch"]


@pytest.mark.parametrize("status", [None, "unsupported_outcome"])
def test_unrecognized_outcome_is_not_evaluated_absence(status):
    row = rows(synthetic({"source": "ChEMBL", "status": status}))[("records", "ChEMBL")]
    assert (row["state"], row["count"]) == ("unavailable", None)
    assert row["basis"]["unrecognized_outcomes"] == [0]


def test_unqueried_identity_and_clinical_requests_remain_separate():
    card = synthetic(
        {"source": "ChEMBL", "status": "added", "records": ["CHEMBL110"]},
        {
            "source": "ChEMBL",
            "data": "indications",
            "status": "not_queried",
            "detail": "not requested",
        },
    )
    state = rows(card)
    assert state[("records", "ChEMBL")]["state"] == "known"
    assert state[("relationships.investigated_for", "ChEMBL")]["state"] == "not_queried"
    assert state[("relationships.investigated_for", "ChEMBL")]["count"] is None


def test_molecular_identity_indications_and_trials_have_separate_counting_inputs():
    card = synthetic(
        {"source": "ChEMBL", "status": "added", "records": ["CHEMBL110"]},
        {
            "source": "ChEMBL",
            "data": "indications",
            "status": "added",
            "records": ["CHEMBL110"],
            "count": 4,
        },
        {
            "source": "ClinicalTrials.gov",
            "status": "added",
            "records": 16,
            "count": 10,
            "truncated": True,
            "missing": ["NCT00000001"],
        },
    )
    state = rows(card)
    assert state[("records", "ChEMBL")]["count"] == 1
    assert state[("relationships.investigated_for", "ChEMBL")]["count"] == 4
    assert state[("relationships.tested_in", "ClinicalTrials.gov")]["count"] == 10
    assert (
        state[("relationships.tested_in", "ClinicalTrials.gov")]["state"] == "partial"
    )
    for area, source, index in [
        ("records", "ChEMBL", 0),
        ("relationships.investigated_for", "ChEMBL", 1),
        ("relationships.tested_in", "ClinicalTrials.gov", 2),
    ]:
        explained = card.explain_knowledge_state(area, source)["rows"][0]
        assert explained["classification_inputs"]["enrichment_indexes"] == [index]
        assert (
            explained["classification_inputs"]["count_inputs"][0]["enrichment_index"]
            == index
        )
    # A count of requested study ids is not a count of returned studies.
    card.quality["enrichments"][-1].pop("count")
    assert (
        rows(card)[("relationships.tested_in", "ClinicalTrials.gov")]["count"] is None
    )


def test_public_clinical_support_and_inert_pinned_explanations_survive_new_head(
    molecules, tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    card = molecules["benznidazole"]
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    pin = store.save(card)
    before = card.to_dict()
    original = card.explain_knowledge_state("relationships.investigated_for", "ChEMBL")
    (indications,) = original["rows"]
    assert (indications["row"]["state"], indications["row"]["count"]) == ("known", 4)
    assert indications["stored_knowledge_context"]["relationships"]
    for link in indications["stored_knowledge_context"]["relationships"]:
        assert store.relationship(link["relationship_ref"]) == link["relationship"]
        for statement in link["source_assertions"]:
            assert (
                store.source_assertion(statement["source_assertion_ref"])["source"][
                    "version"
                ]
                == "ChEMBL_37"
            )
    later = store.load(pin)
    later.quality["enrichments"].append(
        {
            "source": "ChEMBL",
            "data": "indications",
            "status": "error",
            "detail": "later failed batch",
        }
    )
    later_pin = store.save(later)
    assert later_pin != pin
    assert (
        rows(store.load(later_pin))[("relationships.investigated_for", "ChEMBL")][
            "state"
        ]
        == "partial"
    )
    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("no acquisition")
    )
    with ackredit.session("inert original molecular knowledge state"):
        credit = ackredit.get_attribution().to_dict()
        restored = store.load(pin).explain_knowledge_state(
            "relationships.investigated_for", "ChEMBL"
        )
        assert ackredit.get_attribution().to_dict() == credit
    assert restored == original and card.to_dict() == before
    assert restored["card_ref"] == pin
    assert (
        rows(store.load(pin))[("relationships.tested_in", "ClinicalTrials.gov")][
            "count"
        ]
        == 16
    )
