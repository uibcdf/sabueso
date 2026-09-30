"""ChEBI (#83, wave 2): a molecule's classes, roles and definition, joined only through
UniChem's link and the InChIKey ChEBI states. Frozen ChEBI 2.0 entries of 2026-09-30."""

import json
import warnings

import pytest

import sabueso
from sabueso.core.errors import ArgumentError
from sabueso.mappings.chebi import map_chebi_identity
from sabueso.tools.db.chebi import FixtureChEBIClient, accession, get_compounds
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

VCR = "sabueso:small_molecule:inchikey:OGWKCGZFUXNPDA-XQKSVPLYSA-N"


def _vincristine(**options):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        card, _ = sabueso.resolve(
            "chembl:CHEMBL90555",
            chembl_client=FixtureChEMBLClient("temp_data"),
            ccd_client=FixtureCCDClient("temp_data"),
            unichem_client=FixtureUniChemClient("temp_data"),
            chebi_client=FixtureChEBIClient("temp_data"),
            **options,
        )
    return card


@pytest.fixture(scope="module")
def card():
    return _vincristine(chebi=True)


def test_chebi_joins_through_the_link_and_the_inchikey_it_states(card):
    assert card.id == VCR
    assert card.get("identifiers.chebi")["value"] == "CHEBI:28445"
    (link,) = [
        r for r in card.relationships("same_as") if r["subject_ref"] == "chebi:28445"
    ]
    stated_by = {
        card.source_assertion_store.get(i)["source"]["name"]
        for i in link["source_assertion_ids"]
    }
    assert "ChEBI" in stated_by  # and UniChem, which linked it
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "ChEBI"]
    assert (record["status"], record["count"]) == ("added", 1)


def test_classes_and_roles_as_chebi_states_them(card):
    classes = {c["name"] for c in card.get("annotations.chemical_classes")["value"]}
    assert "vinca alkaloid" in classes
    roles = {r["name"]: r for r in card.get("annotations.chemical_roles")["value"]}
    assert roles["antineoplastic agent"]["direct"] is True
    assert roles["antineoplastic agent"]["application"] is True
    assert roles["plant metabolite"]["biological_role"] is True
    # Inherited through its classes or parent roles: stated by ChEBI, not direct.
    assert roles["Bronsted base"]["direct"] is False
    assert roles["Bronsted base"]["chemical_role"] is True


def test_the_definition_is_read_as_text_and_kept_as_written(card):
    node = card.get("annotations.definition")
    assert "<" not in node["value"]["text"] and "C46H56N4O10" in node["value"]["text"]
    (sa,) = [card.source_assertion_store.get(i) for i in node["source_assertion_ids"]]
    assert "<sub>" in sa["asserted_value"]["text"]
    assert sa["source_metadata"]["stars"] == 3


def test_an_entry_whose_inchikey_is_another_joins_no_card():
    entries = json.load(open("temp_data/chebi/compounds.json"))["compounds"]
    other = entries["CHEBI:17150"]  # 2-phosphoglycolic acid
    mapping, key = map_chebi_identity(other, "fixture")
    assert key == "ASCFNMCAHFUBCO-UHFFFAOYSA-N"
    assert mapping["relationships"][0]["object_ref"] == f"inchikey:{key}"
    no_structure = {"data": {"chebi_accession": "CHEBI:1", "default_structure": None}}
    assert map_chebi_identity(no_structure, "fixture")[1] is None


def test_without_the_option_chebi_is_not_asked():
    card = _vincristine()
    assert card.get("annotations.chemical_roles") is None
    assert not [
        e for e in card.quality.get("enrichments") or [] if e["source"] == "ChEBI"
    ]


def test_the_public_function_and_accessions():
    assert accession("chebi:28445") == accession("28445") == "CHEBI:28445"
    record = get_compounds(
        ["CHEBI:28445", "CHEBI:0"], client=FixtureChEBIClient("temp_data")
    )
    assert list(record["record"]["compounds"]) == ["CHEBI:28445"]
    assert record["record"]["missing"] == ["CHEBI:0"]
    with pytest.raises(ArgumentError):
        _vincristine(chebi="yes")
