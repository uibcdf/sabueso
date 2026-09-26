"""One measurement stated by several sources (uibcdf/sabueso#66).

Fixtures: ChEMBL_37 activities and BindingDB REST records (2026-09-25) for TcTIM
(P52270) and HsTIM (P60174), with UniChem lookups of the BindingDB monomers.
"""

import copy

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.measurements import half_unit, measurement_groups
from sabueso.mappings.bindingdb import parse_affinity
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.bindingdb import FixtureBindingDBClient, get_affinities
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.unichem import FixtureUniChemClient


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _card(resolver, accession, bindingdb=True):
    options = dict(chembl={}, chembl_client=FixtureChEMBLClient("temp_data"))
    if bindingdb:
        options.update(
            bindingdb={},
            bindingdb_client=FixtureBindingDBClient("temp_data"),
            unichem_client=FixtureUniChemClient("temp_data"),
        )
    card, _ = sabueso.resolve(accession, resolver=resolver, **options)
    return card


@pytest.fixture(scope="module")
def tctim(resolver):
    return _card(resolver, "P52270")


@pytest.fixture(scope="module")
def hstim(resolver):
    return _card(resolver, "P60174")


def _bindingdb(card):
    return [
        r
        for r in card.relationships("has_bioactivity")
        if r["qualifiers"].get("source") == "BindingDB"
    ]


def test_values_keep_their_relation_and_precision():
    assert parse_affinity(">1.00e+5") == (">", 100000.0, "1.00e+5")
    assert parse_affinity("62") == ("=", 62.0, "62")
    assert half_unit({"value": 62.0, "stated_value": "62", "units": "nM"}) == 0.5
    assert half_unit({"value": 62.46, "units": "nM"}) == pytest.approx(0.005)
    assert half_unit(
        {"value": 100000.0, "stated_value": "1.00e+5", "units": "nM"}
    ) == pytest.approx(500)


def test_bindingdb_restating_chembl_is_grouped_not_counted_twice(tctim):
    identity = measurement_groups(tctim)
    grouped = {rid for g in identity["groups"] for rid in g["records"]}
    records = _bindingdb(tctim)
    assert len(records) == 17
    assert sum(r["id"] in grouped for r in records) == 16
    assert all(g["sources"] == ["BindingDB", "ChEMBL"] for g in identity["groups"])
    assert all(g["basis"] == ["statement"] for g in identity["groups"])
    # The view counts measurements: 16 groups of two records count 16, not 32.
    view = tctim.bioactivities()
    measurements = sum(i["measurement_count"] for i in view["items"])
    records_seen = sum(i["record_count"] for i in view["items"])
    assert records_seen - measurements == 16


def test_a_measurement_attributed_to_another_molecule_is_flagged(tctim):
    review = measurement_groups(tctim)["review"]
    reasons = {tuple(r["molecules"]): r["reason"] for r in review}
    # Same paper (PubMed 35189560), IC50 13000 nM: BindingDB's monomer is
    # IAFAANQPDPWPHK, ChEMBL's molecule is XMRUGIFDPFFCIV.
    assert reasons[
        ("inchikey:IAFAANQPDPWPHK-UHFFFAOYSA-N", "inchikey:XMRUGIFDPFFCIV-UHFFFAOYSA-N")
    ] == ("molecule_differs")


def test_rounding_stereochemistry_new_papers_and_unresolved_molecules(hstim):
    identity = measurement_groups(hstim)
    group_of = identity["group_of"]
    by_id = {r["id"]: r for r in hstim.relationships("has_bioactivity")}
    # Kd 62 (BindingDB) and 62.46 nM (ChEMBL), same paper: one measurement.
    (bdb,) = [
        r
        for r in _bindingdb(hstim)
        if r["qualifiers"]["measurement"]["stated_value"] == "62"
    ]
    mates = [
        by_id[rid]
        for rid, gid in group_of.items()
        if gid == group_of[bdb["id"]] and rid != bdb["id"]
    ]
    assert [m["qualifiers"]["measurement"]["value"] for m in mates] == [62.46]
    # ChEMBL states that experiment twice (Kd and ED50): never grouped with each other.
    ed50 = [
        r
        for r in hstim.relationships("has_bioactivity")
        if r["qualifiers"]["measurement"]["type"] == "ED50"
        and r["qualifiers"]["measurement"]["value"] == 62.46
    ]
    assert ed50 and all(group_of[r["id"]] == r["id"] for r in ed50)
    # A paper ChEMBL lacks for this target: three new measurements, one source each.
    new = [
        r
        for r in _bindingdb(hstim)
        if r["qualifiers"]["document"]["pubmed"] == "23406473"
    ]
    assert len(new) == 3 and all(group_of[r["id"]] == r["id"] for r in new)
    reasons = sorted(r["reason"] for r in identity["review"])
    assert reasons.count("molecule_unresolved") == 5
    assert "stereo_differs" in reasons
    (enrichment,) = [
        e for e in hstim.quality["enrichments"] if e["source"] == "BindingDB"
    ]
    assert len(enrichment["unanchored"]) == 5


def _with(card, extra_rels):
    data = card.to_dict()
    data["relationship_store"] += extra_rels
    data.pop("quantities")
    from sabueso.core.quantities import seal

    data["quantities"] = seal(data)
    return Card.from_dict(data)


def _chembl_record(card):
    return next(
        r
        for r in card.relationships("has_bioactivity")
        if not r["qualifiers"].get("source")
        and r["qualifiers"]["measurement"]["relation"] == "="
        and r["qualifiers"]["document"].get("pubmed")
    )


def test_a_declared_copy_is_grouped_by_provenance(resolver):
    card = _card(resolver, "P52270", bindingdb=False)
    original = _chembl_record(card)
    copy_rel = copy.deepcopy(original)
    copy_rel["id"] = "REL_constructed_copy"
    copy_rel["qualifiers"].update(
        source="PubChem",
        activity_id="pubchem:constructed",
        copy_of={
            "source": "ChEMBL",
            "activity_id": original["qualifiers"]["activity_id"],
        },
    )
    copy_rel["qualifiers"]["document"] = {}  # nothing to compare: provenance decides
    identity = measurement_groups(_with(card, [copy_rel]))
    (group,) = identity["groups"]
    assert set(group["records"]) == {original["id"], "REL_constructed_copy"}
    assert group["basis"] == ["provenance"]


def test_two_candidates_are_ambiguous_and_not_grouped(resolver):
    card = _card(resolver, "P52270", bindingdb=False)
    original = _chembl_record(card)
    twin = copy.deepcopy(original)
    twin["id"] = "REL_constructed_twin"
    twin["qualifiers"]["activity_id"] = -1  # a second ChEMBL record, same statement
    reader = copy.deepcopy(original)
    reader["id"] = "REL_constructed_reader"
    reader["qualifiers"].update(source="BindingDB", activity_id="bindingdb:constructed")
    identity = measurement_groups(_with(card, [twin, reader]))
    assert not identity["groups"]
    (ambiguous,) = [a for a in identity["ambiguous"] if a.get("record")]
    assert ambiguous["record"] == "REL_constructed_reader"
    assert set(ambiguous["candidates"]) == {original["id"], "REL_constructed_twin"}


def test_knowledge_state_and_source_access(resolver, tctim):
    def state(card):
        (row,) = [
            r
            for r in card.knowledge_state()["rows"]
            if r["area"] == "relationships.has_bioactivity"
            and r["source"] == "BindingDB"
        ]
        return row["state"], row["count"]

    assert state(tctim) == ("known", 17)
    assert state(_card(resolver, "P52270", bindingdb=False))[0] == "not_queried"
    record = get_affinities("P52270", client=FixtureBindingDBClient("temp_data"))
    assert (record["source"], record["kind"], len(record["record"])) == (
        "BindingDB",
        "affinities",
        17,
    )


def test_a_shared_value_of_two_matched_compounds_is_not_a_discrepancy(tctim):
    # Paper PubMed 35189560 reports IC50 = 3 uM for two different compounds. Each is
    # grouped with its own records (BindingDB 50597987 with ChEMBL CHEMBL5170853, 50597988
    # with CHEMBL5192352), so pairing them crosswise is not a discrepancy (#75).
    review = measurement_groups(tctim)["review"]
    refs = [
        {tctim.relationship_store.get(i)["object_ref"] for i in r["records"]}
        for r in review
    ]
    assert {"bindingdb:50597987", "chembl:CHEMBL5192352"} not in refs
    assert {"bindingdb:50597988", "chembl:CHEMBL5170853"} not in refs
    assert {"bindingdb:50597991", "chembl:CHEMBL5198783"} in refs  # a genuine case
    # One entry per pair of molecules, however many records state it.
    pairs = [(r["reason"], tuple(r["molecules"]), r.get("note")) for r in review]
    assert len(pairs) == len(set(pairs))
