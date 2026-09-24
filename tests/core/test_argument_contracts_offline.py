"""Argument contracts at the public API, through ArgDigest (uibcdf/sabueso#31).

Integrated as in the sibling components (MolSysMT, MolSysViewer): ``sabueso/_argdigest.py``,
one digester per argument name, and ``skip_digestion`` on every decorated function.
"""

import importlib
import inspect
import warnings

import argdigest
import pytest

from sabueso import (
    ambiguity_deck,
    ligand_deck,
    resolve_molecule_card,
    resolve_protein_card,
)
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, SabuesoError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient

PUBLIC_TOOLS = [
    resolve_protein_card,
    resolve_molecule_card,
    ligand_deck,
    ambiguity_deck,
    Card.bioactivities,
]


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _structures_requested(card):
    return [
        e["structure"]
        for e in card.quality["enrichments"]
        if e.get("source") == "RCSB PDB"
    ]


def test_every_parameter_of_every_public_tool_has_a_digester():
    # STRICTNESS="warn" would only warn at call time; this makes the gap a failure.
    missing = []
    for tool in PUBLIC_TOOLS:
        for name in inspect.signature(inspect.unwrap(tool)).parameters:
            if name == "self":
                continue
            try:
                module = importlib.import_module(
                    f"sabueso._private.argdigest.argument.{name}"
                )
            except ModuleNotFoundError:
                missing.append(f"{tool.__name__}({name})")
                continue
            if not callable(getattr(module, f"digest_{name}", None)):
                missing.append(f"{tool.__name__}({name})")
    assert missing == []


def test_a_single_pdb_id_is_one_structure_not_four_characters(resolver):
    # Before ArgDigest, structures="1SUX" iterated the string: four requests, four
    # "not found" outcomes, and a card silently without its structure.
    card, _ = resolve_protein_card("P52270", resolver, structures="1sux")
    assert _structures_requested(card) == ["1SUX"]


@pytest.mark.parametrize(
    "call",
    [
        lambda r: resolve_protein_card(
            "P52270", r, structures=["1SUX", "not-a-pdb-id"]
        ),
        lambda r: resolve_protein_card("P52270", r, chembl={"limt": 10}),
        lambda r: resolve_protein_card("P52270", r, chembl={"limit": 0}),
        lambda r: resolve_protein_card("P52270", r, string={"required_score": 2000}),
        lambda r: resolve_protein_card("P52270", r, ligand_sites="yes"),
        lambda r: resolve_protein_card("   ", r),
        lambda r: resolve_protein_card("P52270", resolver="https://rest.uniprot.org"),
        lambda r: resolve_protein_card("P52270", r, chembl={}, chembl_client="ChEMBL"),
        lambda r: resolve_molecule_card(""),
        lambda r: ligand_deck({"meta": {}}),
        lambda r: ambiguity_deck(None),
    ],
)
def test_a_wrong_value_is_refused_before_anything_runs(resolver, call):
    with pytest.raises(ArgumentError) as info:
        call(resolver)
    error = info.value
    assert error.code == "SABUESO-E-ARG-001"
    assert isinstance(error, SabuesoError) and isinstance(error, ValueError)


def test_an_unsupported_identifier_is_still_an_answer_not_an_argument_error():
    # Whether an identifier names a supported record is the resolver's answer.
    card, resolution = resolve_molecule_card("not-an-identifier", unichem=False)
    assert card is None and resolution.status == "unsupported"


def test_an_unknown_keyword_is_refused_like_python_would(resolver):
    with pytest.raises(argdigest.UnknownArgumentError):
        resolve_protein_card(
            "P52270", resolver, structure=["1SUX"]
        )  # typo for structures


def test_options_reach_the_source_client_normalized(resolver):
    from sabueso._private.smonitor.warnings import EnrichmentTruncatedWarning

    with pytest.warns(EnrichmentTruncatedWarning):  # 5 of 493: truncation is reported
        card, _ = resolve_protein_card(
            "P52270",
            resolver,
            chembl={"limit": 5},
            chembl_client=FixtureChEMBLClient("temp_data"),
        )
    (enrichment,) = [e for e in card.quality["enrichments"] if e["source"] == "ChEMBL"]
    assert enrichment["limit"] == 5


def test_no_digestion_warnings_on_ordinary_calls(resolver):
    with warnings.catch_warnings():
        warnings.simplefilter("error", argdigest.DigestNotDigestedWarning)
        resolve_protein_card("P52270", resolver, structures=["1SUX"])


def test_skip_digestion_false_is_digested_and_a_false_non_boolean_is_refused(resolver):
    # A truthy value switches digestion off before the flag itself is digested (ArgDigest
    # checks SKIP_PARAM first), so only a falsy non-boolean can reach its digester.
    with pytest.raises(ArgumentError):
        resolve_protein_card("P52270", resolver, skip_digestion=0)
