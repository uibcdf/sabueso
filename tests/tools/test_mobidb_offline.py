"""Native MobiDB v1 exports preserve identity, annotation basis and source axes."""

import copy
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.card import Card
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.mobidb import (
    map_disorder_regions,
    map_modified_residues,
    validate_export,
)
from sabueso.tools.db.mobidb import FixtureMobiDBClient, get_annotations

ROOT = Path("temp_data/mobidb")


def native(identifier="P60174"):
    return json.loads((ROOT / f"annotations__{identifier}.json").read_text())


class Client:
    def __init__(self, payload):
        self.payload = payload

    def annotations(self, identifier):
        return {
            "record": self.payload,
            "version": "7.0" if self.payload else None,
            "retrieved_at": "2026-01-01",
            "response_headers": {
                "x-page-limit": "1",
                "x-returned-count": str(len(self.payload)),
            },
        }


class Response(io.BytesIO):
    status = 200

    def __init__(self, raw):
        super().__init__(raw)
        self.headers = Message()
        for key, value in {
            "Content-Type": "application/json",
            "X-Page-Limit": "1",
            "X-Returned-Count": "1",
        }.items():
            self.headers[key] = value


@pytest.mark.parametrize(
    "identifier,disorder,modified", [("P60174", 30, 19), ("P37840", 43, 4)]
)
def test_full_native_exports_keep_source_scope_and_detached_assertions(
    identifier, disorder, modified
):
    envelope = get_annotations(identifier, client=FixtureMobiDBClient())
    before = copy.deepcopy(envelope)
    assertions = map_disorder_regions(envelope)
    ptms = map_modified_residues(envelope)
    assert len(assertions) == disorder and len(ptms) == modified
    assert envelope == before and envelope["truncated"] is False
    assert (
        envelope["version"] == "7.0"
        and envelope["record"][0]["release"]["api_version"] == "v1"
    )
    for assertion in assertions + ptms:
        assert assertion["subject_ref"] == "uniprot:" + identifier
        assert (
            assertion["asserted_value"]["location"]["sequence"]["sequence_id"]
            == "MobiDB:" + identifier
        )
        assert (
            assertion["source_metadata"]["native_release"]["release_date"] == "2026_07"
        )
        assert "term_id" not in assertion["asserted_value"]
    (access,) = envelope["acquisition_trace"]["records"]
    assert access["source"] == "MobiDB" and access["access"] == "supplied_file"
    assert access["outcome"] == "received" and access["network_attempts"] == 0
    assert access["retrieved_at"] is None and access["source_version"]["value"] == "7.0"
    assert access["provider"]["status"] == "available"
    assertions[0]["source_metadata"]["native_annotation_set"]["regions"].clear()
    assert envelope == before


def test_native_curated_support_and_unknown_ptm_basis_stay_distinct():
    envelope = get_annotations("P37840", client=FixtureMobiDBClient())
    annotations = map_disorder_regions(envelope)
    assert {a["asserted_value"]["provider_basis"] for a in annotations} == {
        "curated",
        "prediction",
    }
    disprot = next(
        a for a in annotations if a["asserted_value"]["provider_source"] == "disprot"
    )
    assert (
        disprot["source_metadata"]["native_annotation_set"]["provenance"]["source_id"]
        == "DP00070"
    )
    ptms = map_modified_residues(envelope)
    assert [a["asserted_value"]["description"] for a in ptms] == [
        "N-acetylmethionine",
        "Phosphoserine",
        "Phosphotyrosine; by FYN",
        "Phosphoserine; by GRK2, PLK2, CK2, CK1 and GRK5",
    ]
    assert all(a["asserted_value"]["provider_basis"] is None for a in ptms)
    assert (
        "Original evidence was not retained"
        in ptms[0]["source_metadata"]["native_annotation_set"]["definition"]
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.append(copy.deepcopy(p[0])),
        lambda p: p[0].update(accession="P37840"),
        lambda p: p[0].update(sequence=None),
        lambda p: p[0].update(length=True),
        lambda p: p[0].update(length=248),
        lambda p: p[0].update(coordinate_system="0-based"),
        lambda p: p[0]["release"].update(api_version="v2"),
        lambda p: p[0]["release"].update(mobidb_version=None),
        lambda p: p[0]["release"].update(release_date="2026_13"),
        lambda p: p[0].update(issues=[{}]),
        lambda p: p[0]["annotation_sets"].append(
            copy.deepcopy(p[0]["annotation_sets"][0])
        ),
        lambda p: p[0]["annotation_sets"][0].update(annotation_id=None),
        lambda p: p[0]["annotation_sets"][0].update(kind=[]),
        lambda p: p[0]["annotation_sets"][0].update(evidence=[]),
        lambda p: p[0]["annotation_sets"][0].update(evidence="full"),
        lambda p: p[0]["annotation_sets"][0].update(regions=[{"start": 0, "end": 1}]),
        lambda p: p[0]["annotation_sets"][0].update(regions=[{"start": 1, "end": 250}]),
        lambda p: p[0]["annotation_sets"][0].update(
            regions=[{"start": 1, "end": True}]
        ),
        lambda p: p[0]["annotation_sets"][0].update(regions=[{"start": 1, "end": 1.0}]),
        lambda p: p[0]["annotation_sets"][0].update(regions="missing"),
        lambda p: p[0]["annotation_sets"][0].update(
            residue_series=[
                {"start": 1, "step": 1, "values": [0], "missing_value": None}
            ]
        ),
        lambda p: p[0].update(length=float("inf")),
    ],
)
def test_malformed_unrelated_or_inconsistent_exports_are_refused(change):
    payload = native()
    change(payload)
    with pytest.raises(ConnectorError):
        validate_export(payload, "P60174")


def test_homology_is_not_curated_and_mixed_basis_is_not_guessed():
    payload = native()
    annotation = next(
        a
        for a in payload[0]["annotation_sets"]
        if a.get("feature") == "disorder" and a.get("regions")
    )
    annotation["evidence"] = "homology"
    result = get_annotations("P60174", client=Client(payload))
    mapped = next(
        a
        for a in map_disorder_regions(result)
        if a["asserted_value"]["annotation_id"] == annotation["annotation_id"]
    )
    assert mapped["asserted_value"]["provider_basis"] == "homology"
    del annotation["evidence"]
    result = get_annotations("P60174", client=Client(payload))
    assert any(
        a["asserted_value"]["provider_basis"] is None
        for a in map_disorder_regions(result)
    )


def test_reported_normalization_loss_is_retained_but_set_is_not_mapped():
    payload = native()
    annotation = next(
        a
        for a in payload[0]["annotation_sets"]
        if a.get("feature") == "disorder" and a.get("regions")
    )
    affected = annotation["annotation_id"]
    payload[0]["issues"].append(
        {"annotation_id": affected, "field": "regions", "code": "INVALID_REGION"}
    )
    result = get_annotations("P60174", client=Client(payload))
    assert result["record"][0]["issues"] == payload[0]["issues"]
    assert all(
        a["asserted_value"]["annotation_id"] != affected
        for a in map_disorder_regions(result)
    )
    assert (
        result["truncated"] is False
    )  # complete export; representation loss is separate


def test_zero_coverage_without_intervals_never_becomes_a_positive_region():
    result = get_annotations("P60174", client=FixtureMobiDBClient())
    alphafold = next(
        a
        for a in result["record"][0]["annotation_sets"]
        if a["annotation_id"] == "prediction-disorder-alphafold"
    )
    assert alphafold["coverage"]["fraction"] == 0 and "regions" not in alphafold
    assert (
        alphafold["residue_series"][0]["quantity"]
        == "smoothed_relative_solvent_accessibility"
    )
    assert "not 1 minus pLDDT" in alphafold["residue_series"][0]["definition"]
    assert not any(
        a["asserted_value"]["annotation_id"] == alphafold["annotation_id"]
        for a in map_disorder_regions(result)
    )


@pytest.mark.parametrize("identifier", ["P60174-3", "P60174/evil", "", None])
def test_invalid_identifiers_are_rejected_before_client_access(identifier):
    class Forbidden:
        def annotations(self, identifier):
            raise AssertionError(
                "Invalid identity must be rejected before source access"
            )

    with pytest.raises(Exception) as caught:
        get_annotations(identifier, client=Forbidden())
    assert not isinstance(caught.value, AssertionError)


@pytest.mark.parametrize(
    "headers",
    [
        {"x-page-limit": "1", "x-returned-count": "1", "x-next-cursor": "next"},
        {"x-page-limit": "2", "x-returned-count": "1"},
        {"x-page-limit": "1", "x-returned-count": "0"},
        {"x-page-limit": "1", "x-returned-count": True},
        {},
    ],
)
def test_unconsumed_pages_or_changed_counts_cannot_claim_complete_export(headers):
    client = Client(native())
    original = client.annotations
    client.annotations = lambda identifier: {
        **original(identifier),
        "response_headers": headers,
    }
    with pytest.raises(ConnectorError):
        get_annotations("P60174", client=client)


def test_empty_export_and_unavailable_fixture_are_distinct(tmp_path):
    empty = get_annotations("P60174", client=Client([]))
    assert empty["version"] is None and map_disorder_regions(empty) == []
    with pytest.raises(ConnectorError) as missing:
        get_annotations("P60174", client=FixtureMobiDBClient(tmp_path))
    assert missing.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize(
    "body,exception,outcome",
    [
        (
            {
                "error": {
                    "code": "PROTEIN_NOT_FOUND",
                    "message": "Protein not found",
                    "parameter": "acc",
                }
            },
            RecordNotFoundError,
            "not_found",
        ),
        (
            {"error": {"code": "ROUTE_NOT_FOUND", "message": "Route missing"}},
            ConnectorError,
            "failed",
        ),
        ({"error": []}, ConnectorError, "failed"),
    ],
)
def test_only_native_unknown_protein_response_is_not_found(
    monkeypatch, body, exception, outcome
):
    from sabueso.tools.db import _http

    def failed(request, timeout):
        raise HTTPError(
            request.full_url,
            404,
            "not found",
            Message(),
            io.BytesIO(json.dumps(body).encode()),
        )

    monkeypatch.setattr(_http, "_urlopen", failed)
    with pytest.raises(exception) as caught:
        get_annotations("P60174")
    assert caught.value.acquisition_trace["records"][0]["outcome"] == outcome


def test_online_export_records_and_replays_original_time_headers_and_mapping(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    def download(request, timeout):
        calls.append(request.full_url)
        return Response((ROOT / "annotations__P60174.json").read_bytes())

    monkeypatch.setattr(_http, "_urlopen", download)
    archive = RetrievalArchive(tmp_path / "mobidb.db")
    with archive.recording():
        original = get_annotations("P60174")

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay must not access the network")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replayed = get_annotations("P60174")
    assert calls == ["https://mobidb.org/api/v1/protein/P60174/export?format=json"]
    assert original["record"] == replayed["record"]
    assert original["retrieved_at"] == replayed["retrieved_at"]
    assert map_disorder_regions(original) == map_disorder_regions(replayed)
    assert original["acquisition_trace"]["records"][0]["network_attempts"] == 1
    assert replayed["acquisition_trace"]["records"][0]["access"] == "replay"


def test_residue_reader_requires_explicit_mobidb_axis_without_fabricated_ontology_id():
    result = get_annotations("P60174", client=FixtureMobiDBClient())
    assertions = map_disorder_regions(result)
    sequence = result["record"][0]["sequence"]
    native_sequence = make_source_assertion(
        "sequence.primary", sequence, "UniProt", "P60174", None
    )
    card = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:P60174"},
        sections={
            "identifiers": {"uniprot": {"value": "P60174", "source_assertion_ids": []}},
            "sequence": {
                "primary": {
                    "value": sequence,
                    "source_assertion_ids": [native_sequence["id"]],
                }
            },
        },
        source_assertion_store=[native_sequence],
    )
    before = card.to_dict()
    canonical = card.residue_knowledge(1, source_assertions=assertions)
    assert canonical["source_annotations"] == [] and canonical["unmapped"]
    native_view = card.residue_knowledge(
        1, sequence_ref="MobiDB:P60174", source_assertions=assertions
    )
    assert (
        native_view["source_annotations"]
        and native_view["rule"] == "residue_knowledge@1"
    )
    assert card.to_dict() == before
    for assertion in assertions:
        assertion["asserted_value"]["feature"] = "unknown"
    rejected = card.residue_knowledge(
        1, sequence_ref="MobiDB:P60174", source_assertions=assertions
    )
    assert rejected["source_annotations"] == [] and rejected["unmapped"]
