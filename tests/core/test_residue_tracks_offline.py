"""Recovered residue scenarios use original support and explicit sequence scope."""

import copy
import hashlib
import json

import ackredit
import pytest

from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, SchemaError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.aaindex import map_index, parse_index
from sabueso.mappings.disprot import map_disorder_regions
from sabueso.tools.db.disprot import FixtureDisProtClient, get_records


def protein(sequence="MST", accession="P60174"):
    assertion = make_source_assertion(
        "sequence.primary", sequence, "UniProt", accession, "2026-01-01"
    )
    return Card(
        meta={
            "entity_type": "protein",
            "card_id": f"sabueso:protein:uniprot:{accession}",
        },
        sections={
            "identifiers": {
                "uniprot": {"value": accession, "source_assertion_ids": []}
            },
            "sequence": {
                "primary": {
                    "value": sequence,
                    "source_assertion_ids": [assertion["id"]],
                }
            },
        },
        source_assertion_store=[assertion],
    )


def track(
    provider="Provider A", sequence_id="UniProt:P60174", sequence="MST", values=None
):
    value = {
        "sequence_id": sequence_id,
        "indexing": "1-based",
        "metric": "probability",
        "state_definition": "source-defined partial-unfolding state",
        "values": [0.0, 0.7, None] if values is None else values,
    }
    assertion = make_source_assertion(
        "sequence.residue_tracks.partial_unfolding",
        value,
        provider,
        "track-1",
        "2020-01-01",
        subject_ref="uniprot:P60174",
    )
    assertion["source"]["version"] = "original-v1"
    assertion["source_metadata"] = {
        "sequence": {
            "id": sequence_id,
            "value": sequence,
            "uniprot_ref": "uniprot:P60174",
            "sha256": hashlib.sha256(sequence.encode()).hexdigest(),
        },
        "publication": "native pointer",
    }
    return assertion


def type_statistic(context):
    return make_source_assertion(
        "amino_acid.statistics.partial_unfolded_frequency",
        {
            "amino_acid": "S",
            "value": 0.08,
            "statistic": "relative_frequency",
            "positional_context": context,
            "reference_population": "dataset A",
        },
        "Provider C",
        context,
        "2020-01-01",
        subject_ref="amino_acid:S",
    )


def test_type_statistics_and_provider_tracks_stay_independent():
    first, second = track(), track("Provider B")
    second["asserted_value"].update(
        metric="occupancy_frequency",
        state_definition="different experimental state",
        observations=[{"position": 2, "value": 0.5}],
    )
    del second["asserted_value"]["values"]
    assertions = [type_statistic("internal"), type_statistic("terminal"), first, second]
    card = protein()
    before, inputs_before = card.to_dict(), copy.deepcopy(assertions)
    with ackredit.session("residue view"):
        with ackredit.capture("reader") as workflow:
            view = card.residue_knowledge(2, source_assertions=assertions)
    assert workflow.attribution.to_dict()["uses"] == []
    assert view["rule"] == "residue_knowledge@1" and view["amino_acid"] == "S"
    assert len(view["amino_acid_type_statistics"]) == 2
    assert [
        (item["support"]["assertion"]["source"]["name"], item["value"]["value"])
        for item in view["residue_tracks"]
    ] == [("Provider A", 0.7), ("Provider B", 0.5)]
    assert {i["value"]["metric"] for i in view["residue_tracks"]} == {
        "probability",
        "occupancy_frequency",
    }
    for item in view["residue_tracks"]:
        assert item["support"]["snapshot_id"] == digest(
            canonical_json(item["support"]["assertion"])
        )
    view["residue_tracks"][0]["support"]["assertion"]["source"]["version"] = "changed"
    view["sequence_support"]["source_assertion_ids"].clear()
    assert card.to_dict() == before and assertions == inputs_before


def test_zero_and_missing_dense_or_sparse_samples_are_distinct():
    card, assertion = protein(), track()
    assert (
        card.residue_knowledge(1, source_assertions=[assertion])["residue_tracks"][0][
            "value"
        ]["value"]
        == 0
    )
    view = card.residue_knowledge(3, source_assertions=[assertion])
    assert view["residue_tracks"] == [] and len(view["missing_values"]) == 1
    assertion["asserted_value"].pop("values")
    assertion["asserted_value"]["observations"] = [
        {"position": 2, "value": 0.0, "sample_context": "source-stated condition"}
    ]
    assert (
        card.residue_knowledge(2, source_assertions=[assertion])["residue_tracks"][0][
            "value"
        ]["value"]
        == 0
    )
    assert (
        len(card.residue_knowledge(1, source_assertions=[assertion])["missing_values"])
        == 1
    )
    observed = card.residue_knowledge(2, source_assertions=[assertion])[
        "residue_tracks"
    ][0]
    assert (
        observed["value"]["native_observation"]["sample_context"]
        == "source-stated condition"
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda a: a.update(subject_ref="uniprot:P99999"),
        lambda a: a["source_metadata"]["sequence"].update(id="UniProt:P60174-2"),
        lambda a: a["source_metadata"]["sequence"].update(value="MAT"),
        lambda a: a["source_metadata"]["sequence"].update(sha256="0" * 64),
        lambda a: a.pop("source_metadata"),
        lambda a: a["asserted_value"].update(indexing="0-based"),
        lambda a: a["asserted_value"].update(values=[0.1]),
        lambda a: a["asserted_value"].update(values=[0, True, 0.5]),
        lambda a: a["asserted_value"].update(values=[0, 1.1, None]),
        lambda a: a["asserted_value"].update(observations=[]),
    ],
)
def test_incompatible_or_malformed_tracks_are_reported_unmapped(change):
    assertion = track()
    change(assertion)
    view = protein().residue_knowledge(2, source_assertions=[assertion])
    assert not view["residue_tracks"] and len(view["unmapped"]) == 1
    assert view["unmapped"][0]["support"]["assertion"] == assertion


@pytest.mark.parametrize("position", [True, 0, -1, 1.5, "2"])
def test_public_position_contract(position):
    with pytest.raises(ArgumentError):
        protein().residue_knowledge(position)


@pytest.mark.parametrize(
    "options",
    [
        {"sequence_ref": ""},
        {"sequence_ref": "isoform-2"},
        {"source_assertions": {}},
        {"source_assertions": [None]},
    ],
)
def test_public_input_contract(options):
    with pytest.raises(ArgumentError):
        protein().residue_knowledge(2, **options)


def test_explicit_isoform_sequence_is_read_without_canonical_projection():
    assertion = track(
        sequence_id="UniProt:P60174-2", sequence="MAT", values=[0.2, 0.3, 0.4]
    )
    card = protein()
    view = card.residue_knowledge(
        2, sequence_ref="UniProt:P60174-2", source_assertions=[assertion]
    )
    assert (
        view["amino_acid"] == "A"
        and view["sequence_basis"] == "source_sequence_declaration"
    )
    assert view["stored_annotations"] is None
    assert view["residue_tracks"][0]["value"]["value"] == 0.3
    assert not card.residue_knowledge(2, source_assertions=[assertion])[
        "residue_tracks"
    ]
    with pytest.raises(SchemaError, match="no valid"):
        card.residue_knowledge(2, sequence_ref="UniProt:P60174-2")
    with pytest.raises(IndexError):
        card.residue_knowledge(
            4, sequence_ref="UniProt:P60174-2", source_assertions=[assertion]
        )
    contradictory = track(sequence_id="UniProt:P60174-2", sequence="MST")
    with pytest.raises(SchemaError, match="contradictory"):
        card.residue_knowledge(
            2,
            sequence_ref="UniProt:P60174-2",
            source_assertions=[assertion, contradictory],
        )


@pytest.mark.local_source_inputs
def test_native_disprot_sequence_is_kept_separate_even_when_strings_match():
    envelope = get_records("P37840", client=FixtureDisProtClient())
    assertions = map_disorder_regions(envelope)
    card = protein(envelope["record"]["data"][0]["sequence"], "P37840")
    canonical = card.residue_knowledge(1, source_assertions=assertions)
    assert not canonical["source_annotations"] and len(canonical["unmapped"]) == len(
        assertions
    )
    position = assertions[0]["asserted_value"]["location"]["sequence"]["start"]
    source = card.residue_knowledge(
        position, sequence_ref="DisProt:DP00070", source_assertions=assertions
    )
    assert source["source_annotations"] and not source["unmapped"]
    metadata = source["source_annotations"][0]["support"]["assertion"][
        "source_metadata"
    ]
    assert metadata["regions_returned"] == 22 and metadata["regions_stated"] == 40
    assert metadata["native_region"]["reference_id"]


def test_aaindex_native_literals_and_missing_values_remain_type_references():
    text = """H TEST000001
D Synthetic test scale
I    A/L R/K N/M D/F C/P Q/S E/T G/W H/Y I/V
    1 2 3 4 5 6 7 8 9 10
    11 12 13 14 15 0 17 18 19 NA
//
"""
    assertions = map_index(
        {
            "record": parse_index(text, "TEST000001"),
            "retrieved_at": None,
            "version": None,
        }
    )
    view = protein().residue_knowledge(2, source_assertions=assertions)
    item = view["amino_acid_type_properties"][0]
    assert item["value"]["native_value"] == "0" and item["value_status"] == "stated"
    assert not view["residue_tracks"]
    missing = protein("MV").residue_knowledge(2, source_assertions=assertions)[
        "amino_acid_type_properties"
    ][0]
    assert (
        missing["value"]["native_value"] == "NA"
        and missing["value_status"] == "not_stated"
    )


def test_saved_reader_preserves_versions_units_and_input_pins(tmp_path):
    card = protein()
    assertion = track(
        values=[{"value": 0.0, "unit": "nm"}, None, {"value": 2.0, "unit": "nm"}]
    )
    assertion["asserted_value"]["metric"] = "source_stated_length"
    another_revision = copy.deepcopy(assertion)
    another_revision["source"]["version"] = "original-v2"
    assertions = [assertion, another_revision]
    view = card.residue_knowledge(1, source_assertions=assertions)
    assert len(view["residue_tracks"]) == 2
    assert len({item["support"]["snapshot_id"] for item in view["residue_tracks"]}) == 2
    assert view["residue_tracks"][0]["value"]["value"] == {"value": 0.0, "unit": "nm"}
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps(assertions))
    reader = Card.from_dict(card.to_dict())
    assert (
        reader.residue_knowledge(1, source_assertions=json.loads(path.read_text()))
        == view
    )
    card.set("sequence.primary", "MAT", [])
    assert reader.residue_knowledge(1, source_assertions=assertions) == view
    assert not card.residue_knowledge(1, source_assertions=assertions)["residue_tracks"]


def test_incomplete_assertions_are_refused_before_projection():
    with pytest.raises(SchemaError):
        protein().residue_knowledge(
            2, source_assertions=[{"field_path": "sequence.residue_tracks.x"}]
        )
    assertion = track(values=[float("nan"), 0.5, None])
    with pytest.raises(SchemaError, match="finite JSON"):
        protein().residue_knowledge(2, source_assertions=[assertion])


@pytest.mark.parametrize(
    "observations",
    [
        [{"position": True, "value": 0.5}],
        [{"position": 4, "value": 0.5}],
        [{"position": 2, "value": 0.5}, {"position": 2, "value": 0.7}],
        [{"position": 2}],
    ],
)
def test_sparse_tracks_refuse_ambiguous_or_invalid_positions(observations):
    assertion = track()
    assertion["asserted_value"].pop("values")
    assertion["asserted_value"]["observations"] = observations
    view = protein().residue_knowledge(2, source_assertions=[assertion])
    assert not view["residue_tracks"] and len(view["unmapped"]) == 1


def test_unrelated_type_reference_and_unsupported_field_remain_visible():
    assertion = type_statistic("internal")
    assertion["subject_ref"] = "uniprot:P60174"
    unsupported = track()
    unsupported["field_path"] = "another.source_field"
    view = protein().residue_knowledge(2, source_assertions=[assertion, unsupported])
    assert not view["amino_acid_type_statistics"]
    assert {item["reason"] for item in view["unmapped"]} == {
        "type reference subject differs",
        "unsupported assertion field",
    }
