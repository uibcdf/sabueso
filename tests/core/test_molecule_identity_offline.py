"""Small-molecule identity anchored at the standard InChIKey (uibcdf/sabueso#25).

Frozen public responses retrieved on 2026-09-23: PDB chemical components (RCSB), ChEMBL_37
molecules and UniChem compounds. BTS is the ligand of the TcTIM structure 1SUX, and
ChEMBL reports it as CHEMBL1161789, measured on TcTIM.
"""

import pytest

from sabueso import resolve_molecule_card
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.core.errors import ConnectorError
from sabueso.mappings.molecule_identity import (
    is_standard_inchikey,
    map_ccd_identity,
    map_chembl_identity,
)
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

BTS_KEY = "XBNHRNFODJOFRU-UHFFFAOYSA-N"
BTS = f"sabueso:small_molecule:inchikey:{BTS_KEY}"
PGA_KEY = "ASCFNMCAHFUBCO-UHFFFAOYSA-N"


def _clients(**failing):
    return dict(
        chembl_client=FixtureChEMBLClient("temp_data", failing=failing.get("chembl")),
        ccd_client=FixtureCCDClient("temp_data", failing=failing.get("ccd")),
        unichem_client=FixtureUniChemClient(
            "temp_data", failing=failing.get("unichem")
        ),
    )


def _links(card):
    return {r["subject_ref"]: r for r in card.relationships("same_as")}


def _sources(card, rel):
    return sorted(
        card.source_assertion_store.get(i)["source"]["name"]
        for i in rel["source_assertion_ids"]
    )


@pytest.mark.parametrize(
    "identifier",
    ["pdb.ligand:BTS", "chembl:CHEMBL1161789", "CHEMBL1161789", f"inchikey:{BTS_KEY}"],
)
def test_a_structure_ligand_and_a_measured_molecule_are_one_entity(identifier):
    card, resolution = resolve_molecule_card(identifier, **_clients())
    assert (resolution.status, resolution.entity_ref) == ("resolved", BTS)
    assert card.id == BTS
    links = _links(card)
    # Each record is linked to the anchor by the source that holds it, and UniChem agrees.
    assert _sources(card, links["pdb.ligand:BTS"]) == ["PDB CCD", "UniChem"]
    assert _sources(card, links["chembl:CHEMBL1161789"]) == ["ChEMBL", "UniChem"]
    # Records in resources Sabueso did not query come from UniChem alone.
    assert _sources(card, links["drugbank:DB03132"]) == ["UniChem"]
    assert {"pubchem:162569", "bindingdb:50597989"} <= set(links)
    assert resolution.decision["rules"] == ["standard_inchikey_anchor"]


def test_fields_come_from_the_molecule_records_and_agree():
    card, _ = resolve_molecule_card("pdb.ligand:BTS", **_clients())
    inchikey = card.get("identifiers.inchikey")
    assert inchikey["value"] == BTS_KEY
    stated_by = sorted(
        card.source_assertion_store.get(i)["source"]["name"]
        for i in inchikey["source_assertion_ids"]
    )
    assert stated_by == ["ChEMBL", "PDB CCD"]
    assert card.get("properties.physchem.formula")["value"] == "C10H11NO3S3"
    assert not card.quality.get("conflicts")


def test_duplicate_components_share_one_anchor_and_gaps_are_recorded():
    card, _ = resolve_molecule_card("pdb.ligand:PGA", **_clients())
    links = _links(card)
    # The CCD holds 2-phosphoglycolate twice, as PGA and 2PL: one molecule.
    assert {"pdb.ligand:PGA", "pdb.ligand:2PL"} <= set(links)
    assert "chebi:17150" in links  # ChEBI ids without their "CHEBI:" banana
    outcomes = {e["source"]: e for e in card.quality["enrichments"]}
    # Records UniChem lists but the saved responses do not hold are reported, not hidden.
    assert outcomes["PDB CCD"]["missing"] == ["2PL"]
    assert outcomes["ChEMBL"]["status"] == "not_found"


def test_development_phase_is_asserted_by_chembl():
    card, _ = resolve_molecule_card("chembl:CHEMBL110", unichem=False, **_clients())
    assert card.get("names.canonical_name")["value"] == "BENZNIDAZOLE"
    assert card.get("clinical.max_phase")["value"] == 4.0  # approved
    (sa_id,) = card.get("clinical.max_phase")["source_assertion_ids"]
    assert card.source_assertion_store.get(sa_id)["asserted_value"] == "4.0"


def test_records_without_a_standard_inchikey_are_never_anchored():
    assert not is_standard_inchikey("XBNHRNFODJOFRU-UHFFFAOYNA-N")  # non-standard
    _, key = map_chembl_identity(
        {"molecule_chembl_id": "CHEMBL0", "molecule_structures": None}, "stub"
    )
    assert key is None
    nonstandard = {
        "chem_comp": {"id": "XXX"},
        "rcsb_chem_comp_descriptor": {
            "InChI": "InChI=1/C2H6O/c1-2-3/h3H,2H2,1H3",
            "InChIKey": "LFQSCWFLJHTTHZ-UHFFFAOYAR-N",
        },
    }
    assert map_ccd_identity(nonstandard, "stub")[1] is None


class _NoStructure:
    def molecules(self, ids):
        record = {"molecule_chembl_id": ids[0], "molecule_structures": None}
        return {"version": None, "retrieved_at": "stub", "molecules": {ids[0]: record}}


def test_statuses_stay_distinct():
    clients = _clients()
    assert resolve_molecule_card("pdb.ligand:ZZZ", **clients)[1].status == "not_found"
    assert resolve_molecule_card("chembl:CHEMBL0", **clients)[1].status == "not_found"
    assert resolve_molecule_card("aspirin", **clients)[1].status == "unsupported"
    unanchored = resolve_molecule_card(
        "chembl:CHEMBL2", **{**clients, "chembl_client": _NoStructure()}
    )[1]
    assert (unanchored.status, unanchored.decision["rules"]) == (
        "unsupported",
        ["no_standard_inchikey"],
    )
    no_unichem = resolve_molecule_card(f"inchikey:{BTS_KEY}", unichem=False, **clients)
    assert no_unichem[1].decision["rules"] == ["inchikey_requires_unichem"]
    failing = _clients(ccd={"BTS"})
    assert resolve_molecule_card("pdb.ligand:BTS", **failing)[1].status == "error"


def test_a_unichem_failure_never_prevents_the_card():
    with pytest.warns(EnrichmentFailedWarning, match="UniChem could not be consulted"):
        card, resolution = resolve_molecule_card(
            "pdb.ligand:BTS", **_clients(unichem={BTS_KEY})
        )
    assert resolution.status == "resolved"
    assert card.quality["enrichments"] == [
        {
            "source": "UniChem",
            "status": "error",
            "detail": f"UniChem request for {BTS_KEY} failed (simulated)",
        }
    ]
    assert set(_links(card)) == {"pdb.ligand:BTS"}  # no expansion, nothing invented
    with pytest.raises(ConnectorError):
        FixtureUniChemClient("temp_data", failing={PGA_KEY}).compound(PGA_KEY)
