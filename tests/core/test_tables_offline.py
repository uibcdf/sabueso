"""Card views as flat rows and DataFrames (uibcdf/sabueso#46).

Quantities stay quantities in rows and, by default, in DataFrames; numbers in a named
unit only when asked. pandas is optional, checked by DepDigest.
"""

import importlib.util

import pytest
import pyunitwizard as puw

import sabueso
from sabueso.core.errors import ArgumentError, LibraryNotFoundError
from sabueso.core.tables import TABLES
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.alphafold import FixtureAlphaFoldClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.interpro import FixtureInterProClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient

HAS_PANDAS = importlib.util.find_spec("pandas") is not None


@pytest.fixture(scope="module")
def tctim():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = sabueso.resolve(
        "P52270",
        resolver=resolver,
        profile="structural_baseline@1",
        chembl_client=FixtureChEMBLClient("temp_data"),
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        interpro_client=FixtureInterProClient("temp_data"),
        predicted_structures=True,
        alphafold_client=FixtureAlphaFoldClient("temp_data"),
    )
    return card


@pytest.fixture(scope="module")
def deck(tctim):
    return sabueso.ligand_deck(
        tctim,
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
    )


def _flat(rows):
    """Every cell is one value: text, number, bool, None or a quantity."""
    for row in rows:
        for value in row.values():
            if value is None or isinstance(value, (str, int, float, bool)):
                continue
            assert puw.is_quantity(value), value


@pytest.mark.parametrize("view", sorted(v for v in TABLES if v != "ligands"))
def test_every_view_has_flat_rows(tctim, view):
    rows = tctim.table(view)
    assert rows
    assert len({tuple(r) for r in rows}) == 1  # the same columns in every row
    _flat(rows)


def test_ligands_take_the_deck(tctim, deck):
    rows = tctim.table("ligands", deck=deck)
    _flat(rows)
    assert all(r["label"] for r in rows)


def test_one_row_per_measurement_with_its_quantity(tctim):
    rows = tctim.table("bioactivities", include_indirect=True)
    assert len(rows) == len(tctim.relationships("has_bioactivity"))
    potency = next(r for r in rows if r["units"] == "nM" and r["relation"] == "=")
    assert puw.is_quantity(potency["normalized"])


def test_view_options_are_passed_and_checked(tctim):
    with pytest.raises(ArgumentError):
        tctim.table("nonexistent")
    import argdigest

    with pytest.raises(argdigest.UnknownArgumentError):
        tctim.table("structures", include_indirect=True)  # a bioactivities option


@pytest.mark.skipif(not HAS_PANDAS, reason="pandas is optional")
def test_a_dataframe_keeps_quantities_unless_a_unit_is_named(tctim):
    rows = tctim.table("bioactivities", include_indirect=True)
    df = sabueso.to_dataframe(rows)
    assert puw.is_quantity(df["normalized"].dropna().iloc[0])
    # Potencies and single-point percentages share the column: no silent partial
    # conversion.
    from sabueso.core.errors import SchemaError

    with pytest.raises(SchemaError, match="percent"):
        sabueso.to_dataframe(rows, units={"normalized": "micromolar"})
    rows = [r for r in rows if r["units"] == "nM"]
    df = sabueso.to_dataframe(rows)
    nm = sabueso.to_dataframe(rows, units={"normalized": "micromolar"})
    assert "normalized [micromolar]" in nm.columns
    assert nm.attrs["units"] == {"normalized [micromolar]": "micromolar"}
    first = df["normalized"].dropna().index[0]
    assert nm["normalized [micromolar]"][first] == pytest.approx(
        puw.get_value(puw.convert(df["normalized"][first], to_unit="micromolar"))
    )


def test_without_pandas_the_error_says_what_to_install(monkeypatch, tctim):
    import depdigest.core.checker as checker

    real = checker.is_installed
    monkeypatch.setattr(
        checker, "is_installed", lambda name: False if name == "pandas" else real(name)
    )
    import depdigest.core.decorator as decorator

    if hasattr(decorator, "is_installed"):
        monkeypatch.setattr(
            decorator,
            "is_installed",
            lambda name: False if name == "pandas" else real(name),
        )
    with pytest.raises(LibraryNotFoundError, match="pandas") as info:
        sabueso.to_dataframe(tctim.table("structures"))
    assert isinstance(info.value, ImportError)
    assert "conda install" in str(info.value)
