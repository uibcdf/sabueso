"""Physical quantities in cards (uibcdf/sabueso#32, devguide/archive/quantities.md).

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
    assert protein.meta["schema_version"] == CARD_SCHEMA_VERSION == "0.3.4"
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


def test_canary_a_value_reads_back_identically_through_every_path(protein, tmp_path):
    # MOLI's canary: 3 nM must never be read as 3 pM. A potency stored in nanomolar must
    # come back as the same amount through every read path, not merely the same number.
    from sabueso.core.deck import Deck
    from sabueso.tools.deck.storage import (
        load_deck_jsonl,
        load_deck_sqlite,
        save_deck_jsonl,
        save_deck_sqlite,
    )

    template = "relationships.has_bioactivity.measurement.normalized"
    written = puw.get_value(
        protein.quantity_columns(template)["nanomolar"], "nanomolar"
    )
    save_card_json(protein, tmp_path / "c.json")
    save_card_sqlite(protein, tmp_path / "c.db")
    save_deck_jsonl(Deck([protein]), tmp_path / "d.jsonl")
    save_deck_sqlite(Deck([protein]), tmp_path / "d.db")
    readers = (
        Card.from_dict(json.loads(json.dumps(protein.to_dict()))),
        load_card_json(tmp_path / "c.json"),
        load_card_sqlite(tmp_path / "c.db", card_id=protein.id),
        load_deck_jsonl(tmp_path / "d.jsonl").cards[0],
        load_deck_sqlite(tmp_path / "d.db").cards[0],
    )
    for loaded in readers:
        column = loaded.quantity_columns(template)["nanomolar"]
        assert list(puw.get_value(column, to_unit="nanomolar")) == list(written)
        # The conversion adds float noise (~1e-16 relative); a scale error is 1e3.
        assert list(puw.get_value(column, to_unit="picomolar")) == pytest.approx(
            [v * 1000 for v in written], rel=1e-12
        )


def _resealed(data):
    """Seal ``data`` again with PyUnitWizard directly, bypassing Sabueso's writer: a
    coherent edit of nodes and seal that only the reader's own expectations can catch."""
    import numpy as np
    from pyunitwizard import QuantityRecordBundle

    from sabueso.core.quantities import _columns

    data["quantities"] = QuantityRecordBundle.from_quantities(
        {
            key: puw.quantity(np.asarray(values), unit, form="pint")
            for key, (unit, values) in _columns(data).items()
        }
    ).to_dict()
    return data


def _resolution(data):
    return next(
        r["qualifiers"]["resolution"]
        for r in data["relationship_store"]
        if r["predicate"] == "has_structure" and r["qualifiers"].get("resolution")
    )


@pytest.mark.parametrize(
    "unit, factor",
    [
        ("second", 1.0),  # another dimension
        ("nanometer", 0.1),  # the same amount, in a unit Sabueso did not negotiate
    ],
)
def test_a_coherent_reseal_in_another_unit_is_refused(protein, unit, factor):
    data = _through_json(protein)
    node = _resolution(data)
    node["value"], node["unit"] = node["value"] * factor, unit
    with pytest.raises(StorageError, match="negotiated"):
        Card.from_dict(_resealed(data))


def test_the_writer_refuses_a_quantity_where_none_was_negotiated(protein):
    card = Card.from_dict(_through_json(protein))
    card.sections["sequence"]["fake"] = {"value": 1.0, "unit": "angstrom"}
    with pytest.raises(SchemaError, match="NEGOTIATED_UNITS"):
        card.to_dict()


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
