"""SKEMPI 2.0: interface mutations joined by stated chains, placed by stated numbering (#83).

Barnase (P00648) and barstar, on the frozen SKEMPI rows of their complexes. Barnase's
author numbering (the mature protein, 1-110) is UniProt's 48-157, so a mutation can
only be placed through the numbering RCSB states.
"""

import json
import math

import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.core.card import Card
from sabueso.mappings.skempi import _temperature, _value, map_rows
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.skempi import FixtureSKEMPIClient, get_mutations

ENTRY = json.loads(open("temp_data/P00648.json", encoding="utf-8").read())


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _card(resolver, structures=(), client=None):
    card, _ = sabueso.resolve(
        "P00648",
        resolver=resolver,
        structures=list(structures),
        skempi=True,
        skempi_client=client or FixtureSKEMPIClient("temp_data"),
    )
    return card


def _mutations(card, structure="pdb:1BRS"):
    return [
        (m, item)
        for item in card.get("annotations.interface_mutations")["value"]
        if item["structure"] == structure
        for m in item["mutations"]
    ]


def test_rows_join_only_through_the_chains_uniprot_states(resolver):
    card = _card(resolver)
    items = card.get("annotations.interface_mutations")["value"]
    assert len(items) == 105
    # UniProt states chains A/B/C of each entry are barnase; D is barstar.
    assert {tuple(i["protein_chains"]) for i in items} == {("A",)}
    sides = {m["on"] for i in items for m in i["mutations"]}
    assert sides == {"this_protein", "partner"}
    partner = [m for i in items for m in i["mutations"] if m["on"] == "partner"]
    assert {m["not_placed"] for m in partner} == {"partner_chain"}


def test_without_the_structure_nothing_is_placed(resolver):
    card = _card(resolver)
    mine = [m for m, _ in _mutations(card) if m["on"] == "this_protein"]
    assert mine and {m["not_placed"] for m in mine} == {"structure_not_loaded"}
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "SKEMPI"]
    assert (record["status"], record["version"], record["placed"]) == (
        "added",
        "2.0",
        0,
    )
    assert len(record["checksum"]) == 64


def test_placed_through_rcsb_author_numbering_and_a_matching_residue(resolver):
    card = _card(resolver, ["1BRS"])
    sequence = ENTRY["sequence"]["value"]
    placed = [m for m, _ in _mutations(card) if "location" in m]
    assert placed
    for m in placed:
        position = m["location"]["start"]
        assert sequence[position - 1] == m["original"]
        assert m["placed_via"] == {
            "rule": "rcsb_author_numbering@1",
            "structure": "pdb:1BRS",
        }
    k27 = [m for m in placed if (m["original"], m["author_residue"]) == ("K", "27")]
    assert k27 and {m["location"]["start"] for m in k27} == {74}
    # Other barnase complexes were not loaded: their mutations stay unplaced.
    other = [m for m, _ in _mutations(card, "pdb:1B2S") if m["on"] == "this_protein"]
    assert {m["not_placed"] for m in other} == {"structure_not_loaded"}


def test_a_residue_that_does_not_match_is_never_placed():
    row = {
        "#Pdb": "1BRS_A_D",
        "Mutation(s)_PDB": "WA27A,KA999A",
        "iMutation_Location(s)": "COR,COR",
        "Affinity_mut (M)": "1E-10",
        "Affinity_wt (M)": "1E-14",
    }
    numbering = {"1BRS": {"A": [[48, 157, 1]]}}
    mapped = map_rows({"1BRS": [row]}, "P00648", ENTRY, numbering, "t", "2.0")
    (item,) = mapped["fields"]["annotations.interface_mutations"]
    assert [m["not_placed"] for m in item["mutations"]] == [
        "residue_mismatch",
        "author_residue_not_mapped",
    ]


def test_quantities_are_kept_as_stated():
    assert _value("5.26E-11", "molar", "mutant") == {
        "mutant": {"value": 5.26e-11, "unit": "molar"}
    }
    assert _value(">1E-04", "molar", "mutant") == {
        "mutant": {"value": 1e-4, "unit": "molar"},
        "mutant_relation": ">",
    }
    assert _value("n.b.", "molar", "mutant") == {"mutant_no_binding": True}
    assert _value("-12.2", "kcal/mol", "dh_mutant")["dh_mutant"]["value"] == -12.2
    assert _value("", "molar", "mutant") == {}
    assert _temperature("298(assumed)") == {
        "temperature": {"value": 298.0, "unit": "kelvin"},
        "temperature_assumed": True,
    }


def test_ddg_is_derived_in_the_view_never_stored(resolver):
    card = _card(resolver, ["1BRS"])
    stored = card.get("annotations.interface_mutations")["value"]
    assert all("ddg" not in item for item in stored)
    view = card.interface_mutations()
    assert view["rule"]["rule"] == "binding_ddg@1"
    k27a = [
        i
        for i in view["items"]
        if i["structure"] == "pdb:1BRS"
        and i["method"] == "ITC"
        and [(m["original"], m["author_residue"], m["change"]) for m in i["mutations"]]
        == [("K", "27", "A")]
    ]
    (item,) = k27a
    expected = (
        1.98720425864083e-3
        * 298
        * math.log(
            item["affinity"]["mutant"]["value"] / item["affinity"]["wild_type"]["value"]
        )
    )
    assert item["ddg"]["value"] == pytest.approx(expected, abs=1e-6)
    assert item["ddg"]["unit"] == "kilocalorie / mole"
    assert 5.3 < item["ddg"]["value"] < 5.5  # barnase K27A, as published


def test_bounds_and_no_binding_are_not_turned_into_values():
    from sabueso.core.interface_mutations import _ddg

    t = {"value": 298.0, "unit": "kelvin"}
    q = {"value": 1e-9, "unit": "molar"}
    bounded = _ddg(
        {
            "temperature": t,
            "affinity": {"mutant": q, "wild_type": q, "mutant_relation": ">"},
        }
    )
    assert bounded["ddg_relation"] == ">"
    flipped = _ddg(
        {
            "temperature": t,
            "affinity": {"mutant": q, "wild_type": q, "wild_type_relation": "<"},
        }
    )
    assert flipped["ddg_relation"] == ">"
    both = _ddg(
        {
            "temperature": t,
            "affinity": {
                "mutant": q,
                "wild_type": q,
                "mutant_relation": ">",
                "wild_type_relation": ">",
            },
        }
    )
    assert both == {"ddg_basis": "both_affinities_bounded"}
    assert _ddg({"temperature": t, "affinity": {"mutant_no_binding": True}}) == {
        "ddg_basis": "mutant_no_binding"
    }


def test_the_card_seals_and_reads_its_quantities(resolver):
    card = _card(resolver, ["1BRS"])
    again = Card.from_dict(json.loads(json.dumps(card.to_dict())))
    assert again.get("annotations.interface_mutations") == card.get(
        "annotations.interface_mutations"
    )


def test_a_failing_source_is_an_error_and_the_state_knows_it(resolver):
    with pytest.warns(EnrichmentFailedWarning):
        card = _card(
            resolver, client=FixtureSKEMPIClient("temp_data", failing={"1BRS"})
        )
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "SKEMPI"]
    assert record["status"] == "error"
    rows = {(r["area"], r["source"]): r for r in card.knowledge_state()["rows"]}
    assert rows[("annotations.interface_mutations", "SKEMPI")]["state"] == "unavailable"


def test_nothing_to_ask_and_nothing_found_say_why(resolver):
    # Q4QGX0 cross-references no PDB entry; Q4D3W2 has 58, none in SKEMPI.
    for accession, reason in (
        ("Q4QGX0", "no PDB structure"),
        ("Q4D3W2", "SKEMPI has no row"),
    ):
        card, _ = sabueso.resolve(
            accession,
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            skempi=True,
            skempi_client=FixtureSKEMPIClient("temp_data"),
        )
        (record,) = [e for e in card.quality["enrichments"] if e["source"] == "SKEMPI"]
        assert record["status"] == "not_found"
        assert reason in record["detail"]
        rows = {(r["area"], r["source"]): r for r in card.knowledge_state()["rows"]}
        assert rows[("annotations.interface_mutations", "SKEMPI")]["state"] == (
            "not_stated"
        )


def test_the_public_function_returns_the_rows_in_the_envelope():
    result = get_mutations(["1brs", "9XYZ"], client=FixtureSKEMPIClient("temp_data"))
    assert result["source"] == "SKEMPI" and result["version"] == "2.0"
    assert len(result["record"]["rows"]["1BRS"]) == 94
    assert result["record"]["missing"] == ["9XYZ"]
