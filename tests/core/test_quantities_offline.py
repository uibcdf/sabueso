"""Physical quantities in cards (uibcdf/sabueso#32, devguide/pending_proposals/quantities.md).

No number is stored without its unit; every stored card seals its quantities with a
PyUnitWizard QuantityRecordBundle (released in pyunitwizard 0.27.0); a change made
outside Sabueso is refused on read; and the session's unit policy never changes what a
card stores.
"""

import json
import re
from pathlib import Path

import pytest
import pyunitwizard as puw

from sabueso import resolve_protein_card
from sabueso.core.card import CARD_SCHEMA_VERSION, Card
from sabueso.core.errors import SchemaError, StorageError
from sabueso.core.quantities import iter_quantity_nodes, normalized_measurement
from sabueso.mappings.rcsb_structures import map_structure_entities
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.card.storage import (
    load_card_json,
    load_card_sqlite,
    save_card_json,
    save_card_sqlite,
)
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.uniprot import create_protein_card_from_file


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def protein():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = resolve_protein_card(
        "P52270",
        resolver,
        structures=["1SUX"],
        chembl={},
        chembl_client=FixtureChEMBLClient("temp_data"),
    )
    return card


@pytest.fixture(scope="module")
def molecule():
    return single_molecule_card(
        chembl={
            "retrieved_at": "2026-02-01",
            "molecules": {"CHEMBL90555": _load("temp_data/CHEMBL90555.json")},
        },
        pubchem={
            "retrieved_at": "2026-02-02",
            "compounds": {"5978": _load("temp_data/5978.json")},
        },
    )


def _through_json(card):
    return json.loads(json.dumps(card.to_dict()))


# --- every stored quantity carries its unit ------------------------------------------------------


def test_quantity_fields_carry_their_negotiated_unit(molecule, protein):
    assert molecule.get("properties.physchem.tpsa")["unit"] == "angstrom ** 2"
    assert molecule.get("properties.physchem.molecular_weight")["unit"] == "dalton"
    assert protein.get("sequence.molecular_weight")["unit"] == "dalton"
    # Counts and logarithmic scores are not quantities, and carry no unit.
    assert "unit" not in molecule.get("properties.physchem.hbd")
    assert "unit" not in molecule.get("properties.physchem.logp")


def test_a_quantity_is_returned_as_a_quantity(molecule):
    tpsa = molecule.quantity("properties.physchem.tpsa")
    assert puw.is_quantity(tpsa)
    assert puw.get_value(tpsa, to_unit="nm**2") == pytest.approx(
        molecule.get("properties.physchem.tpsa")["value"] / 100
    )
    with pytest.raises(SchemaError):
        molecule.quantity("properties.physchem.hbd")


def test_structure_resolution_and_contact_distances_are_quantities():
    (rel,) = map_structure_entities(_load("temp_data/rcsb/1HTI.json"), "x")[
        "relationships"
    ]
    assert rel["qualifiers"]["resolution"]["unit"] == "angstrom"
    assert "resolution_angstrom" not in rel["qualifiers"]
    contact = rel["qualifiers"]["ligands"][0]["instances"][0]["contacts"][0]
    assert contact["min_distance"]["unit"] == "angstrom"
    assert "min_distance_angstrom" not in contact


def test_bioactivities_are_normalized_explicitly_and_kept_verbatim(protein):
    measurements = [
        r["qualifiers"]["measurement"] for r in protein.relationships("has_bioactivity")
    ]
    assert measurements
    for m in measurements:
        normalized = m["normalized"]
        if m["value"] is None:
            assert normalized is None  # a comment-only record states no quantity
        elif m["units"] in ("nM", "uM", "µM", "mM", "pM", "M"):
            assert normalized["unit"] == "nanomolar"
        elif m["units"] == "%":
            assert normalized["unit"] == "percent"
        else:
            assert normalized is None  # never guessed
    # The source's statement stays as it was.
    assert {m["units"] for m in measurements} & {"nM", "uM", "%"}


@pytest.mark.parametrize(
    "value, units, expected",
    [
        (33.0, "uM", ("nanomolar", 33000.0)),
        (5.0, "pM", ("nanomolar", 0.005)),
        (12.0, "%", ("percent", 12.0)),
        (3.0, "nm", None),  # a length spelled like a concentration: never parsed
        (2.0, "ug.mL-1", None),  # not convertible without a molecular weight
        (None, "nM", None),
    ],
)
def test_the_chembl_vocabulary_is_explicit(value, units, expected):
    node = normalized_measurement(value, units)
    if expected is None:
        assert node is None
    else:
        assert (node["unit"], node["value"]) == (
            expected[0],
            pytest.approx(expected[1]),
        )


# --- the seal --------------------------------------------------------------------------------------


def test_a_stored_card_seals_its_quantities_in_columns(protein):
    data = _through_json(protein)
    assert protein.meta["schema_version"] == CARD_SCHEMA_VERSION == "0.3.0"
    keys = set(data["quantities"]["entries"])
    assert "sequence.molecular_weight|dalton" in keys
    assert "relationships.has_bioactivity.measurement.normalized|nanomolar" in keys
    assert "relationships.has_structure.resolution|angstrom" in keys
    # A column per path and unit, not an entry per value.
    assert len(keys) < 10 < sum(1 for _ in iter_quantity_nodes(data))
    assert Card.from_dict(data).to_dict() == data


def _first_bioactivity(data):
    return next(
        r
        for r in data["relationship_store"]
        if r["predicate"] == "has_bioactivity"
        and r["qualifiers"]["measurement"]["normalized"]
    )


TAMPERING = {
    "a node's value edited": lambda d: d["sections"]["sequence"][
        "molecular_weight"
    ].__setitem__("value", 1.0),
    "a node's unit edited": lambda d: _first_bioactivity(d)["qualifiers"][
        "measurement"
    ]["normalized"].__setitem__("unit", "picomolar"),
    "a quantity node added": lambda d: d["sections"]["sequence"].__setitem__(
        "fake", {"value": 1.0, "unit": "angstrom"}
    ),
    "a quantity node removed": lambda d: _first_bioactivity(d)["qualifiers"][
        "measurement"
    ].__setitem__("normalized", None),
    "a column edited in the seal": lambda d: d["quantities"]["entries"][
        "sequence.molecular_weight|dalton"
    ].__setitem__("values", [1.0]),
    "the seal deleted": lambda d: d.pop("quantities"),
}


@pytest.mark.parametrize("name", TAMPERING)
def test_a_change_made_outside_sabueso_is_refused(protein, name):
    data = _through_json(protein)
    TAMPERING[name](data)
    with pytest.raises(StorageError):
        Card.from_dict(data)


def test_the_session_unit_policy_never_changes_what_is_stored(molecule):
    reference = _through_json(molecule)
    with puw.context(standard_units=["angstrom", "ns", "K", "mole", "dalton"]):
        again = single_molecule_card(
            chembl={
                "retrieved_at": "2026-02-01",
                "molecules": {"CHEMBL90555": _load("temp_data/CHEMBL90555.json")},
            },
            pubchem={
                "retrieved_at": "2026-02-02",
                "compounds": {"5978": _load("temp_data/5978.json")},
            },
        )
        assert _through_json(again)["quantities"] == reference["quantities"]


def test_canary_a_value_reads_back_identically_through_every_path(tmp_path):
    # Written as 33 µM by ChEMBL; every reader path must return 33000 nM, never another
    # unit or scale (the error class of the Mars Climate Orbiter).
    card = create_protein_card_from_file(
        "temp_data/P52789.json", retrieved_at="2026-02-01"
    )
    mw = card.quantity("sequence.molecular_weight")
    save_card_json(card, tmp_path / "c.json")
    save_card_sqlite(card, tmp_path / "c.db")
    for loaded in (
        Card.from_dict(json.loads(json.dumps(card.to_dict()))),
        load_card_json(tmp_path / "c.json"),
        load_card_sqlite(tmp_path / "c.db", card_id=card.id),
    ):
        again = loaded.quantity("sequence.molecular_weight")
        assert puw.get_value(again, to_unit="dalton") == puw.get_value(
            mw, to_unit="dalton"
        )


# --- guard: no bare number leaves a quantity without a stated unit ---------------------------------


def test_no_value_is_extracted_without_a_target_unit():
    # Standard units belong to the user's session (uibcdf/moli#11); a value stripped of its
    # unit without `to_unit` is in whatever unit the session chose (uibcdf/molsysviewer#96).
    allowed = {
        "sabueso/core/quantities.py": 1
    }  # verify(): the unit is checked on the line before
    offenders = {}
    for path in Path("sabueso").rglob("*.py"):
        hits = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if re.search(r"\bget_value\(", line) and "to_unit" not in line
        ]
        if len(hits) > allowed.get(path.as_posix(), 0):
            offenders[path.as_posix()] = hits
    assert offenders == {}
