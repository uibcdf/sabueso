"""has_structure relationships, the ProteinCard structures view, and RCSB mapping.

uibcdf/sabueso#6, steps 4a (UniProt side) and 4b (RCSB side) of acceptance cases A9 and
A10.
"""

import json

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.merge import merge_mapping_results
from sabueso.core.structures import (
    coverage,
    coverage_class,
    merge_ranges,
    normalize_methods,
)
from sabueso.mappings.rcsb_structures import map_structure_entities
from sabueso.mappings.uniprot import _parse_pdb_chains, map_protein
from sabueso.tools.db.uniprot import create_protein_card_from_file

HSTIM_PEPTIDE_COMPLEXES = ["pdb:1KLG", "pdb:1KLU", "pdb:2IAM", "pdb:2IAN", "pdb:4E41"]


def _card(accession):
    return create_protein_card_from_file(
        f"temp_data/{accession}.json", retrieved_at="2026-02-01"
    )


def _item(view, ref):
    return next(i for i in view["items"] if i["structure_ref"] == ref)


def test_uniprot_chains_property_is_parsed():
    assert _parse_pdb_chains("A/B=2-249") == (["A", "B"], [[2, 249]])
    assert _parse_pdb_chains("A/B/C/D=3-18, A/B/C/D=44-100, A/B/C/D=123-251") == (
        ["A", "B", "C", "D"],
        [[3, 18], [44, 100], [123, 251]],
    )
    assert _parse_pdb_chains("A=-") == (["A"], [])


def test_coverage_and_its_derived_class():
    assert merge_ranges([[10, 20], [1, 5], [15, 30]]) == [[1, 5], [10, 30]]
    assert coverage([[2, 249]], 249) == 0.996
    assert coverage([], 249) is None
    assert coverage_class(0.996) == "full_length"
    assert coverage_class(0.805) == "partial"
    assert coverage_class(0.06) == "fragment_or_peptide"


def test_a9_human_tim_structures_exclude_peptide_complexes_visibly():
    card = _card("P60174")
    assert len(card.relationships(predicate="has_structure")) == 29

    view = card.structures()
    assert len(view["items"]) == 24
    assert view["excluded"] == HSTIM_PEPTIDE_COMPLEXES
    assert view["classification"]["rule"] == "structure_coverage_class@1"
    assert view["classification"]["parameters"] == {
        "full_length_min": 0.9,
        "partial_min": 0.3,
    }

    hti = _item(view, "pdb:1HTI")
    assert (hti["chains"], hti["ranges"], hti["coverage"]) == (
        ["A", "B"],
        [[2, 249]],
        0.996,
    )
    assert (hti["coverage_class"], hti["method"], hti["resolution_angstrom"]) == (
        "full_length",
        "X-ray",
        2.8,
    )
    assert hti["sources"] == ["UniProt"]

    klg = _item(card.structures(include_fragments=True), "pdb:1KLG")
    assert (klg["chains"], klg["ranges"], klg["coverage"], klg["coverage_class"]) == (
        ["C"],
        [[23, 37]],
        0.06,
        "fragment_or_peptide",
    )


def test_a10_tcruzi_tim_structures_include_a_loop_deletion_construct():
    card = _card("P52270")
    view = card.structures()
    assert len(view["items"]) == 7 and view["excluded"] == []

    tcd = _item(view, "pdb:1TCD")
    assert (tcd["ranges"], tcd["coverage"], tcd["coverage_class"]) == (
        [[3, 251]],
        0.992,
        "full_length",
    )
    q37 = _item(view, "pdb:3Q37")
    assert q37["ranges"] == [[3, 18], [44, 100], [123, 251]]
    assert (q37["coverage"], q37["coverage_class"]) == (0.805, "partial")


def test_structure_relationships_are_backed_by_what_uniprot_states():
    card = _card("P52270")
    (rel,) = card.relationships(object_ref="pdb:3Q37")
    (sa_id,) = rel["source_assertion_ids"]
    assertion = card.source_assertion_store.get(sa_id)
    assert assertion["field_path"] == "relationships.has_structure"
    assert assertion["subject_ref"] == "uniprot:P52270"
    assert assertion["asserted_value"]["chains"] == (
        "A/B/C/D=3-18, A/B/C/D=44-100, A/B/C/D=123-251"
    )


# Step 4b: RCSB polymer-entity mapping as a second, agreeing source (A9, A10)


def _json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _card_with_rcsb(accession, pdb_ids):
    entry = _json(f"temp_data/{accession}.json")
    mappings = [map_protein(entry, "2026-02-01")] + [
        map_structure_entities(
            _json(f"temp_data/rcsb/{pdb_id}.json"),
            "2026-02-01",
            subjects={accession},
            reference_lengths={accession: entry["sequence"]["length"]},
        )
        for pdb_id in pdb_ids
    ]
    return build_card_from_mapping(
        merge_mapping_results(mappings), meta={"entity_type": "protein"}
    )


def test_method_vocabulary_is_normalized():
    assert normalize_methods(["X-RAY DIFFRACTION"]) == "X-ray"
    assert normalize_methods(["X-RAY DIFFRACTION", "NEUTRON DIFFRACTION"]) == (
        "Neutron+X-ray"
    )
    assert normalize_methods([]) is None


def test_a9_rcsb_reveals_the_complex_and_ligands_behind_human_tim_structures():
    card = _card_with_rcsb("P60174", ["1HTI", "1KLG"])
    assert {r["subject_ref"] for r in card.relationships()} == {"uniprot:P60174"}

    view = card.structures(include_fragments=True)
    klg = _item(view, "pdb:1KLG")
    assert klg["sources"] == ["RCSB PDB", "UniProt"]
    assert klg["coverage_class"] == "fragment_or_peptide"
    assert sorted(
        uniprot for o in klg["other_entities"] for uniprot in o["uniprot"]
    ) == [
        "P01903",
        "P01911",
        "P0A0L5",
    ]
    hti = _item(view, "pdb:1HTI")
    assert [lig["comp_id"] for lig in hti["ligands"]] == ["PGA"]
    # 2-phosphoglycolate is what 1HTI studies (flag assigned by RCSB for this entry).
    assert hti["ligands"][0]["subject_of_investigation"] is True
    assert hti["other_entities"] == []


def test_a10_uniprot_and_rcsb_agree_on_tcruzi_tim_1tcd():
    card = _card_with_rcsb("P52270", ["1TCD"])
    (rel,) = card.relationships(object_ref="pdb:1TCD")
    sources = [
        card.source_assertion_store.get(sa)["source"]["name"]
        for sa in rel["source_assertion_ids"]
    ]
    assert sources == ["UniProt", "RCSB PDB"]
    assert "qualifier_conflicts" not in rel
    q = rel["qualifiers"]
    assert (q["method"], q["chains"], q["ranges"], q["coverage"]) == (
        "X-ray",
        ["A", "B"],
        [[3, 251]],
        0.992,
    )
    rcsb_sa = card.source_assertion_store.get(rel["source_assertion_ids"][1])
    assert (
        rcsb_sa["subject_ref"] == "pdb:1TCD"
    )  # structure facts keep their own subject


def test_disagreeing_sources_stay_visible_as_qualifier_conflicts():
    entry = _json("temp_data/rcsb/1TCD.json")
    region = entry["polymer_entities"][0]["rcsb_polymer_entity_align"][0][
        "aligned_regions"
    ][0]
    region["ref_beg_seq_id"] = 5  # pretend RCSB aligned 5-253 instead of 3-251
    card = build_card_from_mapping(
        merge_mapping_results(
            [
                map_protein(_json("temp_data/P52270.json"), "2026-02-01"),
                map_structure_entities(entry, "2026-02-01", subjects={"P52270"}),
            ]
        ),
        meta={"entity_type": "protein"},
    )
    (rel,) = card.relationships(object_ref="pdb:1TCD")
    assert rel["qualifier_conflicts"]["ranges"] == [[[3, 251]], [[5, 253]]]
