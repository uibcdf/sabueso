"""Independent interval cases and public original-policy compatibility (#184/#185)."""

import gzip
import hashlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest
import pyunitwizard as puw

from sabueso.core.bioactivity_class_v4 import RULE, classify
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No acquisition during scientific interpretation")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.mark.parametrize(
    "value,relation,expected",
    [
        (1, "=", "active"), (10, "=", "active"),
        (11, "=", "weak"), (100, "=", "weak"), (101, "=", "inactive"),
        (10, "<", "active"), (10, "<=", "active"),
        (11, "<", "inconclusive"), (100, "<=", "inconclusive"),
        (101, "<", "inconclusive"),
        (10, ">", "inconclusive"), (99, ">", "inconclusive"),
        (100, ">", "inactive"), (100, ">=", "inconclusive"),
        (101, ">=", "inactive"), (1, "~", "inconclusive"),
        (1, "!=", "inconclusive"),
    ],
)  # fmt: skip
def test_all_permitted_values_must_fit_one_band(value, relation, expected):
    answer = classify(
        {"type": "IC50", "value": value, "units": "uM", "relation": relation}
    )
    assert answer["class"] == expected
    assert answer["interpretation"]


@pytest.mark.parametrize(
    "low,high,expected",
    [(1, 10, "active"), (11, 100, "weak"), (101, 200, "inactive"),
     (10, 11, "inconclusive"), (100, 101, "inconclusive"),
     (100, 100, "weak"), (11, 10, "inconclusive")],
)  # fmt: skip
def test_closed_ranges_keep_their_boundaries(low, high, expected):
    answer = classify(
        {
            "type": "IC50",
            "value": low,
            "upper_value": high,
            "units": "uM",
            "relation": "=",
        }
    )
    assert answer["class"] == expected


@pytest.mark.parametrize("value", [True, -1, 0, float("nan"), float("inf"), "invalid"])
def test_invalid_potency_never_becomes_a_band(value):
    assert (
        classify({"type": "IC50", "value": value, "units": "uM"})["class"]
        == "inconclusive"
    )


@pytest.mark.parametrize("relation", ["=", ">", ">=", "<", "<=", "~"])
@pytest.mark.parametrize("value", [40, 70])
def test_single_point_is_not_a_dose_response_curve(value, relation):
    answer = classify(
        {"type": "Inhibition", "value": value, "units": "%", "relation": relation},
        "Assay at 1 uM substrate; inhibition measured at 100 uM compound",
    )
    assert answer["class"] == "inconclusive"
    assert answer["test_concentration_state"] == "not_interpreted"
    assert "test_concentration" not in answer
    assert "tested-compound dose" in answer["interpretation"]


@pytest.mark.parametrize("units,value", [("nM", 100000), ("uM", 100), ("mM", 0.1)])
def test_equivalent_units_preserve_the_inclusive_lower_bound(units, value):
    assert (
        classify({"type": "Ki", "value": value, "units": units, "relation": ">="})[
            "class"
        ]
        == "inconclusive"
    )


@pytest.mark.parametrize("field", ["uncertainty", "normalized_uncertainty"])
def test_uninterpreted_uncertainty_does_not_become_an_exact_point(field):
    answer = classify(
        {"type": "Kd", "value": 5, "units": "uM", field: {"kind": "unspecified"}}
    )
    assert answer["class"] == "inconclusive"
    assert answer["basis"] == "uncertainty_not_interpreted"


def synthetic_card():
    card = Card(
        meta={"card_id": "sabueso:protein:uniprot:P52270", "entity_type": "protein"}
    )
    qualifiers = {
        "source": "Synthetic",
        "activity_id": "synthetic-inhibition",
        "measurement": {
            "type": "Inhibition",
            "value": 40,
            "units": "%",
            "relation": ">",
        },
        "assay": {
            "id": "synthetic:assay",
            "relationship_type": "D",
            "description": "Inhibition at 200 uM",
        },
        "document": {},
    }
    assertion = make_source_assertion(
        "relationships.has_bioactivity",
        deepcopy(qualifiers),
        "Synthetic",
        "synthetic-inhibition",
        "2026-11-04",
    )
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(
        make_relationship(
            "uniprot:P52270",
            "has_bioactivity",
            "chembl:CHEMBL_SYNTHETIC",
            qualifiers,
            [assertion["id"]],
        )
    )
    return card


def test_public_default_explains_the_change_and_preserves_original_policy_and_card():
    card = synthetic_card()
    before = card.to_dict()
    old = card.bioactivities(classification_rule="bioactivity_class@3")
    current = card.bioactivities()
    assert current == card.bioactivities(classification_rule=RULE)
    old_item, new_item = old["items"][0], current["items"][0]
    assert old_item["class"] == "inactive"
    assert new_item["class"] == "inconclusive"
    original, new = old_item["measurements"][0], new_item["measurements"][0]
    for field in [
        "relationship_id",
        "activity_id",
        "relation",
        "value",
        "units",
        "source",
        "group",
    ]:
        assert new[field] == original[field]
    assert puw.get_value(new["normalized"], to_unit="percent") == 40
    assert current["classification"]["rule"] == RULE
    assert "single_point_policy" in current["classification"]["parameters"]
    assert current["classification"]["parameters"]["unused_thresholds"] == [
        "single_point_min"
    ]
    explanation = card.explain_bioactivity(
        new_item["molecule_ref"], classification_rule=RULE
    )
    assert explanation["item"] == new_item
    assert explanation["classification"] == current["classification"]
    assert explanation["rule"]["rule"] == "bioactivity_explanation@2"
    assert explanation["rule"]["parameters"]["classification_rule"] == RULE
    assert explanation["records"]
    assert (
        card.explain_bioactivity(
            old_item["molecule_ref"], classification_rule="bioactivity_class@3"
        )["rule"]["rule"]
        == "bioactivity_explanation@1"
    )
    assert card.bioactivities(classification_rule="bioactivity_class@3") == old
    assert card.to_dict() == before


@pytest.mark.parametrize("rule", [None, 4, True, "@4", "bioactivity_class@5"])
@pytest.mark.parametrize("skip", [False, True])
def test_unknown_rule_is_refused_even_when_digestion_is_skipped(rule, skip):
    card = Card()
    with pytest.raises(ArgumentError):
        card.bioactivities(classification_rule=rule, skip_digestion=skip)
    with pytest.raises(ArgumentError):
        card.explain_bioactivity(
            "chembl:CHEMBL_SYNTHETIC", classification_rule=rule, skip_digestion=skip
        )


@pytest.mark.parametrize(
    "thresholds",
    [
        {"active_max": "200 uM"},
        {"weak_max": "0 uM"},
        {"active_max": "nan uM"},
        {"single_point_min": "101 percent"},
    ],
)
def test_invalid_thresholds_are_refused_even_on_an_empty_card(thresholds):
    with pytest.raises(ArgumentError):
        Card().bioactivities(classification_rule=RULE, thresholds=thresholds)


def molecule_deck():
    anchor = "inchikey:ABCDEFGHIJKLMN-AAAAAAAAAA-N"
    molecule = Card(
        meta={
            "card_id": f"sabueso:small_molecule:{anchor}",
            "entity_type": "small_molecule",
        }
    )
    assertion = make_source_assertion(
        "relationships.same_as",
        {"object_ref": anchor},
        "Synthetic",
        "synthetic-identity",
        "2026-11-04",
    )
    molecule.source_assertion_store.add(assertion)
    molecule.relationship_store.add(
        make_relationship(
            "chembl:CHEMBL_SYNTHETIC", "same_as", anchor, {}, [assertion["id"]]
        )
    )
    return molecule, Deck([molecule])


def test_current_table_explains_uncomputed_dose_without_relabelling_it_as_missing():
    card = synthetic_card()
    (row,) = card.table("bioactivities")
    assert row["class"] == "inconclusive"
    assert row["classification_rule"] == RULE
    assert row["test_concentration"] is None
    assert row["test_concentration_state"] == "not_interpreted"
    assert "tested-compound dose" in row["interpretation"]
    assert (row["value"], row["units"], row["relation"]) == (40, "%", ">")
    (legacy,) = card.table("bioactivities", classification_rule="bioactivity_class@3")
    assert legacy["class"] == "inactive"
    assert "interpretation" not in legacy
    _, deck = molecule_deck()
    (ligand,) = card.table("ligands", deck=deck)
    assert ligand["classification_rule"] == RULE
    assert ligand["class"] == "inconclusive"
    assert "not efficacy" in ligand["interpretation"]
    (original,) = card.table(
        "ligands", deck=deck, classification_rule="bioactivity_class@3"
    )
    assert original["class"] == "inactive" and "interpretation" not in original


@pytest.mark.parametrize(
    "rule,expected,explanation_rule",
    [
        ("bioactivity_class@4", "inconclusive", "ligand_deck_explanation@3"),
        ("bioactivity_class@3", "inactive", "ligand_deck_explanation@2"),
    ],
)
def test_ligand_views_explanations_and_comparisons_share_the_selected_policy(
    rule, expected, explanation_rule
):
    card = synthetic_card()
    molecule, deck = molecule_deck()
    before = card.to_dict(), molecule.to_dict()
    view = card.ligands(deck, classification_rule=rule)
    why = card.explain_ligand(molecule.id, deck, classification_rule=rule)
    comparison = card.compare_ligands(deck, card, deck, classification_rule=rule)
    assert view["items"][0]["bioactivity"]["class"] == expected
    assert (
        why["classification"] == view["classification"] == comparison["classification"]
    )
    assert why["rule"]["rule"] == explanation_rule
    assert why["items"][0]["item"] == view["items"][0]
    child = why["items"][0]["bioactivities"][0]
    assert child["classification"]["rule"] == rule
    assert child["item"]["class"] == expected
    assert comparison["shared"][0]["self"]["bioactivity"]["class"] == expected
    assert comparison["shared"][0]["other"]["bioactivity"]["class"] == expected
    if rule == RULE:
        assert card.ligands(deck) == view
        assert card.explain_ligand(molecule.id, deck) == why
        assert card.compare_ligands(deck, card, deck) == comparison
    assert (card.to_dict(), molecule.to_dict()) == before


def original_packet_fixture():
    path = Path(__file__).with_name("data") / "bioactivity_default_legacy_v1.json.gz"
    raw = path.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "f816d19d582dc0da113627995ffede51ce84b420a8331b1b71543f1e019fbeec"
    )
    data = json.loads(gzip.decompress(raw))
    assert data["producer"]["head"] == "129020182555787d3cab58cc110e7a707fc5e553"
    return data


@pytest.mark.parametrize("mapping", [f"packet_aspects@{n}" for n in range(6, 15)])
def test_original_packet_mappings_keep_the_original_activity_rule(mapping):
    import sabueso
    from sabueso.core.packets import _facts, as_stated, full_rules

    original = original_packet_fixture()
    card = Card.from_dict(original["card"])
    actual = as_stated(_facts("bioactivities", card, mapping=mapping))
    expected = original["full"]["facts"]["bioactivities"]["subject"]
    assert actual["classification"]["sabueso_version"] == sabueso.__version__
    assert expected["classification"]["sabueso_version"] == original["producer"]["sdk"]

    def without_derivation_producer(value):
        if isinstance(value, dict):
            derived = {
                "rule",
                "inputs",
                "parameters",
                "sabueso_version",
            } <= value.keys()
            return {
                key: without_derivation_producer(child)
                for key, child in value.items()
                if not (derived and key == "sabueso_version")
            }
        if isinstance(value, list):
            return [without_derivation_producer(child) for child in value]
        return value

    # Recomputing an original rule records the current SDK as its producer.
    # Only that derivation stamp may differ; source versions/inputs stay exact.
    # The separate saved-reader test below requires exact original byte meaning.
    assert without_derivation_producer(actual) == without_derivation_producer(expected)
    assert full_rules(mapping)["bioactivities"][0] == "bioactivity_class@3"
    assert card.bioactivities()["classification"]["rule"] == RULE


@pytest.mark.parametrize("detail", ["full", "index"])
def test_genuine_old_packet_reading_is_inert_and_new_packets_declare_new_science(
    detail, tmp_path, monkeypatch
):
    from sabueso import KnowledgeStore
    from sabueso.core import packets

    original = original_packet_fixture()
    card = Card.from_dict(original["card"])
    old = packets.KnowledgePacket(deepcopy(original[detail]))
    store = KnowledgeStore(tmp_path / "history.db")
    assert store.save(card) == old.entities["subject"]["ref"]
    ref = store.save_packet(old, "original_activity")
    with monkeypatch.context() as patch:

        def forbidden(*args, **kwargs):
            raise AssertionError("Original packet reading cannot recompute science")

        patch.setattr(Card, "bioactivities", forbidden)
        patch.setattr(packets, "_facts", forbidden)
        restored = store.load_packet(ref)
        assert restored.to_dict() == original[detail]
        assert restored.snapshot_id() == old.snapshot_id()
    current = packets.compose_packet(
        packets.KnowledgeQuery(
            "uniprot:P52270", aspects=["bioactivities"], detail=detail
        ),
        card,
    )
    assert current.to_dict()["aspect_mapping"] == "packet_aspects@16"
    assert current.same_knowledge(old) is None
    activity = current.facts["bioactivities"]["subject"]
    if detail == "full":
        assert activity["classification"]["rule"] == RULE
    else:
        assert activity["full_rules"][0] == RULE
    current_ref = store.save_packet(current, "current_activity")
    assert store.load_packet(current_ref).to_dict() == current.to_dict()
