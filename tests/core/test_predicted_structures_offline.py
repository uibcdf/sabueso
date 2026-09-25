"""Predicted structures from AlphaFold DB, apart from experimental ones (#57).

Fixtures are AlphaFold DB API responses for TcTIM (P52270) and HsTIM (P60174), model
version 6, retrieved on 2026-09-25.
"""

import json
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.alphafold import FixtureAlphaFoldClient, get_prediction


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _card(resolver, client, accession="P52270"):
    card, _ = sabueso.resolve(
        accession, resolver=resolver, predicted_structures=True, alphafold_client=client
    )
    return card


def test_a_model_is_a_predicted_structure_with_its_confidence(resolver):
    card = _card(resolver, FixtureAlphaFoldClient("temp_data"))
    (model,) = card.predicted_structures()["items"]
    assert model["model_ref"] == "alphafold:AF-P52270-F1"
    assert model["model_version"] == 6
    assert model["mean_plddt"] == pytest.approx(97.31)
    assert model["coverage"] == 1.0 and model["sequence_matches"] is True
    (rel,) = card.relationships("has_predicted_structure")
    (sa_id,) = rel["source_assertion_ids"]
    assert card.source_assertion_store.get(sa_id)["source"] == {
        "type": "database",
        "name": "AlphaFold DB",
        "record_id": "AF-P52270-F1",
        "version": "6",
    }
    again = Card.from_dict(json.loads(json.dumps(card.to_dict())))
    assert again.predicted_structures() == card.predicted_structures()


def test_models_never_count_as_experimental_structures(resolver):
    plain, _ = sabueso.resolve("P52270", resolver=resolver)
    card = _card(resolver, FixtureAlphaFoldClient("temp_data"))
    assert card.structures() == plain.structures()
    assert not [
        r for r in card.relationships("has_structure") if "alphafold" in r["object_ref"]
    ]


def test_a_model_of_another_sequence_is_flagged(resolver, tmp_path):
    (tmp_path / "alphafold").mkdir()
    models = json.loads(Path("temp_data/alphafold/P52270.json").read_text("utf-8"))
    models[0]["sequenceChecksum"] = "0" * 32  # constructed: an older sequence version
    (tmp_path / "alphafold" / "P52270.json").write_text(json.dumps(models), "utf-8")
    card = _card(resolver, FixtureAlphaFoldClient(tmp_path))
    assert card.predicted_structures()["items"][0]["sequence_matches"] is False


def test_absent_and_failed_models_are_states(resolver, tmp_path):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    def state(card):
        (row,) = [
            r
            for r in card.knowledge_state()["rows"]
            if r["area"] == "relationships.has_predicted_structure"
        ]
        return row["state"]

    absent = _card(resolver, FixtureAlphaFoldClient(tmp_path))
    assert absent.predicted_structures() == {"items": []}
    assert state(absent) == "not_stated"
    with pytest.warns(EnrichmentFailedWarning):
        failed = _card(
            resolver, FixtureAlphaFoldClient("temp_data", failing={"P52270"})
        )
    assert state(failed) == "unavailable"
    plain, _ = sabueso.resolve("P52270", resolver=resolver)
    assert state(plain) == "not_queried"


def test_source_access_returns_the_raw_models():
    record = get_prediction("P60174", client=FixtureAlphaFoldClient("temp_data"))
    assert (record["source"], record["kind"], record["version"]) == (
        "AlphaFold DB",
        "prediction",
        "v6",
    )
    assert record["record"][0]["entryId"] == "AF-P60174-F1"


def test_the_table_is_flat(resolver):
    card = _card(resolver, FixtureAlphaFoldClient("temp_data"))
    (row,) = card.table("predicted_structures")
    assert row["range"] == "1-251" and row["fraction_very_high"] == pytest.approx(0.952)
