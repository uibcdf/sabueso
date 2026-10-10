"""Original comparative rules retain exact support, scope and missing inputs."""

from copy import deepcopy

import ackredit
import argdigest
import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.core.tissue_usage import (
    EXONS,
    ISOFORMS,
    REGIONS,
    TERMS,
    TISSUE_TEXT,
    TRANSCRIPTS,
    VARIANTS,
)
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.gnomad import FixtureGnomADClient
from sabueso.tools.db.gtex import FixtureGTExClient
from sabueso.tools.db.uniref import FixtureUniRefClient


def synthetic():
    return Card(
        meta={"card_id": "sabueso:protein:uniprot:P60174", "entity_type": "protein"}
    )


def stated(card, path, value, *, aggregate=False):
    rows = value if isinstance(value, list) and not aggregate else [value]
    ids = []
    for i, row in enumerate(rows):
        assertion = make_source_assertion(
            path, row, "synthetic", str(i), "original time"
        )
        assertion["source"]["version"] = "original version"
        card.source_assertion_store.add(assertion)
        ids.append(assertion["id"])
    card.set(path, value, ids)
    return ids


@pytest.fixture(scope="module")
def public_cards():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    return {
        accession: sabueso.resolve(accession, resolver=resolver, **options)[0]
        for accession, options in (
            (
                "P52270",
                {"uniref": True, "uniref_client": FixtureUniRefClient("temp_data")},
            ),
            ("Q4DV43", {}),
            (
                "P60174",
                {
                    "gnomad": {},
                    "exon_usage": True,
                    "gtex": True,
                    "gnomad_client": FixtureGnomADClient("temp_data"),
                    "gtex_client": FixtureGTExClient("temp_data"),
                },
            ),
        )
    }


def test_public_explanations_preserve_existing_views_and_never_acquire_or_credit(
    public_cards, monkeypatch
):
    from sabueso.tools.db import _http

    def forbidden(*a, **k):
        pytest.fail("explanation must be inert")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    human = public_cards["P60174"]
    before = {key: card.to_dict() for key, card in public_cards.items()}
    with ackredit.session("inert comparative explanations"):
        credit = ackredit.get_attribution().to_dict()
        sequence = public_cards["P52270"].explain_sequence_differences(
            public_cards["Q4DV43"]
        )
        variant = human.explain_variant_tissue_usage(0.2)
        isoform = human.explain_isoform_tissue_usage(0.2)
        assert ackredit.get_attribution().to_dict() == credit
    assert sequence["view"] == public_cards["P52270"].sequence_differences(
        public_cards["Q4DV43"]
    )
    assert sequence["rule"]["inputs"] == sequence["card_refs"]
    assert sequence["coordinate_scope"]["residue_correspondence"] == "not_established"
    assert any(
        row["relationship"]["predicate"] == "clustered_with"
        for row in sequence["context"][0]["relationships"]
    )
    assert variant["view"] == human.variant_tissue_usage(0.2)
    assert isoform["view"] == human.isoform_tissue_usage(0.2)
    assert variant["rule"]["parameters"]["threshold"] == 0.2
    assert isoform["rule"]["parameters"]["threshold"] == 0.2
    for result in (variant, isoform):
        assert result["card_ref"] == human.pinned_ref()
        assert result["context"]["execution_observation"]["status"] == "not_observed"
        assert result["tissue_terms"]["view"]["rule"]["rule"] == "gtex_tissue_key@1"
        join = next(
            row for row in result["tissue_terms"]["joins"] if row["tissue"] == "testis"
        )
        assert join["term_input"]["source_assertions"][0]["version"] == "gtex_v10"
        assert all(
            row["card_ref"] == human.pinned_ref() for row in join["pext_locators"]
        )
        field = next(f for f in result["fields"] if f["field_path"] == REGIONS)
        assert {r["version"] for r in field["source_assertions"]} == {
            "gnomad_r4 pext (GTEx v10)"
        }
        result["fields"].clear()
    assert {key: card.to_dict() for key, card in public_cards.items()} == before


@pytest.mark.parametrize(
    "sequence,basis",
    [(None, "sequence_not_stated"), ("AC", "different_lengths"), ("ACD", None)],
)
def test_sequence_missing_lengths_and_equal_positions_keep_both_pins(sequence, basis):
    left, right = synthetic(), synthetic()
    stated(left, "sequence.primary", "ACE")
    if sequence:
        stated(right, "sequence.primary", sequence)
    result = left.explain_sequence_differences(right)
    assert result["view"].get("basis") == basis
    assert result["card_refs"] == [left.pinned_ref(), right.pinned_ref()]
    if basis is None:
        assert result["view"]["differences"] == [
            {"position": 3, "residues": ["E", "D"]}
        ]
        assert result["status"] == "on_card"
    else:
        assert result["status"] == "partial"


def test_selected_and_alternative_sequences_conflicts_and_missing_support_remain_separate():
    left, right = synthetic(), synthetic()
    selected = stated(left, "sequence.primary", "ACE")
    other = make_source_assertion(
        "sequence.primary", "ACD", "synthetic", "other", "old"
    )
    left.source_assertion_store.add(other)
    left.quality["conflicts"] = [
        {"field": "sequence.primary", "source_assertion_ids": [selected, [other["id"]]]}
    ]
    left.quality["alternatives"] = [
        {
            "field": "sequence.primary",
            "source_assertion_ids": [[other["id"], "SA_missing"]],
        }
    ]
    stated(right, "sequence.primary", "ACE")
    result = left.explain_sequence_differences(right)
    assert result["view"]["identical"] is True
    field = result["fields"][0]
    assert [row["id"] for row in field["source_assertions"]] == selected
    assert [row["id"] for row in field["alternatives"]] == [other["id"]]
    assert field["conflicts"] == left.quality["conflicts"]
    assert field["selection_alternatives"] == left.quality["alternatives"]
    assert any(g["reason"] == "missing_source_assertion" for g in result["gaps"])


def region(start=10, end=20, **extra):
    return {
        "assembly": "GRCh38",
        "chromosome": "12",
        "start": start,
        "end": end,
        "tissues": [{"tissue": "testis", "value": 0.5}],
        **extra,
    }


def test_variant_join_uses_genomic_position_and_first_region_not_protein_position():
    card = synthetic()
    stated(card, REGIONS, [region(), region(mean=99)])
    stated(
        card,
        VARIANTS,
        [
            {
                "variant_id": "12-15-A-G",
                "location": {"start": 900, "end": 900},
                "not_placed": "synthetic",
            },
            {"variant_id": "12-30-A-G"},
            {"hgvs_p": "p.Ala3Thr"},
        ],
    )
    answer = card.explain_variant_tissue_usage()
    assert answer["view"]["counts"] == {
        "in_region": 1,
        "outside_pext_regions": 1,
        "no_position": 1,
    }
    first = answer["items"][0]
    assert first["region_input"]["locator"]["index"] == 0
    assert first["coordinate_scope"]["position"]["position"] == 15
    assert first["variant_input"]["value"]["location"]["start"] == 900
    assert {g["reason"] for g in answer["gaps"]} >= {
        "outside_pext_regions",
        "no_position",
        "tissue_term_not_stated",
    }


@pytest.mark.parametrize("aggregate", [False, True])
def test_row_support_never_invents_finer_assertion_membership(aggregate):
    card = synthetic()
    stated(card, REGIONS, [region()], aggregate=aggregate)
    stated(card, VARIANTS, [{"variant_id": "12-15-A-G"}])
    answer = card.explain_variant_tissue_usage()
    record = answer["items"][0]["region_input"]
    assert record["support_basis"] == (
        "selected_field_list" if aggregate else "exact_asserted_value"
    )
    assert record["mapping_lineage"] == "not_reconstructed"


def test_tissue_term_collision_preserves_candidates_and_actual_last_selection():
    card = synthetic()
    stated(card, REGIONS, [region()])
    stated(card, VARIANTS, [{"variant_id": "12-15-A-G"}])
    stated(
        card,
        TERMS,
        [
            {"gtex_id": "Testis", "ontology_id": "one"},
            {"gtex_id": "TESTIS", "ontology_id": "two"},
        ],
    )
    answer = card.explain_variant_tissue_usage()
    join = answer["tissue_terms"]["joins"][0]
    assert join["term_input"]["value"]["ontology_id"] == "two"
    assert join["other_matching_terms"][0]["value"]["ontology_id"] == "one"
    assert any(g["reason"] == "multiple_matching_tissue_terms" for g in answer["gaps"])


def iso_card():
    card = synthetic()
    stated(
        card,
        ISOFORMS,
        [{"isoform_id": "X-1", "name": "1"}, {"isoform_id": "X-2", "name": "2"}],
    )
    stated(card, TRANSCRIPTS, [{"isoform": "X-1", "transcript": "T1"}])
    stated(
        card,
        EXONS,
        [
            {
                "isoform": "X-1",
                "transcript": "T1",
                "cds": [[10, 30]],
                "assembly": "GRCh38",
                "chromosome": "12",
            }
        ],
    )
    stated(card, REGIONS, [region()])
    return card


def test_isoform_explanation_records_actual_weighted_intersections_and_incomplete_own_bases():
    card = iso_card()
    answer = card.explain_isoform_tissue_usage()
    first = answer["items"][0]
    assert first["own_regions"] == [[10, 30]]
    assert first["pext_inputs"][0]["intersection"] == [10, 20]
    assert first["pext_inputs"][0]["bases"] == 11
    assert first["bases_without_pext"] == 10
    assert first["item"]["own_bases_complete"] is False
    assert answer["items"][1]["item"]["pext"]["basis"] == "no_transcript_stated"
    assert any(g["reason"] == "incomplete_isoform_exon_support" for g in answer["gaps"])
    assert answer["coordinate_scope"]["subtraction_inputs"] == {"X-1": [[10, 30]]}


def test_isoform_tissue_text_keeps_original_used_and_excluded_assertions():
    card = iso_card()
    for molecule in (None, "Isoform 1", "Isoform unknown"):
        assertion = make_source_assertion(
            TISSUE_TEXT, str(molecule), "UniProt", str(molecule), "original time"
        )
        assertion["source_metadata"] = {"molecule": molecule, "eco": ["ECO:0000269"]}
        card.source_assertion_store.add(assertion)
    answer = card.explain_isoform_tissue_usage()
    decisions = answer["tissue_specificity_decisions"]
    assert [r["basis"] for r in decisions] == [
        "entry_scope",
        "exact_isoform_name",
        "unknown_isoform_molecule",
    ]
    assert len(answer["entry_tissue_specificity"]) == 1
    assert len(answer["items"][0]["tissue_specificity"]) == 1
    assert decisions[2]["status"] == "excluded"
    field = next(row for row in answer["fields"] if row["field_path"] == TISSUE_TEXT)
    assert not field["stored"] and len(field["alternatives"]) == 3
    assert (
        decisions[2]["source_assertions"][0]["source_metadata"]["molecule"]
        == "Isoform unknown"
    )


@pytest.mark.parametrize("missing_transcripts", [False, True])
def test_missing_exons_and_old_transcript_inputs_retain_original_basis(
    missing_transcripts,
):
    card = iso_card()
    if missing_transcripts:
        card.sections["identifiers"].pop("ensembl_transcripts")
        expected = "transcripts_not_recorded"
    else:
        stated(card, TRANSCRIPTS, [{"isoform": "X-2", "transcript": "T2"}])
        expected = "transcript_not_in_gnomad"
    answer = card.explain_isoform_tissue_usage()
    assert answer["items"][1]["item"]["pext"]["basis"] == expected
    assert any(g["reason"] == expected for g in answer["gaps"])


def test_foreign_genomic_scopes_are_visible_without_silently_changing_historical_rule():
    card = iso_card()
    stated(card, REGIONS, [region(chromosome="1", assembly="GRCh37")])
    answer = card.explain_isoform_tissue_usage()
    assert answer["view"] == card.isoform_tissue_usage()
    assert any(g["reason"] == "genomic_scope_not_confirmed" for g in answer["gaps"])
    assert (
        answer["coordinate_scope"]["chromosome_matching"]
        == "not_checked_by_isoform_exon_usage@2"
    )


def test_overlapping_pext_regions_preserve_old_denominator_without_negative_missing_bases():
    card = iso_card()
    stated(card, REGIONS, [region(10, 30), region(10, 30, mean=1)])
    answer = card.explain_isoform_tissue_usage()
    assert answer["view"] == card.isoform_tissue_usage()
    assert answer["items"][0]["item"]["pext"]["bases_with_pext"] == 42
    assert answer["items"][0]["bases_without_pext"] == 0
    assert any(
        g["reason"] == "overlapping_pext_regions_counted_multiple_times"
        for g in answer["gaps"]
    )


@pytest.mark.parametrize(
    "method", ["explain_variant_tissue_usage", "explain_isoform_tissue_usage"]
)
@pytest.mark.parametrize(
    "invalid", [True, "0.1", None, -0.1, 1.1, float("nan"), float("inf"), [], {}]
)
def test_dimensionless_threshold_refuses_invalid_cutoffs(method, invalid):
    with pytest.raises(ArgumentError):
        getattr(synthetic(), method)(invalid)
    with pytest.raises(ArgumentError):
        getattr(synthetic(), method)(invalid, skip_digestion=True)


def test_public_argument_guards_and_missing_pins(public_cards):
    card = public_cards["P60174"]
    with pytest.raises(ArgumentError):
        card.explain_sequence_differences("P52270")
    with pytest.raises(argdigest.UnknownArgumentError):
        card.explain_variant_tissue_usage(extra=True)
    with pytest.raises(StorageError):
        Card().explain_isoform_tissue_usage()


def test_historical_pin_never_substitutes_newer_sequence_and_fields_are_detached(
    tmp_path,
):
    card, other = synthetic(), synthetic()
    stated(card, "sequence.primary", "ACE")
    stated(other, "sequence.primary", "ACD")
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    pin, other_pin = store.save(card), store.save(other)
    original = card.explain_sequence_differences(other)
    stated(card, "sequence.primary", "ACD")
    later = store.save(card)
    assert later != pin
    assert (
        store.load(pin).explain_sequence_differences(store.load(other_pin)) == original
    )
    assert (
        store.load(later).explain_sequence_differences(other)["view"]["identical"]
        is True
    )
    before = deepcopy(card.to_dict())
    original["fields"][0]["node"]["value"] = "forged"
    assert card.to_dict() == before
