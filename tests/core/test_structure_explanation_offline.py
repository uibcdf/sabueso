"""Inventory explanations: source support, unknowns and historical card states (#91)."""

from copy import deepcopy

import pytest
import pyunitwizard as puw

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

TC = "sabueso:protein:uniprot:P52270"
HS = "sabueso:protein:uniprot:P60174"


def _build(accession, **options):
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"),
        rcsb_client=FixtureRCSBClient("temp_data", **options),
    )
    card, _ = sabueso.resolve(accession, resolver=resolver, structures="all")
    return card


@pytest.fixture(scope="module")
def deck():
    return Deck([_build("P52270"), _build("P60174")])


def test_a_shared_group_has_pinned_support_for_every_member(
    deck, tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    def no_network(*args, **kwargs):
        raise AssertionError("Explaining stored knowledge must not ask a source")

    monkeypatch.setattr(_http, "urlopen", no_network)
    regions = {TC: [96], HS: [95]}
    why = deck.explain(TC, structure_ref="pdb:1SUX", regions=regions)
    assert why["status"] == "grouped" and why["group"]["shared"]
    assert why["group"] == next(
        group
        for group in deck.structure_inventory(regions=regions)["states"]
        if "pdb:1SUX" in group["structures"][TC]
    )
    assert {rule["rule"] for rule in why["rules"]} == {
        "structure_coverage_class@1",
        "structure_state@2",
        "structure_inventory@1",
    }
    assert why["rule"]["rule"] == "structure_inventory_explanation@1"
    assert why["rule"]["inputs"] == [card.pinned_ref() for card in deck.cards]
    assert why["item"]["complete_chains"] == ["A", "B"]
    assert {member["structure_ref"] for member in why["members"]} == {
        "pdb:1SUX",
        "pdb:1HTI",
    }
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save_deck(deck, "pair")
    for member in why["members"]:
        assert store.relationship(member["relationship_ref"]) == member["relationship"]
        assert member["support_basis"] == "relationship"
        assert {sa["source"] for sa in member["source_assertions"]} == {
            "UniProt",
            "RCSB PDB",
        }
        for assertion in member["source_assertions"]:
            stored = store.source_assertion(assertion["source_assertion_ref"])
            assert assertion["asserted_value"] == stored["asserted_value"]
            assert assertion["subject_ref"] == stored["subject_ref"]
            # RCSB statements remain about a PDB record, UniProt's about the protein.
            assert assertion["subject_ref"].startswith(
                "pdb:" if assertion["source"] == "RCSB PDB" else "uniprot:"
            )
        context = member["reference_context"]
        assert context["basis"] == "stored_card_fields"
        assert {field["field_path"] for field in context["fields"]} == {
            "sequence.length",
            "sequence.primary",
        }
        for field in context["fields"]:
            assert field["source_assertions"]
            for assertion in field["source_assertions"]:
                assert store.source_assertion(assertion["source_assertion_ref"])


def test_author_assemblies_and_disagreements_stay_inspectable(deck):
    why = deck.explain(TC, structure_ref="pdb:2V5B")
    assert why["group"]["state"]["oligomer"] == "Monomer"
    assert why["item"]["oligomer_basis"] == "author"
    assert why["item"]["oligomer_disagreement"] is True
    support = next(m for m in why["members"] if m["structure_ref"] == "pdb:2V5B")
    assert {
        a["oligomeric_state"]
        for a in support["relationship"]["qualifiers"]["assemblies"]
    } == {
        "Monomer",
        "Homo 2-mer",
    }


def test_excluded_unknown_and_unrecorded_are_distinct(deck):
    excluded = deck.explain(HS, structure_ref="pdb:1KLG")
    assert (excluded["status"], excluded["reason"]) == (
        "excluded",
        "fragment_or_peptide",
    )
    assert excluded["item"]["coverage_class"] == "fragment_or_peptide"
    assert excluded["members"] and excluded["group"] is None
    included = deck.explain(HS, structure_ref="pdb:1KLG", include_fragments=True)
    assert included["status"] == "grouped"
    assert included["group"]["state"]["coverage"] == "fragment_or_peptide"
    unknown = deck.explain(TC, structure_ref="pdb:1CI1")
    assert (unknown["status"], unknown["reason"]) == ("not_inventoried", "not_found")
    assert unknown["item"]["state"]["sequence"] is None
    assert unknown["group"] is None
    unrecorded = deck.explain(TC, structure_ref="pdb:9ZZZ")
    assert unrecorded["status"] == "not_on_card"
    assert unrecorded["item"] is None and unrecorded["members"] == []
    missing_card = deck.explain(
        "sabueso:protein:uniprot:P00000", structure_ref="pdb:1SUX"
    )
    assert missing_card["reason"] == "card_not_in_deck"


def test_a_pinned_deck_keeps_its_explanation_after_another_acquisition(deck, tmp_path):
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    old_ref = store.save_deck(deck, "pair")
    before = deck.explain(TC, structure_ref="pdb:1SUX")
    # A new source acquisition fails for this structure, while the prior pin remains.
    with pytest.warns(EnrichmentFailedWarning):
        fresh = _build("P52270", failing={"1SUX"})
    store.save_deck(Deck([fresh, deck.cards[1]]), "pair")
    latest = store.load_deck("pair").explain(TC, structure_ref="pdb:1SUX")
    assert (latest["status"], latest["reason"]) == ("not_inventoried", "error")
    assert latest["card_ref"] != before["card_ref"]
    historical = store.load_deck(old_ref).explain(TC, structure_ref="pdb:1SUX")
    assert historical["group"] == before["group"]
    assert historical["card_ref"] == before["card_ref"]
    for member in historical["members"]:
        assert store.relationship(member["relationship_ref"]) == member["relationship"]
        for assertion in member["source_assertions"]:
            assert (
                store.source_assertion(assertion["source_assertion_ref"])[
                    "asserted_value"
                ]
                == assertion["asserted_value"]
            )
    # Another store cannot substitute its latest card for an absent historical pin.
    other = sabueso.KnowledgeStore(tmp_path / "other.db")
    other.save_deck(Deck([fresh, deck.cards[1]]), "pair")
    with pytest.raises(StorageError):
        other.load_deck(old_ref)


def test_a_source_not_requested_is_not_reported_as_not_found():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = sabueso.resolve("P52270", resolver=resolver)
    why = Deck([card]).explain(card.id, structure_ref="pdb:1SUX")
    assert (why["status"], why["reason"]) == ("not_inventoried", "not_requested")
    assert why["members"][0]["source_assertions"]
    assert why["item"]["state"]["sequence"] is None


def test_maps_and_regions_are_recorded_and_equal_numbers_are_not_equivalence(deck):
    window = {p: p for p in range(95, 116)}
    options = dict(
        regions={TC: [[95, 96]], HS: [105]},
        group_by=(
            "method",
            "coverage",
            "sequence",
            "ligands:interest",
            "substitutions",
        ),
        residue_maps={TC: window},
        reference=HS,
    )
    why = deck.explain(TC, structure_ref="pdb:4HHP", **options)
    assert why["group"]["shared"]
    assert why["group"]["state"]["substitutions"] == ["105D"]
    assert why["rule"]["parameters"]["residue_maps"] == {TC: window}
    assert why["rule"]["parameters"]["regions"] == {TC: [95, 96], HS: [105]}
    assert why["item"]["substitutions_in_reference"][0]["reference_position"] == 105
    unmapped = deck.explain(TC, structure_ref="pdb:4HHP", group_by=options["group_by"])
    assert not unmapped["group"]["shared"]


def test_support_preserves_unknown_inputs_conflicts_and_detaches_from_cards(deck):
    card = Card.from_dict(deck.cards[0].to_dict())
    (rel,) = card.relationships("has_structure", object_ref="pdb:2V5B")
    rel["qualifiers"]["ligands"] = None
    rel["qualifiers"].pop("observed")
    rel["qualifier_conflicts"] = {"method": ["X-ray", "NMR"]}
    card.quality["conflicts"] = [{"field": "sequence.primary", "type": "disagreement"}]
    before = card.snapshot_id()
    why = Deck([card]).explain(TC, structure_ref="pdb:2V5B", regions=[15])
    assert why["item"]["state"]["ligands"] is None
    assert why["item"]["missing_in_region"] is None
    (member,) = why["members"]
    assert "observed" not in member["relationship"]["qualifiers"]
    assert member["relationship"]["qualifier_conflicts"] == {"method": ["X-ray", "NMR"]}
    assert member["reference_context"]["fields"][1]["conflicts"]
    member["relationship"]["qualifiers"]["assemblies"].clear()
    member["reference_context"]["fields"][0]["node"]["value"] = 0
    member["source_assertions"][0]["asserted_value"] = "changed by the reader"
    assert card.snapshot_id() == before


def test_resolution_keeps_its_unit_under_another_session_policy(deck):
    with puw.context(standard_units=["nm", "ps", "K", "mole", "dalton"]):
        why = deck.explain(TC, structure_ref="pdb:1SUX")
    assert puw.get_value(
        why["item"]["resolution"], to_unit="angstrom"
    ) == pytest.approx(2.0)
    member = next(m for m in why["members"] if m["structure_ref"] == "pdb:1SUX")
    assert member["relationship"]["qualifiers"]["resolution"] == {
        "value": 2.0,
        "unit": "angstrom",
    }


@pytest.mark.parametrize(
    "options",
    [
        {"structure_ref": "1SUX"},
        {"structure_ref": "pdb.ligand:ATP"},
        {"structure_ref": "pdb:1SUX", "group_by": "oligmoer"},
        {"structure_ref": "pdb:1SUX", "reference": "unknown"},
        {"structure_ref": "pdb:1SUX", "regions": [[5, 2]]},
        {"structure_ref": "pdb:1SUX", "residue_maps": {TC: {0: 1}}},
        {"group_by": "method"},
    ],
)
def test_wrong_selectors_and_options_are_refused(deck, options):
    with pytest.raises(ArgumentError):
        deck.explain(TC, **options)


def test_membership_explanation_stays_available_and_structure_refs_are_normalized(deck):
    assert deck.explain(TC)["in_deck"]
    assert deck.explain(TC, structure_ref=" PDB:1sux ")["structure_ref"] == "pdb:1SUX"
    with pytest.raises(ArgumentError):
        Deck([deck.cards[0], deepcopy(deck.cards[0])]).explain(
            TC, structure_ref="pdb:1SUX"
        )
