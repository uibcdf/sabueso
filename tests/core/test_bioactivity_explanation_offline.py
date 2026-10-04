"""Derived measurement groups/classes retain exact pinned inputs and decisions."""

from copy import deepcopy

import ackredit
import argdigest
import pytest
import pyunitwizard as puw

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.measurements import measurement_groups
from sabueso.core.quantities import normalized_measurement
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.bindingdb import FixtureBindingDBClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.unichem import FixtureUniChemClient

MOLECULE = "chembl:CHEMBL_SYNTHETIC"


def synthetic():
    return Card(
        meta={"card_id": "sabueso:protein:uniprot:P52270", "entity_type": "protein"}
    )


def record(
    card,
    activity,
    value=1000,
    *,
    source="ChEMBL",
    molecule=MOLECULE,
    units="nM",
    relation="=",
    assignment="D",
    copy_of=None,
    measurement=None,
    description=None,
    publication="1",
):
    m = {
        "type": "IC50",
        "value": value,
        "units": units,
        "relation": relation,
        "normalized": normalized_measurement(value, units),
    }
    m.update(measurement or {})
    q = {
        "source": source,
        "activity_id": activity,
        "measurement": m,
        "assay": {
            "id": f"assay:{activity}",
            "relationship_type": assignment,
            "description": description,
        },
        "document": {"pubmed": publication},
    }
    if copy_of:
        q["copy_of"] = copy_of
    sa = make_source_assertion(
        "relationships.has_bioactivity",
        deepcopy(q),
        source,
        str(activity),
        "2026-01-01",
    )
    sa["source"]["version"] = f"original-{source}"
    card.source_assertion_store.add(sa)
    rel = make_relationship(
        "uniprot:P52270", "has_bioactivity", molecule, q, [sa["id"]]
    )
    card.relationship_store.add(rel)
    return card.relationship_store.get(rel["id"])


@pytest.fixture(scope="module", params=["P52270", "P60174"])
def public_card(request):
    return sabueso.resolve(
        request.param,
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        chembl={},
        chembl_client=FixtureChEMBLClient("temp_data"),
        bindingdb={},
        bindingdb_client=FixtureBindingDBClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
    )[0]


def test_public_measurement_groups_and_classes_retain_actual_view_and_source_versions(
    public_card,
):
    before = public_card.to_dict()
    identity = measurement_groups(public_card)
    group = identity["groups"][0]
    answer = public_card.explain_measurement(group["id"])
    assert answer["group"] == group
    assert answer["grouping_rule"] == identity["rule"]
    assert answer["rule"]["rule"] == "measurement_group_explanation@1"
    assert answer["status"] == "on_card" and not answer["gaps"]
    assert all(j["accepted"] and j["basis"] == "statement" for j in answer["joins"])
    assert {a["source"] for r in answer["records"] for a in r["source_assertions"]} == {
        "BindingDB",
        "ChEMBL",
    }
    item = next(
        i
        for i in public_card.bioactivities()["items"]
        if any(m["group"] == group["id"] for m in i["measurements"])
    )
    explained = public_card.explain_bioactivity(item["molecule_ref"])
    assert explained["rule"]["rule"] == "bioactivity_explanation@1"
    assert explained["item"]["classes"] == item["classes"]
    assert explained["item"]["class"] == item["class"]
    assert explained["item"]["measurement_count"] == len(explained["groups"])
    assert {
        a["version"]
        for r in explained["records"]
        for a in r["source_assertions"]
        if a["source"] == "ChEMBL"
    } == {"ChEMBL_37"}
    assert public_card.to_dict() == before


def test_coarser_precision_is_a_quantity_and_does_not_merge_molecules():
    card = synthetic()
    a = record(card, 1, 62, measurement={"stated_value": "62"})
    b = record(card, 2, 62.46, source="BindingDB")
    answer = card.explain_measurement(a["id"])
    assert set(answer["group"]["records"]) == {a["id"], b["id"]}
    (join,) = answer["joins"]
    assert join["precision"]["tolerance"] == {"value": 0.5, "unit": "nanomolar"}
    assert join["shared_publications"] == [{"namespace": "pubmed", "id": "1"}]
    assert join["shared_molecule_keys"] == [MOLECULE]
    assert answer["context"]["entities"][MOLECULE]["records"] == [MOLECULE]


def test_declared_copy_never_votes_with_original_and_retains_dropped_relation():
    card = synthetic()
    original = record(card, 1, 100000, relation=">")
    copied = record(
        card,
        2,
        100000,
        source="PubChem",
        relation=None,
        copy_of={"source": "ChEMBL", "activity_id": 1},
    )
    answer = card.explain_bioactivity(MOLECULE)
    (group,) = answer["groups"]
    assert group["voters"] == [original["id"]] and group["class"] == "inactive"
    assert copied["id"] in group["records"] and answer["item"]["measurement_count"] == 1
    (join,) = group["joins"]
    assert join["selector"] == {"basis": "source_activity_id", "precision_used": False}
    assert join["precision"] is None
    assert answer["item"]["record_count"] == 2


def test_copy_only_group_is_explicitly_a_fallback_not_confirmation():
    card = synthetic()
    copied = record(
        card, 2, source="PubChem", copy_of={"source": "ChEMBL", "assay": "missing"}
    )
    answer = card.explain_bioactivity(MOLECULE)
    (group,) = answer["groups"]
    assert group["basis"] == "copies_only" and group["voters"] == [copied["id"]]
    assert group["identity"]["sources"] == ["PubChem"]
    assert (
        answer["measurement_identity"]["unresolved_copies"][0]["record"] == copied["id"]
    )


def test_disagreement_within_one_measurement_is_inconclusive():
    card = synthetic()
    record(card, 1, 10000, measurement={"stated_value": "10000"})
    record(card, 2, 10000.4, source="BindingDB")
    answer = card.explain_bioactivity(MOLECULE)
    assert answer["item"]["class"] == "inconclusive"
    assert answer["groups"][0]["voter_classes"] == ["active", "weak"]
    assert answer["item"]["classes"] == {"inconclusive": 1}


def test_strongest_class_preserves_discordance_between_distinct_groups():
    card = synthetic()
    record(card, 1, 1000)
    record(card, 2, 200000)
    answer = card.explain_bioactivity(MOLECULE)
    assert answer["item"]["class"] == "active" and answer["item"]["discordant"]
    assert answer["item"]["classes"] == {"active": 1, "inactive": 1}
    assert len(answer["groups"]) == 2


def test_indirect_filter_and_nondefault_quantity_policy_are_exact():
    card = synthetic()
    direct = record(card, 1, 5, units="uM")
    indirect = record(card, 2, 0.1, units="uM", assignment="H")
    policy = {"active_max": puw.quantity(1, "micromolar")}
    answer = card.explain_bioactivity(MOLECULE, thresholds=policy)
    assert answer["item"]["class"] == "weak"
    assert answer["classification"]["parameters"]["active_max"] == {
        "value": 1,
        "unit": "micromolar",
    }
    assert answer["record_decisions"] == [
        {"relationship_id": direct["id"], "included": True, "molecule_ref": MOLECULE},
        {
            "relationship_id": indirect["id"],
            "included": False,
            "reason": "target_assignment:H",
        },
    ]
    assert (
        answer["records"][0]["relationship"]["qualifiers"]["measurement"]["units"]
        == "uM"
    )
    assert (
        card.explain_bioactivity(MOLECULE, include_indirect=True, thresholds=policy)[
            "item"
        ]["class"]
        == "active"
    )


@pytest.mark.parametrize(
    "kind", ["range", "single_point", "unknown_units", "not_determined"]
)
def test_classification_branches_keep_raw_inputs_and_quantity_boundaries(kind):
    card = synthetic()
    options = {
        "range": dict(
            value=1000,
            measurement={
                "upper_value": 20000,
                "normalized_upper": {"value": 20000, "unit": "nanomolar"},
            },
        ),
        "single_point": dict(
            value=75,
            units="%",
            measurement={"type": "Inhibition"},
            description="Inhibition at 20 uM",
        ),
        "unknown_units": dict(units="unrecognized"),
        "not_determined": dict(value=None, measurement={"comment": "not determined"}),
    }
    rel = record(card, 1, **options[kind])
    answer = card.explain_bioactivity(MOLECULE)
    (measurement,) = answer["item"]["measurements"]
    assert (
        measurement["basis"]
        == {
            "range": "potency_range",
            "single_point": "single_point",
            "unknown_units": "unknown_units",
            "not_determined": "no_value",
        }[kind]
    )
    assert answer["records"][0]["relationship"] == rel
    if kind == "range":
        assert measurement["class"] == "inconclusive"
        assert (
            puw.get_value(
                puw.convert(measurement["normalized_upper"], to_unit="micromolar")
            )
            == 20
        )
    if kind == "single_point":
        assert measurement["class"] == "weak"
        assert (
            puw.get_value(
                puw.convert(measurement["test_concentration"], to_unit="micromolar")
            )
            == 20
        )


def test_ambiguity_never_selects_a_candidate_and_keeps_candidate_support():
    card = synthetic()
    a = record(card, 1)
    b = record(card, 2)
    reader = record(card, 3, source="BindingDB")
    answer = card.explain_measurement(reader["id"])
    assert answer["group"]["records"] == [reader["id"]]
    assert answer["diagnostics"]["ambiguous"][0]["candidates"] == sorted(
        [a["id"], b["id"]]
    )
    assert {r["relationship"]["id"] for r in answer["context"]["relationships"]} == {
        a["id"],
        b["id"],
    }
    assert answer["joins"] == []


def test_named_assay_copy_uses_precision_only_to_select_between_candidates():
    card = synthetic()
    original = record(card, 1, 1000)
    other = record(card, 2, 2000)
    other["qualifiers"]["assay"]["id"] = original["qualifiers"]["assay"]["id"]
    copied = record(
        card,
        3,
        1000,
        source="PubChem",
        copy_of={"source": "ChEMBL", "assay": "assay:1"},
    )
    answer = card.explain_measurement(copied["id"])
    assert set(answer["group"]["records"]) == {copied["id"], original["id"]}
    (join,) = answer["joins"]
    assert join["selector"] == {"basis": "named_assay_molecule", "precision_used": True}
    assert join["precision"]["tolerance"]["unit"] == "nanomolar"
    assert other["id"] in {
        r["relationship"]["id"] for r in answer["context"]["relationships"]
    }


def test_connectivity_assay_copy_retains_review_without_entity_identity_merge():
    card = synthetic()
    a = "inchikey:ABCDEFGHIJKLMN-AAAAAAAAAA-N"
    b = "inchikey:ABCDEFGHIJKLMN-BBBBBBBBBB-N"
    original = record(card, 1, molecule=a)
    copied = record(
        card,
        2,
        molecule=b,
        source="PubChem",
        copy_of={"source": "ChEMBL", "assay": "assay:1"},
    )
    answer = card.explain_measurement(copied["id"])
    assert set(answer["group"]["records"]) == {original["id"], copied["id"]}
    assert answer["joins"][0]["selector"]["basis"] == "named_assay_connectivity"
    assert answer["joins"][0]["shared_molecule_keys"] == []
    assert answer["diagnostics"]["review"][0]["reason"] == "stereo_differs"
    assert {
        key for key in answer["context"]["entities"] if key.startswith("inchikey:")
    } == {a, b}


def test_stored_identity_context_points_to_original_serialized_glossary():
    card = synthetic()
    rel = record(card, 1)
    card.register_identity(
        "inchikey:ABCDEFGHIJKLMN-AAAAAAAAAA-N",
        [MOLECULE],
        "small_molecule",
        {"basis": "synthetic source-stated lookup"},
    )
    answer = card.explain_measurement(rel["id"])
    (stored,) = answer["context"]["stored_identities"]
    locator = stored["locator"]
    assert card.to_dict()[locator["field_path"]][locator["key"]] == stored["record"]
    assert stored["source_assertion_membership"] == "not_recorded"


def test_consistency_checks_keep_other_record_support_and_do_not_correct_values():
    card = synthetic()
    a = record(card, 1, 100, measurement={"pchembl": 1})
    b = record(card, 2, 100000)
    answer = card.explain_bioactivity(MOLECULE)
    assert [c["rule"] for c in answer["checks"]] == [
        "pchembl_consistency@1",
        "unit_scale_discrepancy@1",
    ]
    flags = answer["item"]["measurements"][0]["flags"]
    assert "pchembl_inconsistent" in flags and "scale_discrepancy:3:2" in flags
    assert {r["relationship"]["id"] for r in answer["records"]} == {a["id"], b["id"]}
    assert answer["records"][0]["relationship"]["qualifiers"]["measurement"][
        "value"
    ] in {100, 100000}


def test_missing_lineage_is_partial_and_preserves_the_class():
    card = synthetic()
    rel = record(card, 1)
    rel["source_assertion_ids"] = ["SA_missing"]
    answer = card.explain_bioactivity(MOLECULE)
    assert answer["status"] == "partial" and answer["item"]["class"] == "active"
    assert not answer["records"][0]["source_assertions"][0]["found"]
    rel["source_assertion_ids"] = []
    assert (
        card.explain_measurement(rel["id"])["gaps"][0]["reason"]
        == "no_relationship_support"
    )


def test_unknown_item_is_not_on_card_and_does_not_imply_inactivity():
    card = synthetic()
    assert card.explain_bioactivity(MOLECULE)["item"] is None
    assert card.explain_bioactivity(MOLECULE)["status"] == "not_on_card"
    assert card.explain_measurement("REL_missing")["group"] is None
    assert card.explain_measurement("MG_0123456789abcdef")["status"] == "not_on_card"


def test_reading_is_inert_and_answers_are_detached(monkeypatch):
    from sabueso.tools.db import _http

    card = synthetic()
    rel = record(card, 1)
    before = card.to_dict()
    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("no acquisition")
    )
    with ackredit.session("inert bioactivity explanation"):
        credited = ackredit.get_attribution().to_dict()
        answer = card.explain_bioactivity(MOLECULE)
        measurement = card.explain_measurement(rel["id"])
        assert ackredit.get_attribution().to_dict() == credited
    answer["records"][0]["relationship"]["qualifiers"].clear()
    measurement["context"]["entities"].clear()
    assert card.to_dict() == before


def test_historical_pin_retains_original_support_after_later_card_changes(tmp_path):
    card = synthetic()
    rel = record(card, 1)
    store = sabueso.KnowledgeStore(tmp_path / "bioactivities.db")
    pin = store.save(card)
    expected = card.explain_measurement(rel["id"])
    expected_class = card.explain_bioactivity(MOLECULE)["item"]["class"]
    record(card, 2, 200000)
    store.save(card)
    restored = store.load(pin)
    assert restored.explain_measurement(rel["id"]) == expected
    assert restored.explain_bioactivity(MOLECULE)["item"]["class"] == expected_class
    link = expected["records"][0]
    assert store.relationship(link["relationship_ref"]) == link["relationship"]
    sa = link["source_assertions"][0]
    assert (
        store.source_assertion(sa["source_assertion_ref"])["source"]["version"]
        == "original-ChEMBL"
    )


@pytest.mark.parametrize(
    "method,value",
    [
        ("explain_measurement", None),
        ("explain_measurement", "activity:1"),
        ("explain_measurement", "MG_bad"),
        ("explain_measurement", "REL_foo#SA_x"),
        ("explain_bioactivity", None),
        ("explain_bioactivity", "CHEMBL1"),
        ("explain_bioactivity", "chembl:two words"),
    ],
)
def test_native_selectors_are_checked_through_argdigest(method, value):
    with pytest.raises(ArgumentError):
        getattr(synthetic(), method)(value)


def test_explanation_options_use_existing_argument_contracts():
    card = synthetic()
    with pytest.raises(ArgumentError):
        card.explain_bioactivity(MOLECULE, include_indirect="yes")
    with pytest.raises(ArgumentError):
        card.explain_bioactivity(MOLECULE, thresholds={"active_max": 1})
    with pytest.raises(argdigest.UnknownArgumentError):
        card.explain_measurement("REL_missing", surprise=True)
