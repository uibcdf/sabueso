"""has_structure relationships from UniProt and the ProteinCard structures view.

uibcdf/sabueso#6, step 4a: the UniProt side of acceptance cases A9 and A10.
"""

from sabueso.core.structures import coverage, coverage_class, merge_ranges
from sabueso.mappings.uniprot import _parse_pdb_chains
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
