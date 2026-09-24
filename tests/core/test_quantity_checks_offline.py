"""Quantities returned by views and columns, and the two domain checks of #32.

A digest cannot detect a source that is wrong but internally consistent. These checks
cover the error class that matters most for potencies, a unit slip, from two angles: a
stated pChEMBL that disagrees with the normalized potency, and equivalent measurements
that differ by exactly 3 or 6 orders of magnitude.
"""

import copy
import json

import pytest
import pyunitwizard as puw

from sabueso import resolve_protein_card
from sabueso.core.bioactivities import (
    PCHEMBL_RULE,
    SCALE_RULE,
    pchembl_consistent,
)
from sabueso.core.quantities import quantity_node, scale_discrepancy
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.resolver.field_resolver import resolve_field
from sabueso.resolver.loader import load_selection_rules
from sabueso.tools.db.chembl import FixtureChEMBLClient

TCTIM, HSTIM = "P52270", "P60174"


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _card(resolver, accession, chembl_dir="temp_data"):
    card, _ = resolve_protein_card(
        accession,
        resolver,
        chembl={},
        chembl_client=FixtureChEMBLClient(chembl_dir),
    )
    return card


def _measurements(card):
    view = card.bioactivities(include_indirect=True)
    return {m["activity_id"]: m for i in view["items"] for m in i["measurements"]}


# --- pChEMBL consistency -----------------------------------------------------------------


@pytest.mark.parametrize(
    "pchembl, value_nM, relation, expected",
    [
        (4.58, 26000.0, "=", True),  # ChEMBL states 4.58 for 4.58503: not half-up
        (4.59, 26000.0, "=", True),
        (4.60, 26000.0, "=", False),
        (8.52, 3.0, "=", True),
        (11.52, 3.0, "=", False),  # 3 nM stated as if it were 3 pM
        (5.52, 3.0, "=", False),  # or as if it were 3 µM
        (8.52, 3.0, "<", None),  # a bound has no pChEMBL to check
        (None, 3.0, "=", None),
    ],
)
def test_pchembl_is_checked_against_the_normalized_potency(
    pchembl, value_nM, relation, expected
):
    node = quantity_node(value_nM, "nanomolar")
    assert pchembl_consistent(pchembl, node, relation) is expected


def test_pchembl_is_not_checked_against_a_percentage():
    assert pchembl_consistent(5.0, quantity_node(50.0, "percent"), "=") is None


def test_every_stated_pchembl_in_the_fixtures_is_consistent(resolver):
    # ChEMBL_37, TcTIM and HsTIM: 38 measurements with pChEMBL, the largest deviation
    # 0.00503 (26000 nM stated as 4.58).
    for accession in (TCTIM, HSTIM):
        flagged = [
            m["activity_id"]
            for m in _measurements(_card(resolver, accession)).values()
            if "pchembl_inconsistent" in m["flags"]
        ]
        assert flagged == []


# --- Scale discrepancy -------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, orders",
    [
        (26.0, 26000.0, 3),
        (26000.0, 26.0, 3),
        (0.026, 26000.0, 6),
        (26.0, 26001.0, None),
        (26.0, 2600.0, None),  # 2 orders is not a unit slip between SI prefixes
        (26.0, 26.0, None),
        (0.0, 26.0, None),
        (True, 1000.0, None),
        ("26", 26000.0, None),
    ],
)
def test_scale_discrepancy(a, b, orders):
    assert scale_discrepancy(a, b) == orders


@pytest.fixture
def slipped(tmp_path):
    """HsTIM's ChEMBL response with one IC50 repeated at 1000x its value, as a later
    paper would report it after writing nM where µM was meant."""
    saved = json.loads(
        open("temp_data/chembl/CHEMBL4880.json", encoding="utf-8").read()
    )
    original = next(
        a
        for a in saved["activities"]
        if a["standard_units"] == "nM"
        and a["standard_relation"] == "="
        and a["standard_type"] == "IC50"
        and a["pchembl_value"]
    )
    slip = copy.deepcopy(original)
    slip["activity_id"] = 999000001
    slip["document_chembl_id"] = "CHEMBL_TEST_DOC"
    slip["standard_value"] = str(float(original["standard_value"]) * 1000)
    # The pChEMBL is copied as is, so it now disagrees with the slipped value.
    saved["activities"].append(slip)
    saved["total_count"] += 1
    (tmp_path / "chembl").mkdir()
    (tmp_path / "chembl" / "CHEMBL4880.json").write_text(json.dumps(saved))
    return tmp_path, (original["activity_id"], slip["activity_id"])


def test_a_unit_slip_between_equivalent_measurements_is_flagged(resolver, slipped):
    directory, (original, slip) = slipped
    measurements = _measurements(_card(resolver, HSTIM, directory))
    assert f"scale_discrepancy:3:{slip}" in measurements[original]["flags"]
    assert f"scale_discrepancy:3:{original}" in measurements[slip]["flags"]
    # The copied pChEMBL disagrees with the slipped value, and only with that one.
    assert "pchembl_inconsistent" in measurements[slip]["flags"]
    assert "pchembl_inconsistent" not in measurements[original]["flags"]
    # Nothing is corrected: both values stay as the sources state them.
    ratio = puw.get_value(
        measurements[slip]["normalized"] / measurements[original]["normalized"]
    )
    assert pytest.approx(float(ratio)) == 1000.0


def test_the_checks_are_recorded_as_rules(resolver):
    view = _card(resolver, HSTIM).bioactivities()
    assert [c["rule"] for c in view["checks"]] == [PCHEMBL_RULE, SCALE_RULE]


def test_a_field_conflict_marks_a_scale_discrepancy():
    weights = [
        make_source_assertion(
            "properties.physchem.molecular_weight", v, src, "r", "2026-09-24"
        )
        for v, src in (("373.4", "ChEMBL"), ("373400.0", "PubChem"))
    ]
    for sa in weights:  # as the mappings store them: the text verbatim, and a number
        sa["normalized_value"] = float(sa["asserted_value"])
    result = resolve_field(
        "properties.physchem.molecular_weight", weights, load_selection_rules()
    )
    assert result["conflict"]["scale_discrepancy"] == [
        {"orders": 3, "values": [373.4, 373400.0]}
    ]


# --- Quantities out --------------------------------------------------------------------


def test_the_bioactivity_view_returns_the_normalized_potency_as_a_quantity(resolver):
    measurements = _measurements(_card(resolver, HSTIM))
    potency = next(
        m for m in measurements.values() if m["units"] == "nM" and m["value"] == 62.46
    )
    q = potency["normalized"]
    assert puw.is_quantity(q)
    assert puw.get_value(puw.convert(q, to_unit="micromolar")) == pytest.approx(0.06246)
    # The source's own value and unit stay as stated.
    assert (potency["value"], potency["units"]) == (62.46, "nM")


def test_columns_are_array_quantities_one_per_unit(resolver):
    card = _card(resolver, HSTIM)
    (resolution,) = card.quantity_columns(
        "relationships.has_structure.resolution"
    ).values()
    assert puw.get_unit(resolution) == puw.get_unit(puw.quantity(1.0, "angstrom"))
    assert len(puw.get_value(resolution)) == len(card.relationships("has_structure"))

    potencies = card.quantity_columns(
        "relationships.has_bioactivity.measurement.normalized"
    )
    assert sorted(potencies) == ["nanomolar", "percent"]  # never mixed, never converted
    assert card.quantity_columns("no.such.path") == {}
