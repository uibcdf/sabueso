"""Curated assertions survive rebuilds through a curation store (uibcdf/sabueso#48)."""

import json

import pytest

import sabueso
from sabueso.core.errors import StorageError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.card.small_molecule import single_molecule_card

VARIANT = "features_positional.natural_variant"
E105D = {"original": "E", "alternatives": ["D"]}


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _hstim(resolver, **kwargs):
    card, _ = sabueso.resolve("P60174", resolver=resolver, **kwargs)
    return card


def _curate(card):
    with pytest.warns(sabueso._private.smonitor.warnings.CuratedDisagreementWarning):
        variant = card.add_literature_assertion(
            VARIANT,
            {
                "start": 105,
                "substitution": E105D,
                "description": "alters a water network",
            },
            "pubmed:18562316",
            "curator-a",
            locator="Title",
            eco_code="ECO:0000269",
            curated_at="2026-09-24",
        )
    subunit = card.add_literature_assertion(
        "annotations.subunit", "Homodimer", "pubmed:8061610", "curator-a"
    )
    interaction = card.add_literature_relationship(
        "interacts_with",
        "uniprot:Q00001",
        {"method": "pull-down"},
        "doi:10.1000/x",
        "b",
    )
    return [variant, subunit, interaction]


def _ids(records):
    return sorted(r["source_assertion_id"] for r in records)


def test_a_rebuilt_card_gets_the_same_curated_assertions(resolver, tmp_path):
    card = _hstim(resolver)
    curated = _curate(card)
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    assert store.save(card) == {"added": 3, "updated": 0, "total": 3}

    with pytest.warns(sabueso._private.smonitor.warnings.CuratedDisagreementWarning):
        rebuilt = _hstim(resolver, curations=store)
    assert _ids(rebuilt.quality["curation"]) == _ids(curated)
    assert rebuilt.quality["curation_store"] == {
        "applied": 3,
        "skipped_retracted": 0,
        "changed": [],
    }
    # Same ids, same statements: what was curated is on the new card as it was.
    for record in curated:
        old = card.source_assertion_store.get(record["source_assertion_id"])
        new = rebuilt.source_assertion_store.get(record["source_assertion_id"])
        assert new == old


def test_saving_twice_changes_nothing(resolver, tmp_path):
    card = _hstim(resolver)
    _curate(card)
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)
    before = (tmp_path / "curation.jsonl").read_text(encoding="utf-8")
    assert store.save(card) == {"added": 0, "updated": 0, "total": 3}
    assert (tmp_path / "curation.jsonl").read_text(encoding="utf-8") == before


def test_a_changed_outcome_is_reported(resolver, tmp_path):
    # A curation recorded when no source stated the item ("new"); the rebuilt card's
    # source now states exactly the same item, so it corroborates.
    card = _hstim(resolver)
    uniprot_item = next(
        i
        for i in card.get(VARIANT)["value"]
        if i["location"]["sequence"]["start"] == 42
    )
    record = card.add_literature_assertion(
        VARIANT, uniprot_item, "pubmed:9338582", "curator-a"
    )
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)
    records = store.records()
    records[0]["outcome"] = "new"  # as it was first recorded
    store._write(records)

    rebuilt = _hstim(resolver, curations=store)
    (change,) = rebuilt.quality["curation_store"]["changed"]
    assert change["source_assertion_id"] == record["source_assertion_id"]
    assert (change["previous_outcome"], change["outcome"]) == ("new", "corroborates")
    store.save(rebuilt)  # the store now remembers the outcome last seen
    assert store.records()[0]["outcome"] == "corroborates"


def test_a_retracted_record_is_kept_but_not_applied(resolver, tmp_path):
    card = _hstim(resolver)
    variant, subunit, _ = _curate(card)
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)
    store.retract(
        subunit["source_assertion_id"], "not stated in that paper", "curator-b"
    )

    with pytest.warns(sabueso._private.smonitor.warnings.CuratedDisagreementWarning):
        rebuilt = _hstim(resolver, curations=str(tmp_path / "curation.jsonl"))
    assert rebuilt.quality["curation_store"]["skipped_retracted"] == 1
    assert subunit["source_assertion_id"] not in _ids(rebuilt.quality["curation"])
    (kept,) = [
        r
        for r in store.records()
        if r["source_assertion_id"] == subunit["source_assertion_id"]
    ]
    assert kept["retracted"]["reason"] == "not stated in that paper"
    assert kept["retracted"]["curator"] == "curator-b"
    # Saving the card that still holds it does not bring it back.
    store.save(card)
    assert all(
        r.get("retracted")
        for r in store.records()
        if r["source_assertion_id"] == subunit["source_assertion_id"]
    )


def test_records_of_another_entity_are_ignored(resolver, tmp_path):
    card = _hstim(resolver)
    _curate(card)
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)
    other, _ = sabueso.resolve("P52270", resolver=resolver, curations=store)
    assert other.quality["curation_store"]["applied"] == 0
    assert "curation" not in other.quality


def test_a_quantity_keeps_its_id_across_rebuilds(tmp_path):
    def molecule():
        record = json.loads(open("temp_data/CHEMBL90555.json", encoding="utf-8").read())
        return single_molecule_card(
            chembl={"retrieved_at": "2026-02-01", "molecules": {"CHEMBL90555": record}}
        )

    card = molecule()
    first = card.add_literature_assertion(
        "properties.physchem.molecular_weight", "0.825 kDa", "pubmed:1", "curator-a"
    )
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)
    again = molecule()
    store.apply(again)
    (record,) = again.quality["curation"]
    assert record["source_assertion_id"] == first["source_assertion_id"]
    assert record["outcome"] == "corroborates"
    assertion = again.source_assertion_store.get(record["source_assertion_id"])
    assert assertion["asserted_value"] == "0.825 kDa"  # as written


def test_the_file_is_versioned_and_checked(tmp_path):
    path = tmp_path / "curation.jsonl"
    path.write_text('{"sabueso_curations": {"format": 99}}\n', encoding="utf-8")
    with pytest.raises(StorageError, match="format"):
        sabueso.CurationStore(path).records()
    path.write_text('{"something": "else"}\n', encoding="utf-8")
    with pytest.raises(StorageError, match="not a Sabueso curation store"):
        sabueso.CurationStore(path).records()
    assert sabueso.CurationStore(tmp_path / "missing.jsonl").records() == []


def test_retracting_an_unknown_record_is_refused(tmp_path):
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    with pytest.raises(StorageError):
        store.retract("SA_Literature_pubmed:1_0000", "why", "who")


def test_resolve_refuses_a_wrong_curations_argument(resolver):
    with pytest.raises(sabueso.core.errors.ArgumentError):
        sabueso.resolve("P60174", resolver=resolver, curations=42)
