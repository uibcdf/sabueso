"""BindingDB and PubChem BioAssay keep the ceiling every source keeps (#88, #98): up to
5000 records by default, ordered by a named rule, and a cut is recorded and reported."""

import warnings

import pytest

import sabueso
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.bindingdb import FixtureBindingDBClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pubchem_bioassay import (
    FixturePubChemBioAssayClient,
    keep_rows,
)
from sabueso.tools.db.unichem import FixtureUniChemClient


def _card(**options):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        card, _ = sabueso.resolve(
            "P52270",
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            bindingdb_client=FixtureBindingDBClient("temp_data"),
            # Copies of ChEMBL lead to their ChEMBL originals: never online here.
            chembl_client=FixtureChEMBLClient("temp_data"),
            unichem_client=FixtureUniChemClient("temp_data"),
            pubchem_bioassay_client=FixturePubChemBioAssayClient("temp_data"),
            **options,
        )
    return card, [str(w.message) for w in caught]


def _record(card, source):
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == source]
    return record


def test_pubchem_rows_are_cut_by_a_named_order_and_the_cut_is_reported():
    card, messages = _card(pubchem_bioassay={"limit": 5})
    record = _record(card, "PubChem BioAssay")
    assert (record["truncated"], record["total_count"]) == (True, 493)
    assert record["row_order"] == "pubchem_row_order@1"
    from_pubchem = [
        r
        for r in card.relationships("has_bioactivity")
        if r["qualifiers"].get("source") == "PubChem BioAssay"
    ]
    assert 0 < len(from_pubchem) <= 5
    assert any("PubChem BioAssay" in m and "493" in m for m in messages)


def test_the_row_order_puts_confirmatory_measured_rows_first():
    import json

    record = json.load(open("temp_data/pubchem_bioassay/P52270.json"))
    kept = keep_rows(record, "P52270", 10)
    cells = [
        dict(zip(t["Columns"]["Column"], row["Cell"]))
        for t in kept["concise"].values()
        for row in t["Row"]
    ]
    assert len(cells) == 10 and kept["total_rows"] == 493
    assert all(c["Assay Type"] == "Confirmatory" for c in cells)
    assert all(c["Activity Value [uM]"] for c in cells)
    assert set(kept["summaries"][0]) and {
        str(s["AID"]) for s in kept["summaries"]
    } <= set(kept["concise"])


def test_true_and_empty_options_both_ask_pubchem():
    for option in (True, {}):
        card, _ = _card(pubchem_bioassay=option)
        record = _record(card, "PubChem BioAssay")
        assert record["status"] == "added" and record["truncated"] is False


def test_bindingdb_records_are_cut_by_a_named_order():
    card, messages = _card(bindingdb={"limit": 3})
    record = _record(card, "BindingDB")
    assert record["record_order"] == "bindingdb_record_order@1"
    assert record["truncated"] is True and record["total_count"] > 3
    assert record["count"] <= 3
    assert any("BindingDB" in m and "incomplete" in m for m in messages)
    whole, _ = _card(bindingdb={})
    assert _record(whole, "BindingDB")["truncated"] is False


def test_a_misspelt_option_is_refused():
    with pytest.raises(ArgumentError):
        _card(pubchem_bioassay={"limt": 5})
    with pytest.raises(ArgumentError):
        _card(bindingdb={"limit": 0})
