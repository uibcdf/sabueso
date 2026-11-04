"""A copy cannot bypass a resolved original's direct-target scope (#188)."""

import socket
from copy import deepcopy

import pytest

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.core.quantities import normalized_measurement
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

RULE = "bioactivity_target_scope@2"
MOLECULE = "chembl:CHEMBL_SYNTHETIC"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No source access during target selection")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def card():
    return Card(
        meta={"card_id": "sabueso:protein:uniprot:P60174", "entity_type": "protein"}
    )


def record(
    c,
    activity,
    *,
    source="ChEMBL",
    assignment="D",
    copy_of=None,
    subject="uniprot:P60174",
):
    q = {
        "source": source,
        "activity_id": activity,
        "measurement": {
            "type": "Ki",
            "value": 15000,
            "units": "nM",
            "relation": "=",
            "normalized": normalized_measurement(15000, "nM"),
        },
        "assay": {"id": "synthetic:assay", "relationship_type": assignment},
        "document": {"pubmed": "1"},
    }
    if copy_of:
        q["copy_of"] = copy_of
    assertion = make_source_assertion(
        "relationships.has_bioactivity",
        deepcopy(q),
        source,
        str(activity),
        "2026-11-04",
    )
    c.source_assertion_store.add(assertion)
    rel = make_relationship(subject, "has_bioactivity", MOLECULE, q, [assertion["id"]])
    c.relationship_store.add(rel)
    return rel["id"]


@pytest.mark.parametrize(
    "measurement_rule", ["measurement_identity@1", "measurement_identity@2"]
)
def test_a_copy_of_an_indirect_original_cannot_enter_direct_only_output(
    measurement_rule,
):
    c = card()
    original = record(c, 1, assignment="H")
    copied = record(
        c, 2, source="PubChem BioAssay", copy_of={"source": "ChEMBL", "activity_id": 1}
    )
    before = c.to_dict()
    legacy = c.bioactivities(measurement_rule=measurement_rule)
    assert len(legacy["items"]) == 1
    current = c.bioactivities(measurement_rule=measurement_rule, target_scope_rule=RULE)
    assert not current["items"] and len(current["excluded"]) == 2
    decision = current["target_selection"]["records"][copied]
    assert decision["state"] == "assignment_disagreement"
    assert (
        decision["mapped_assignment"] == "D"
        and decision["originals"][0]["mapped_assignment"] == "H"
    )
    assert decision["originals"][0]["relationship_id"] == original
    assert not decision["direct_supported"]
    wider = c.bioactivities(
        include_indirect=True, measurement_rule=measurement_rule, target_scope_rule=RULE
    )
    assert sum(i["record_count"] for i in wider["items"]) == 2
    explanation = c.explain_bioactivity(
        MOLECULE, measurement_rule=measurement_rule, target_scope_rule=RULE
    )
    assert explanation["status"] == "outside_scope" and explanation["item"] is None
    assert explanation["rule"]["rule"] == "bioactivity_explanation@4"
    assert {r["relationship"]["id"] for r in explanation["records"]} == {
        original,
        copied,
    }
    assert (
        c.to_dict() == before
        and c.bioactivities(measurement_rule=measurement_rule) == legacy
    )


@pytest.mark.parametrize(
    "original_assignment,copy_assignment,expected",
    [
        ("D", "D", True),
        ("D", None, True),
        ("H", "H", False),
        ("H", None, False),
        (None, "D", False),
        ("D", "H", False),
    ],
)
def test_direct_scope_requires_original_context_and_retains_missing_or_different_values(
    original_assignment, copy_assignment, expected
):
    c = card()
    record(c, 1, assignment=original_assignment)
    copied = record(
        c,
        2,
        source="PubChem BioAssay",
        assignment=copy_assignment,
        copy_of={"source": "ChEMBL", "activity_id": 1},
    )
    view = c.bioactivities(target_scope_rule=RULE)
    decision = view["target_selection"]["records"][copied]
    assert decision["direct_supported"] is expected
    assert decision["mapped_assignment"] == copy_assignment
    wider = c.bioactivities(include_indirect=True, target_scope_rule=RULE)
    assert sum(i["record_count"] for i in wider["items"]) == 2


def test_numeric_correspondence_cannot_resolve_an_absent_declared_original():
    c = card()
    original = record(c, 1)
    copied = record(
        c,
        2,
        source="PubChem BioAssay",
        copy_of={"source": "ChEMBL", "activity_id": 999},
    )
    view = c.bioactivities(
        measurement_rule="measurement_identity@1", target_scope_rule=RULE
    )
    included = {m["relationship_id"] for i in view["items"] for m in i["measurements"]}
    assert included == {original}
    assert not view["target_selection"]["records"][copied]["direct_supported"]
    assert (
        view["target_selection"]["records"][copied]["reason"] == "original_not_resolved"
    )


def test_foreign_subject_copy_chains_and_cycles_never_supply_missing_direct_scope():
    c = card()
    record(c, 1, subject="uniprot:P52270")
    copied = record(
        c, 2, source="PubChem BioAssay", copy_of={"source": "ChEMBL", "activity_id": 1}
    )
    view = c.bioactivities(target_scope_rule=RULE)
    assert (
        not view["items"]
        and view["target_selection"]["records"][copied]["state"]
        == "subject_disagreement"
    )
    c = card()
    record(c, 1, copy_of={"source": "PubChem BioAssay", "activity_id": 2})
    record(
        c, 2, source="PubChem BioAssay", copy_of={"source": "ChEMBL", "activity_id": 1}
    )
    assert not c.bioactivities(target_scope_rule=RULE)["items"]
    c = card()
    record(c, 1)
    record(
        c, 2, source="PubChem BioAssay", copy_of={"source": "ChEMBL", "activity_id": 1}
    )
    chained = record(
        c, 3, source="Other", copy_of={"source": "PubChem BioAssay", "activity_id": 2}
    )
    assert c.bioactivities(target_scope_rule=RULE)["target_selection"]["records"][
        chained
    ]["direct_supported"]


def molecule_deck():
    anchor = "inchikey:AAAAAAAAAAAAAA-AAAAAAAAAA-N"
    molecule = Card(
        meta={
            "card_id": "sabueso:small_molecule:" + anchor,
            "entity_type": "small_molecule",
        }
    )
    a = make_source_assertion(
        "relationships.same_as",
        {"record": MOLECULE, "anchor": anchor},
        "Synthetic",
        "molecule",
        "2026-11-04",
    )
    molecule.source_assertion_store.add(a)
    molecule.relationship_store.add(
        make_relationship(MOLECULE, "same_as", anchor, source_assertion_ids=[a["id"]])
    )
    return molecule, Deck([molecule])


def test_ligand_answers_explanations_comparison_and_tables_share_target_scope():
    c = card()
    record(c, 1, assignment="H")
    record(
        c, 2, source="PubChem BioAssay", copy_of={"source": "ChEMBL", "activity_id": 1}
    )
    molecule, deck = molecule_deck()
    view = c.ligands(deck, target_scope_rule=RULE)
    assert (
        view["items"][0]["bioactivity"] is None
        and view["items"][0]["excluded_measurements"] == 2
    )
    explanation = c.explain_ligand(molecule.id, deck, target_scope_rule=RULE)
    assert explanation["rule"]["rule"] == "ligand_deck_explanation@5"
    assert explanation["items"][0]["item"] == view["items"][0]
    assert explanation["target_selection"] == view["target_selection"]
    compared = c.compare_ligands(deck, c, deck, target_scope_rule=RULE)
    assert compared["shared"][0]["self"] == compared["shared"][0]["other"]
    assert compared["target_selection"]["self"] == view["target_selection"]
    assert compared["target_selection"]["other"] == view["target_selection"]
    row = c.table("ligands", deck=deck, target_scope_rule=RULE)[0]
    assert row["target_scope_rule"] == RULE
    direct = card()
    record(direct, 1)
    row = direct.table("bioactivities", target_scope_rule=RULE)[0]
    assert (
        row["target_scope_rule"] == RULE
        and row["target_scope_state"] == "mapped_direct"
    )


@pytest.mark.parametrize("bad", [None, True, 2, [], {}, "bioactivity_target_scope@3"])
@pytest.mark.parametrize(
    "method",
    [
        "bioactivities",
        "explain_bioactivity",
        "ligands",
        "explain_ligand",
        "compare_ligands",
    ],
)
def test_unknown_selector_is_refused_before_pin_capture_without_digestion(bad, method):
    c = card()

    def forbidden():
        raise AssertionError("No pin capture for unsupported target policy")

    c.pinned_ref = forbidden
    deck = Deck([])
    args = {
        "bioactivities": [],
        "explain_bioactivity": [MOLECULE],
        "ligands": [deck],
        "explain_ligand": [
            "sabueso:small_molecule:inchikey:AAAAAAAAAAAAAA-AAAAAAAAAA-N",
            deck,
        ],
        "compare_ligands": [deck, c, deck],
    }[method]
    with pytest.raises(ArgumentError, match="target_scope_rule"):
        getattr(c, method)(*args, target_scope_rule=bad, skip_digestion=True)


def test_missing_focal_identity_and_ambiguous_original_do_not_establish_direct_scope():
    c = card()
    record(c, 1)
    c.meta["card_id"] = None
    view = c.bioactivities(target_scope_rule=RULE)
    assert not view["items"] and view["target_selection"]["focal_ref"] is None
    assert {r["reason"] for r in view["target_selection"]["records"].values()} == {
        "focal_protein_reference_not_stated"
    }
    c = card()
    record(c, 1)
    record(c, 2)
    copied = record(
        c,
        3,
        source="PubChem BioAssay",
        copy_of={"source": "ChEMBL", "assay": "synthetic:assay"},
    )
    view = c.bioactivities(target_scope_rule=RULE)
    assert not view["target_selection"]["records"][copied]["direct_supported"]
    assert (
        view["target_selection"]["records"][copied]["copy_resolution"]["reason"]
        == "ambiguous_original"
    )


def test_mapped_assignment_and_source_record_stay_unchanged_and_default_is_original():
    c = card()
    record(c, 1, assignment="H")
    record(
        c, 2, source="PubChem BioAssay", copy_of={"source": "ChEMBL", "activity_id": 1}
    )
    before = c.to_dict()
    legacy = c.bioactivities()
    assert legacy == c.bioactivities(target_scope_rule="bioactivity_target_scope@1")
    assert "target_selection" not in legacy
    c.bioactivities(target_scope_rule=RULE)
    assert c.to_dict() == before
    with pytest.raises(ArgumentError, match="target_scope_rule"):
        c.bioactivities(target_scope_rule="current")
