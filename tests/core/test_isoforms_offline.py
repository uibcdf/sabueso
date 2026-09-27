"""UniProt isoforms, alternative sequences and secondary structure; deletions and
isoform-restricted comments kept as stated (uibcdf/sabueso#80).

Frozen UniProt entries (release 2026_03): human TIM P60174 (three isoforms, secondary
structure read from four PDB entries) and mu-opioid receptor P35372 (18 isoforms,
deletions stated as natural variants, comments restricted to one isoform).
"""

import json
from pathlib import Path

import pytest

import sabueso
from sabueso.core.curation import ITEM_IDENTITY
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


def _mapping(accession):
    entry = json.loads(Path(f"temp_data/{accession}.json").read_text(encoding="utf-8"))
    return map_protein(entry, "2026-09-27")


def _span(item):
    sequence = item["location"]["sequence"]
    return sequence["start"], sequence["end"]


def test_isoforms_are_listed_as_the_entry_states_them():
    fields = _mapping("P60174")["fields"]
    assert fields["annotations.isoforms"] == [
        {"isoform_id": "P60174-1", "name": "1", "sequence_status": "Displayed"},
        {
            "isoform_id": "P60174-3",
            "name": "2",
            "sequence_status": "Described",
            "alternative_sequence_ids": ["VSP_060722"],
        },
        {
            "isoform_id": "P60174-4",
            "name": "3",
            "sequence_status": "Described",
            "alternative_sequence_ids": ["VSP_060721"],
        },
    ]
    assert fields["annotations.alternative_products"] == {
        "events": ["Alternative promoter usage", "Alternative splicing"]
    }
    receptor = _mapping("P35372")["fields"]
    assert len(receptor["annotations.isoforms"]) == 18
    assert receptor["annotations.isoforms"][1]["synonyms"] == ["MOR1A", "MOR-1A"]
    # The note says the list may be incomplete: kept, since an absent isoform is not
    # evidence that it does not exist.
    assert (
        receptor["annotations.alternative_products"]["note"]
        == "Additional isoforms seem to exist."
    )


def test_an_alternative_sequence_names_the_isoforms_the_entry_links_to_it():
    items = _mapping("P60174")["features"]["features_positional.alternative_sequence"]
    by_id = {i["feature_id"]: i for i in items}
    extension = by_id["VSP_060722"]
    assert _span(extension) == (1, 1)
    assert extension["substitution"] == {
        "original": "M",
        "alternatives": ["MAEDGEEAEFHFAALYISGQWPRLRADTDLQRLGSSAM"],
    }
    assert extension["isoform_ids"] == ["P60174-3"]
    assert extension["description"] == "in isoform 2"
    # One segment shared by three isoforms of the receptor.
    receptor = _mapping("P35372")["features"][
        "features_positional.alternative_sequence"
    ]
    shared = next(i for i in receptor if i["feature_id"] == "VSP_042327")
    assert shared["isoform_ids"] == ["P35372-12", "P35372-14", "P35372-15"]


def test_a_deletion_is_stated_as_missing_never_as_an_unspecified_change():
    # "1-82: Missing (in isoform 3)": UniProt's JSON gives an empty alternative sequence.
    items = _mapping("P60174")["features"]["features_positional.alternative_sequence"]
    missing = next(i for i in items if i["feature_id"] == "VSP_060721")
    assert (_span(missing), missing["substitution"]) == ((1, 82), {"missing": True})
    # A natural variant that deletes residues 388-400 of the receptor.
    variants = _mapping("P35372")["features"]["features_positional.natural_variant"]
    deletion = next(i for i in variants if _span(i) == (388, 400))
    assert deletion["substitution"] == {"missing": True}
    # A substitution with residues is never marked missing.
    assert all(
        "missing" not in (v.get("substitution") or {})
        for v in _mapping("P60174")["features"]["features_positional.natural_variant"]
    )


def test_curation_tells_a_deletion_from_a_substitution_at_the_same_positions():
    same = ITEM_IDENTITY["features_positional.natural_variant"]
    location = {"sequence": {"start": 388, "end": 400}}
    deletion = {"location": location, "substitution": {"missing": True}}
    unstated = {"location": location, "substitution": {}}
    assert same(deletion) != same(unstated)
    assert same(deletion) == same(
        {"location": location, "substitution": {"missing": 1}}
    )


def test_secondary_structure_keeps_the_structure_each_segment_was_read_from():
    items = _mapping("P60174")["features"]["features_positional.secondary_structure"]
    elements = [i["element"] for i in items]
    counts = {e: elements.count(e) for e in set(elements)}
    assert counts == {"helix": 18, "strand": 10, "turn": 3}
    first = items[0]
    assert (_span(first), first["element"], first["structures"]) == (
        (4, 6),
        "helix",
        ["pdb:6UPF"],
    )
    # One entry mixes the structures it reads from.
    assert {s for i in items for s in i["structures"]} == {
        "pdb:9F69",
        "pdb:6UPF",
        "pdb:4POC",
        "pdb:6UP8",
    }


def test_a_comment_restricted_to_an_isoform_keeps_the_restriction():
    mapping = _mapping("P35372")
    function = [
        a
        for a in mapping["source_assertions"]
        if a["field_path"] == "annotations.function"
    ]
    restricted = {
        a["source_metadata"]["molecule"]
        for a in function
        if "molecule" in (a.get("source_metadata") or {})
    }
    assert restricted == {"Isoform 12", "Isoform 16", "Isoform 17"}
    # The value stays the stated text; the restriction is on its SourceAssertion.
    assert all(isinstance(a["asserted_value"], str) for a in function)
    assert any("molecule" not in (a.get("source_metadata") or {}) for a in function)


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def test_an_entry_with_one_isoform_does_not_state_isoforms(resolver):
    states = {}
    for accession in ("P60174", "P52270"):
        card, _ = sabueso.resolve(accession, resolver=resolver)
        rows = card.knowledge_state()["rows"]
        states[accession] = {
            r["area"]: r["state"] for r in rows if r["source"] == "UniProt"
        }
    assert states["P60174"]["annotations.isoforms"] == "known"
    assert states["P60174"]["features_positional.secondary_structure"] == "known"
    # TcTIM's entry lists no alternative products: not stated, never "one isoform".
    assert states["P52270"]["annotations.isoforms"] == "not_stated"
    assert states["P52270"]["features_positional.alternative_sequence"] == "not_stated"


def test_only_a_card_holding_an_old_deletion_reports_the_gap():
    from sabueso.core.migration import _has

    path = "features_positional.natural_variant.substitution.missing"
    item = {"location": {"sequence": {"start": 388, "end": 400}}}
    old = {"sections": {"features_positional": {"natural_variant": {"value": [item]}}}}
    assert not _has(old, path)  # a 0.3.5 deletion: no substitution at all
    item["substitution"] = {"original": "E", "alternatives": ["D"]}
    assert _has(old, path)
    assert _has({"sections": {}}, path)  # no variants, nothing to refresh
