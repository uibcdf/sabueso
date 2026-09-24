"""Views name references one way, and give molecules a readable label (uibcdf/sabueso#47).

A key whose value is a reference (``<namespace>:<id>``) ends in ``_ref`` in every view:
``molecule_ref``, ``ligand_ref``, ``structure_ref``, ``partner_ref``, ``publication_ref``.
"""

import re
import warnings

import pytest

from sabueso import ligand_deck, resolve_protein_card
from sabueso.core.labels import molecule_label
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.interpro import FixtureInterProClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient

REF = re.compile(r"^(?:sabueso:)?[a-z][a-z0-9_.]*:\S")
#: Keys whose value may be a reference without naming one: a summary of any value.
EXEMPT = {"value"}


@pytest.fixture(scope="module")
def views():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    chembl = FixtureChEMBLClient("temp_data")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        card, _ = resolve_protein_card(
            "P52270",
            resolver,
            structures="all",
            chembl={},
            chembl_client=chembl,
            interfaces=True,
            ligand_sites=True,
            family_sites=True,
            pdbe_kb_client=FixturePDBeKBClient("temp_data"),
            interpro_client=FixtureInterProClient("temp_data"),
        )
    deck = ligand_deck(
        card, chembl_client=chembl, ccd_client=FixtureCCDClient("temp_data")
    )
    return {
        "structures": card.structures(),
        "bioactivities": card.bioactivities(),
        "ligand_sites": card.ligand_sites(),
        "ligands": card.ligands(deck),
        "compare_ligands": card.compare_ligands(deck, card, deck),
        "oligomer": card.oligomer(),
        "literature": card.literature(),
    }


def _offending(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}"
            if (
                isinstance(value, str)
                and REF.match(value)
                and not key.endswith("_ref")
                and key not in EXEMPT
            ):
                yield here
            yield from _offending(value, here)
    elif isinstance(node, list):
        for item in node[:20]:
            yield from _offending(item, f"{path}[]")


@pytest.mark.parametrize(
    "name",
    [
        "structures",
        "bioactivities",
        "ligand_sites",
        "ligands",
        "compare_ligands",
        "oligomer",
        "literature",
    ],
)
def test_every_reference_key_ends_in_ref(views, name):
    view = views[name]
    # Derivation records describe a rule, not the view's items.
    items = {
        k: v for k, v in view.items() if k not in ("classification", "checks", "rules")
    }
    assert sorted(set(_offending(items))) == []


def test_molecules_carry_a_readable_label(views):
    items = views["ligands"]["items"]
    assert all(i["label"] for i in items)
    sources = {i["label_source"] for i in items}
    assert sources <= {"name", "chembl", "pdb.ligand", "inchikey"}
    bts = next(i for i in items if "pdb.ligand:BTS" in i["records"])
    assert bts["label_source"] in ("name", "chembl")
    shared = views["compare_ligands"]["shared"][0]
    assert shared["label"] and shared["label_source"]
    assert all(i["label"] for i in views["bioactivities"]["items"])


@pytest.mark.parametrize(
    "name, refs, anchor, expected",
    [
        ("Suramin", ["chembl:CHEMBL1"], "x:INCHI", ("Suramin", "name")),
        (
            None,
            ["pdb.ligand:BTS", "chembl:CHEMBL2", "chembl:CHEMBL1"],
            "x:K",
            ("CHEMBL1", "chembl"),
        ),
        (None, ["pdb.ligand:PGA"], "x:K", ("PGA", "pdb.ligand")),
        (
            None,
            [],
            "sabueso:small_molecule:inchikey:ABC-DEF-N",
            ("ABC-DEF-N", "inchikey"),
        ),
    ],
)
def test_label_order(name, refs, anchor, expected):
    assert molecule_label(name, refs, anchor) == expected
