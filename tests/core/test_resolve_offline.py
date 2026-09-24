"""``sabueso.resolve``: one entry point, routed by the query's namespace (uibcdf/sabueso#38)."""

import re

import argdigest
import pytest

import sabueso
from sabueso.core.errors import ArgumentError
from sabueso.resolver import (
    EntityQuery,
    EntityResolver,
    FixtureRCSBClient,
    FixtureUniProtClient,
)
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

BTS_KEY = "XBNHRNFODJOFRU-UHFFFAOYSA-N"
BTS = f"sabueso:small_molecule:inchikey:{BTS_KEY}"


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _molecule_clients():
    return dict(
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
    )


@pytest.mark.parametrize("query", ["P52270", "uniprot:P52270"])
def test_a_protein_identifier_resolves_to_its_protein_card(resolver, query):
    card, resolution = sabueso.resolve(query, resolver=resolver)
    assert card.id == "sabueso:protein:uniprot:P52270"
    assert resolution.decision["route"] == {
        "entity_type": "protein",
        "tool": "resolve_protein_card",
        "basis": "default",
    }


@pytest.mark.parametrize(
    "query, basis",
    [
        ("pdb.ligand:BTS", "namespace:pdb.ligand"),
        ("chembl:CHEMBL1161789", "namespace:chembl"),
        ("CHEMBL1161789", "namespace:chembl"),
        (BTS_KEY, "namespace:inchikey"),
    ],
)
def test_a_small_molecule_identifier_resolves_to_its_molecule_card(query, basis):
    card, resolution = sabueso.resolve(query, **_molecule_clients())
    assert card.id == BTS
    assert resolution.decision["route"]["tool"] == "resolve_molecule_card"
    assert resolution.decision["route"]["basis"] == basis


def test_a_name_and_organism_go_to_the_protein_resolver(resolver):
    # The protein resolver keeps its own rules: here, a name without an organism is too
    # broad to resolve, and that is the answer, not a silent choice.
    card, resolution = sabueso.resolve(
        EntityQuery(name="triosephosphate isomerase"), resolver=resolver
    )
    assert card is None
    assert "name_without_organism" in resolution.decision["rules"]
    assert resolution.decision["route"]["basis"] == "name_and_organism"


def test_entity_type_overrides_the_namespace():
    card, resolution = sabueso.resolve(
        "P52270", entity_type="small_molecule", unichem=False
    )
    assert card is None and resolution.status == "unsupported"
    assert resolution.decision["route"]["basis"] == "entity_type"


def test_a_small_molecule_needs_an_identifier():
    card, resolution = sabueso.resolve(
        EntityQuery(name="aspirin", entity_type="small_molecule")
    )
    assert card is None and resolution.status == "unsupported"
    assert resolution.decision["rules"] == ["small_molecule_needs_an_identifier"]


def test_an_option_of_the_other_tool_is_refused_not_ignored(resolver):
    with pytest.raises(argdigest.UnknownArgumentError):
        sabueso.resolve("P52270", resolver=resolver, unichem=False)
    with pytest.raises(argdigest.UnknownArgumentError):
        sabueso.resolve("pdb.ligand:BTS", structures="all", **_molecule_clients())


def test_an_unknown_option_is_refused(resolver):
    with pytest.raises(argdigest.UnknownArgumentError):
        sabueso.resolve("P52270", resolvr=resolver)


@pytest.mark.parametrize(
    "call",
    [
        lambda: sabueso.resolve("P52270", entity_type="dna"),
        lambda: sabueso.resolve("   "),
        lambda: sabueso.resolve("P52270", structures="not-a-pdb-id"),
    ],
)
def test_wrong_values_are_refused(call):
    with pytest.raises(ArgumentError):
        call()


def test_the_admitted_options_are_those_of_the_card_tools():
    from sabueso._private.argdigest.domain.card_options import domain

    members = set(domain.members())
    assert {"resolver", "structures", "chembl", "unichem", "ccd_client"} <= members
    assert not members & {"query", "identifier", "skip_digestion"}


# --- enrichment profiles (#45) ---------------------------------------------------------


def test_a_profile_expands_to_its_options_and_is_recorded(resolver):
    from sabueso.tools.db.interpro import FixtureInterProClient
    from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient

    card, resolution = sabueso.resolve(
        "P52270",
        resolver=resolver,
        profile="structural_baseline@1",
        chembl_client=FixtureChEMBLClient("temp_data"),
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        interpro_client=FixtureInterProClient("temp_data"),
    )
    sources = {(e["source"], e.get("data")) for e in card.quality["enrichments"]}
    assert {
        ("ChEMBL", None),
        ("InterPro", None),
        ("PDBe-KB", "interface_residues"),
        ("PDBe-KB", "ligand_sites"),
    } <= sources
    assert len([e for e in card.quality["enrichments"] if "structure" in e]) == 7
    profile = resolution.decision["profile"]
    assert profile["name"] == "structural_baseline@1"
    assert profile["overridden"] == []
    # The card itself says how it was built, also after storage.
    import json

    from sabueso.core.card import Card

    again = Card.from_dict(json.loads(json.dumps(card.to_dict())))
    assert again.quality["entity_resolution"]["decision"]["profile"] == profile


def test_explicit_options_override_a_profile_and_are_recorded(resolver):
    card, resolution = sabueso.resolve(
        "P52270",
        resolver=resolver,
        profile="structural_baseline@1",
        structures=["1SUX"],
        chembl=None,
        interfaces=False,
        ligand_sites=False,
        family_sites=False,
    )
    assert resolution.decision["profile"]["overridden"] == [
        "chembl",
        "family_sites",
        "interfaces",
        "ligand_sites",
        "structures",
    ]
    assert [e["structure"] for e in card.quality["enrichments"]] == ["1SUX"]


def test_a_profile_applies_the_options_of_the_routed_entity_type():
    card, resolution = sabueso.resolve(
        "pdb.ligand:BTS", profile="structural_baseline@1", **_molecule_clients()
    )
    assert card.id == BTS
    assert resolution.decision["profile"]["options"] == {"unichem": True}


@pytest.mark.parametrize("profile", ["structural_baseline", "nonexistent@1", 1])
def test_an_unknown_profile_is_refused(resolver, profile):
    with pytest.raises(ArgumentError):
        sabueso.resolve("P52270", resolver=resolver, profile=profile)


def test_published_profiles_are_versioned_and_use_real_options():
    from sabueso._private.argdigest.domain.card_options import domain
    from sabueso.resolver.loader import load_enrichment_profiles

    options = set(domain.members())
    for name, profile in load_enrichment_profiles().items():
        assert re.fullmatch(r"[a-z_]+@[1-9][0-9]*", name)
        assert profile["description"]
        for kind in ("protein", "small_molecule"):
            assert set(profile[kind]) <= options, (name, kind)
