"""PubChem BioAssay: declared copies are pointers, never confirmations (#68).

Fixtures: PubChem assays linked to TcTIM (13, all deposited by ChEMBL) and HsTIM (11:
10 by ChEMBL, one by BindingDB), 2026-09-25, with ChEMBL_37 and BindingDB fixtures.
"""

from collections import Counter

import pytest

import sabueso
from sabueso.core.measurements import measurement_groups
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.bindingdb import FixtureBindingDBClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pubchem_bioassay import FixturePubChemBioAssayClient, get_assays
from sabueso.tools.db.unichem import FixtureUniChemClient


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _card(resolver, accession, chembl=None, bindingdb=True):
    options = dict(
        chembl=chembl if chembl is not None else {},
        chembl_client=FixtureChEMBLClient("temp_data"),
        pubchem_bioassay=True,
        pubchem_bioassay_client=FixturePubChemBioAssayClient("temp_data"),
    )
    if bindingdb:
        options.update(
            bindingdb={},
            bindingdb_client=FixtureBindingDBClient("temp_data"),
            unichem_client=FixtureUniChemClient("temp_data"),
        )
    card, _ = sabueso.resolve(accession, resolver=resolver, **options)
    return card


def test_three_sources_count_as_measurements_not_records(resolver):
    card = _card(resolver, "P52270")
    view = card.bioactivities()
    measurements = sum(i["measurement_count"] for i in view["items"])
    records = sum(i["record_count"] for i in view["items"])
    assert (records, measurements) == (1002, 505)
    identity = measurement_groups(card)
    assert (
        Counter(tuple(g["sources"]) for g in identity["groups"])[
            ("ChEMBL", "PubChem BioAssay")
        ]
        > 400
    )
    # Copies the depositor's compound standardised differently: grouped, and flagged.
    flagged = [r for r in identity["review"] if r.get("note")]
    assert flagged and {r["reason"] for r in flagged} == {"stereo_differs"}
    reasons = Counter(u["reason"] for u in identity["unresolved_copies"])
    assert reasons == {"molecule_not_found_in_assay": 7}


def test_a_copy_never_votes_when_its_original_is_there(resolver):
    card = _card(resolver, "P52270")
    view = card.bioactivities()
    for item in view["items"]:
        by_group = {}
        for m in item["measurements"]:
            by_group.setdefault(m["group"], []).append(m)
        for members in by_group.values():
            originals = [m for m in members if not m["copy"]]
            if originals and len({m["class"] for m in originals}) == 1:
                expected = originals[0]["class"]
                assert item["classes"].get(expected, 0) >= 1


def test_copies_lead_to_what_a_truncated_query_missed(resolver):
    from sabueso._private.smonitor.warnings import EnrichmentTruncatedWarning

    with pytest.warns(EnrichmentTruncatedWarning):  # the target query itself was cut
        card = _card(resolver, "P52270", chembl={"limit": 25}, bindingdb=False)
    chembl = [
        r
        for r in card.relationships("has_bioactivity")
        if not r["qualifiers"].get("source")
    ]
    assert len(chembl) == 493  # 25 from the target query, 468 through the copies
    followed = [r for r in chembl if r["qualifiers"].get("retrieved_via")]
    assert len(followed) == 468
    (pointer,) = [e for e in card.quality["enrichments"] if e.get("data")]
    assert (pointer["status"], pointer["count"], pointer["targets"]) == (
        "added",
        468,
        ["CHEMBL5834"],
    )


def test_a_bindingdb_copy_is_resolved_only_when_bindingdb_is_asked_for(resolver):
    without = measurement_groups(_card(resolver, "P60174", bindingdb=False))
    assert Counter(u["reason"] for u in without["unresolved_copies"]) == {
        "original_not_on_card": 3
    }
    with_bindingdb = measurement_groups(_card(resolver, "P60174"))
    groups = [g for g in with_bindingdb["groups"] if "BindingDB" in g["sources"]]
    assert any(set(g["sources"]) == {"BindingDB", "PubChem BioAssay"} for g in groups)
    assert any(
        set(g["sources"]) == {"BindingDB", "ChEMBL", "PubChem BioAssay"} for g in groups
    )


def test_knowledge_state_and_source_access(resolver):
    card = _card(resolver, "P60174", bindingdb=False)
    (row,) = [
        r
        for r in card.knowledge_state()["rows"]
        if r["area"] == "relationships.has_bioactivity"
        and r["source"] == "PubChem BioAssay"
    ]
    assert row["state"] == "known"
    record = get_assays("P60174", client=FixturePubChemBioAssayClient("temp_data"))
    assert (record["source"], record["kind"]) == ("PubChem BioAssay", "assays")
    assert Counter(s["SourceName"] for s in record["record"]["summaries"]) == {
        "ChEMBL": 10,
        "BindingDB": 1,
    }
