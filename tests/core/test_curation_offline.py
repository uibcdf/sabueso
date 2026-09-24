"""Curated literature assertions on existing fields (uibcdf/sabueso#41, part 2).

A curated assertion is compared with what other sources state, never given priority,
and never discarded; a difference is recorded and warned about, for a reader to judge.
"""

import json

import pytest
import pyunitwizard as puw

from sabueso import resolve_protein_card
from sabueso._private.smonitor.warnings import CuratedDisagreementWarning
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, SchemaError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.card.small_molecule import single_molecule_card

VARIANT = "features_positional.natural_variant"
MUTAGENESIS = "features_positional.mutagenesis"
MW = "properties.physchem.molecular_weight"
E105D = {"original": "E", "alternatives": ["D"]}


@pytest.fixture
def hstim():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = resolve_protein_card("P60174", resolver)
    return card


@pytest.fixture
def molecule():
    record = json.loads(open("temp_data/CHEMBL90555.json", encoding="utf-8").read())
    return single_molecule_card(
        chembl={"retrieved_at": "2026-02-01", "molecules": {"CHEMBL90555": record}}
    )


def _uniprot_variant(card, position):
    return next(
        i
        for i in card.get(VARIANT)["value"]
        if i["location"]["sequence"]["start"] == position
    )


def test_a_curated_assertion_is_a_literature_source_assertion(hstim):
    record = hstim.add_literature_assertion(
        MUTAGENESIS,
        {
            "start": 14,
            "substitution": {"original": "K", "alternatives": ["M"]},
            "description": "Loss of activity.",
        },
        "pubmed:18562316",
        "curator-a",
        locator="Table 1",
        quote="K13M is inactive",
        eco_code="ECO:0000269",
        curated_at="2026-09-24",
    )
    assert record["outcome"] == "new"
    assertion = hstim.source_assertion_store.get(record["source_assertion_id"])
    assert assertion["source"] == {
        "type": "literature",
        "name": "Literature",
        "record_id": "pubmed:18562316",
    }
    assert assertion["subject_ref"] == "uniprot:P60174"
    assert assertion["source_metadata"]["curation"] == {
        "curator": "curator-a",
        "curated_at": "2026-09-24",
        "locator": "Table 1",
        "quote": "K13M is inactive",
    }
    # The shorthand "start" became a location in the card's UniProt numbering.
    item = assertion["asserted_value"]
    assert item["location"]["sequence"] == {
        "sequence_id": "UniProt:P60174",
        "start": 14,
        "end": 14,
        "indexing": "1-based",
    }
    assert item in hstim.get(MUTAGENESIS)["value"]


def test_the_same_item_with_other_content_differs_and_is_flagged(hstim):
    uniprot = _uniprot_variant(hstim, 105)
    with pytest.warns(CuratedDisagreementWarning, match="differs"):
        record = hstim.add_literature_assertion(
            VARIANT,
            {
                "start": 105,
                "substitution": E105D,
                "description": "destabilizes the dimer",
            },
            "pubmed:18562316",
            "curator-a",
        )
    assert record["outcome"] == "differs"
    (conflict,) = [
        c for c in hstim.quality["conflicts"] if c["type"] == "curated_difference"
    ]
    assert conflict["values"][0] == uniprot  # nothing is discarded or overridden
    assert _uniprot_variant(hstim, 105) == uniprot
    assert len([i for i in hstim.get(VARIANT)["value"] if _pos(i) == 105]) == 2


def _pos(item):
    return item["location"]["sequence"]["start"]


def test_the_same_item_with_the_same_content_corroborates(hstim):
    record = hstim.add_literature_assertion(
        VARIANT, _uniprot_variant(hstim, 42), "pubmed:9338582", "curator-a"
    )
    assert record["outcome"] == "corroborates"
    assert record["source_assertion_id"] in hstim.get(VARIANT)["source_assertion_ids"]
    assert "conflicts" not in hstim.quality


def test_free_text_is_added_but_never_compared(hstim):
    record = hstim.add_literature_assertion(
        "annotations.subunit", "Homodimer", "pubmed:8061610", "curator-a"
    )
    assert record["outcome"] == "not_compared"


def test_the_same_statement_twice_is_recorded_once(hstim):
    args = (VARIANT, _uniprot_variant(hstim, 42), "pubmed:9338582", "curator-a")
    first = hstim.add_literature_assertion(*args)
    again = hstim.add_literature_assertion(*args)
    assert again == first
    assert len(hstim.quality["curation"]) == 1
    # The same value at another place in the paper is another assertion.
    other = hstim.add_literature_assertion(*args, locator="Fig. 4")
    assert other["source_assertion_id"] != first["source_assertion_id"]


@pytest.mark.parametrize(
    "value, outcome",
    [
        ("824.97 Da", "corroborates"),
        ("825 Da", "corroborates"),  # agrees at the precision it is stated with
        ("0.825 kDa", "corroborates"),
        ({"value": 824.97, "unit": "dalton"}, "corroborates"),
        ("0.9 kDa", "differs"),  # 900 ± 50 Da does not include 824.97
        ("830 Da", "differs"),
    ],
)
def test_a_curated_quantity_is_compared_at_its_stated_precision(
    molecule, value, outcome
):
    with pytest.warns() if outcome == "differs" else _no_warning():
        record = molecule.add_literature_assertion(MW, value, "pubmed:1", "curator-a")
    assert record["outcome"] == outcome
    # A database value is never displaced by a curated one.
    assert molecule.get(MW)["value"] == 824.97
    assertion = molecule.source_assertion_store.get(record["source_assertion_id"])
    assert assertion["asserted_value"] == value  # kept as written


class _no_warning:
    def __enter__(self):
        import warnings

        self._catch = warnings.catch_warnings()
        self._catch.__enter__()
        warnings.simplefilter("error", CuratedDisagreementWarning)

    def __exit__(self, *exc):
        return self._catch.__exit__(*exc)


def test_a_quantity_needs_its_unit(molecule):
    with pytest.raises(SchemaError, match="bare number"):
        molecule.add_literature_assertion(MW, 824.97, "pubmed:1", "curator-a")
    record = molecule.add_literature_assertion(
        MW, puw.quantity(824.97, "Da"), "pubmed:1", "curator-a"
    )
    assert record["outcome"] == "corroborates"


def test_method_dependent_values_compare_within_a_method(molecule):
    assert (
        molecule.add_literature_assertion(
            "properties.physchem.logp", 2.5, "pubmed:1", "curator-a"
        )["outcome"]
        == "not_comparable"
    )
    assert (
        molecule.add_literature_assertion(
            "properties.physchem.logp", 3.52, "pubmed:1", "curator-a", method="ALogP"
        )["outcome"]
        == "corroborates"
    )


def test_a_curated_value_fills_a_field_no_source_states(hstim):
    # Only for a field no database states; logP of a protein is just an example.
    record = hstim.add_literature_assertion(
        "properties.physchem.logp", 1.0, "pubmed:1", "curator-a"
    )
    assert record["outcome"] == "new"
    assert hstim.get("properties.physchem.logp")["value"] == 1.0


def test_curation_survives_storage_and_shows_in_the_literature_view(hstim):
    with pytest.warns(CuratedDisagreementWarning):
        hstim.add_literature_assertion(
            VARIANT,
            {
                "start": 105,
                "substitution": E105D,
                "description": "destabilizes the dimer",
            },
            "pubmed:18562316",
            "curator-a",
            locator="Fig. 2",
        )
    loaded = Card.from_dict(json.loads(json.dumps(hstim.to_dict())))
    assert loaded.quality["curation"] == hstim.quality["curation"]
    pubs = {p["ref"]: p for p in loaded.literature()["publications"]}
    (curated,) = pubs["pubmed:18562316"]["curated"]
    assert (curated["field_path"], curated["locator"], curated["outcome"]) == (
        VARIANT,
        "Fig. 2",
        "differs",
    )


@pytest.mark.parametrize(
    "change",
    [
        {"field_path": "identifiers.uniprot"},  # identity is never curated
        {"field_path": "sequence.primary"},
        {"publication": "PMID 18562316"},
        {"curator": ""},
        {"quote": "x" * 400},
        {"eco_code": "ECO:1"},
        {"curated_at": "yesterday"},
    ],
)
def test_wrong_arguments_are_refused(hstim, change):
    kwargs = dict(
        field_path="annotations.subunit",
        value="Homodimer",
        publication="pubmed:1",
        curator="curator-a",
    )
    kwargs.update(change)
    with pytest.raises(ArgumentError):
        hstim.add_literature_assertion(**kwargs)


@pytest.mark.parametrize(
    "field_path, value",
    [
        (MUTAGENESIS, {"description": "no position"}),
        (MUTAGENESIS, {"start": 14, "description": "no substitution"}),
        ("annotations.subunit", {"text": "not a text"}),
        ("annotations.disease", {"accession": "DI-1"}),
    ],
)
def test_an_item_must_fit_its_field(hstim, field_path, value):
    with pytest.raises(SchemaError):
        hstim.add_literature_assertion(field_path, value, "pubmed:1", "curator-a")
