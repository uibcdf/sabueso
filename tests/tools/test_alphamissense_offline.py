"""Native predictions, source identity, untouched literals and separate acquisition."""

import copy
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.mappings.alphamissense import decode_csv, map_variants
from sabueso.tools.db.alphamissense import (
    FixtureAlphaMissenseClient,
    OnlineAlphaMissenseClient,
    get_annotations,
)

ROOT = Path("temp_data/alphamissense")
HEADER = "protein_variant,am_pathogenicity,am_class\r\n"


def native_models():
    return json.loads((ROOT / "alphafold/P60174.json").read_text())


def descriptor():
    return native_models()[0]


class Discovery:
    def __init__(self, records=None):
        self.records = native_models() if records is None else records

    def prediction(self, identifier):
        return {"record": copy.deepcopy(self.records), "retrieved_at": "2020-01-01"}


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, content_type):
        super().__init__(data)
        self.headers = Message()
        self.headers["Content-Type"] = content_type


def test_native_complete_artifact_and_capped_source_assertions_keep_exact_scope():
    full = get_annotations("P60174", client=FixtureAlphaMissenseClient())
    artifact = full["record"]["artifact"]
    assert full["version"] is None and full["truncated"] is False
    assert artifact["total"] == len(artifact["rows"]) == 4731
    assert artifact["coverage"]["complete_grid"] is True
    assert (
        artifact["sha256"]
        == "d5831f6d4971e3440a51c665de67443ad79b8ff9910788e419a0899c963a8796"
    )
    assert len(full["record"]["discovery"]["record"]) == 3
    assert full["record"]["discovery"]["version"] == "v6"
    limited = get_annotations("p60174", limit=3, client=FixtureAlphaMissenseClient())
    assert limited["truncated"] is True
    before = copy.deepcopy(limited)
    assertions = map_variants(limited)
    assert limited == before and len(assertions) == 3
    first = assertions[0]
    assert first["asserted_value"]["knowledge_class"] == "predicted"
    assert first["asserted_value"]["provider_class"] == "LBen"
    assert "provider_class_recognized" not in first["asserted_value"]
    assert first["source_metadata"]["class_validation"]["recognized"] is True
    assert first["asserted_value"]["pathogenicity_score"] == 0.2415
    assert first["source_metadata"]["native_variant"]["am_pathogenicity"] == "0.2415"
    assert (
        first["source"]["version"] is None and first["subject_ref"] == "uniprot:P60174"
    )
    assert (
        first["asserted_value"]["location"]["sequence"]["sequence_id"]
        == "AlphaMissense:AF-P60174-F1"
    )
    assert first["source_metadata"]["sequence"]["id"] != "uniprot:P60174"
    assert first["acquisition"] == {"method": "database"}
    assert first["source_metadata"]["returned_subset"] is True
    accesses = limited["acquisition_trace"]["records"]
    assert [a["source"] for a in accesses] == ["AlphaFold DB", "AlphaMissense"]
    assert all(
        a["network_attempts"] == 0 and a["outcome"] == "received" for a in accesses
    )
    assert (
        accesses[1]["access"] == "supplied_file" and accesses[1]["retrieved_at"] is None
    )
    assert accesses[1]["source_version"]["value"] is None
    assert accesses[1]["response_identity"]["hash"] == "sha256:" + artifact["sha256"]
    assert accesses[1]["provider"]["status"] == "available"
    assert any(
        b.get("doi") == "10.1126/science.adg7492" for b in accesses[1]["bibliography"]
    )
    first["source_metadata"]["discovery_descriptor"]["sequence"] = "A"
    assert limited == before


@pytest.mark.parametrize(
    "tail",
    [
        "M1A,nan,LBen\n",
        "M1A,inf,LBen\n",
        "M1A,-0.1,LBen\n",
        "M1A,1.1,LBen\n",
        "M1A,bad,LBen\n",
        "M0A,0.2,LBen\n",
        "M250A,0.2,LBen\n",
        "A1C,0.2,LBen\n",
        "M1M,0.2,LBen\n",
        "M1*,0.2,LBen\n",
        "M01A,0.2,LBen\n",
        "M1ß,0.2,LBen\n",
        "M1A,0.2,LBen,extra\n",
        "M1A,0.2\n",
        'M1A,"unclosed\n',
    ],
)
def test_invalid_native_variants_scores_or_width_fail(tail):
    with pytest.raises(ConnectorError):
        decode_csv(HEADER + tail, descriptor())


@pytest.mark.parametrize(
    "header",
    [
        "",
        "protein_variant,am_class\n",
        "protein_variant,am_pathogenicity,am_class,am_class\n",
    ],
)
def test_missing_or_duplicate_headers_are_not_empty_source_answers(header):
    with pytest.raises(ConnectorError):
        decode_csv(header, descriptor())


def test_duplicate_variants_and_native_accession_disagreement_are_refused():
    with pytest.raises(ConnectorError, match="repeats"):
        decode_csv(HEADER + "M1A,0.2,LBen\nM1A,0.2,LBen\n", descriptor())
    with pytest.raises(ConnectorError, match="accession"):
        decode_csv("uniprot_id," + HEADER + "P60175,M1A,0.2,LBen\n", descriptor())


def test_zero_missing_and_future_classification_stay_distinct(tmp_path):
    base = tmp_path / "alphamissense"
    (base / "alphafold").mkdir(parents=True)
    (base / "alphafold/P60174.json").write_text(json.dumps(native_models()))
    (base / "AF-P60174-F1-aa-substitutions.csv").write_text(
        HEADER + "M1A,0,FutureState\nM1C,,\nM1D,NA,LPath\n"
    )
    result = get_annotations("P60174", client=FixtureAlphaMissenseClient(tmp_path))
    assertions = map_variants(result)
    values = [a["asserted_value"] for a in assertions]
    assert [v["pathogenicity_score"] for v in values] == [0.0, None, None]
    assert values[0]["provider_class"] == "FutureState"
    assert "provider_class_recognized" not in values[0]
    assert assertions[0]["source_metadata"]["class_validation"] == {
        "rule": "native_alphamissense_class_vocabulary@1",
        "recognized": False,
        "basis": "supported_native_AFDB_codes; provider_class_not_recomputed",
    }
    assert values[1]["provider_class"] is None
    assert values[2]["provider_class"] == "LPath"
    assert result["record"]["artifact"]["coverage"]["missing"] == 4728
    assert (
        result["truncated"] is False
    )  # all artifact rows read; grid gaps are separate


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update(amAnnotationsUrl="https://evil.example/variants.csv"),
        lambda d: d.update(
            amAnnotationsUrl="https://alphafold.ebi.ac.uk/files/AF-P60175-F1-aa-substitutions.csv"
        ),
        lambda d: d.update(entryId="AF-P60174-F2"),
        lambda d: d.update(taxId=9598),
        lambda d: d.update(taxId=9606.0),
        lambda d: d.update(isUniProt=False),
        lambda d: d.update(sequenceStart=True),
        lambda d: d.update(sequenceStart=1.0),
        lambda d: d.update(sequenceEnd=248),
        lambda d: d.update(sequence="A"),
        lambda d: d.update(sequenceChecksum="0" * 32),
        lambda d: d.update(isComplex=True),
    ],
)
def test_unrelated_or_unsupported_discovery_never_downloads_scores(monkeypatch, change):
    from sabueso.tools.db import alphamissense

    model = descriptor()
    change(model)

    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid discovery must not download scores")

    monkeypatch.setattr(alphamissense, "urlopen", forbidden)
    with pytest.raises(ConnectorError):
        get_annotations(
            "P60174",
            client=OnlineAlphaMissenseClient(alphafold_client=Discovery([model])),
        )


def test_unrelated_protein_or_multiple_canonical_descriptors_are_not_silently_chosen():
    unrelated = descriptor()
    unrelated["uniprotAccession"] = "P60175"
    for models in [[unrelated], [descriptor(), descriptor()]]:
        with pytest.raises(ConnectorError):
            get_annotations(
                "P60174",
                client=OnlineAlphaMissenseClient(alphafold_client=Discovery(models)),
            )


@pytest.mark.parametrize("records", [None, {}, ["bad"]])
def test_malformed_discovery_is_connector_failure(records):
    class Malformed:
        def prediction(self, identifier):
            return {"record": records}

    with pytest.raises(ConnectorError):
        get_annotations(
            "P60174", client=OnlineAlphaMissenseClient(alphafold_client=Malformed())
        )


@pytest.mark.parametrize("version", [True, "v6", -1, {}, 6.0])
def test_malformed_host_version_is_refused_before_score_download(version):
    model = descriptor()
    model["latestVersion"] = version
    with pytest.raises(ConnectorError):
        get_annotations(
            "P60174",
            client=OnlineAlphaMissenseClient(alphafold_client=Discovery([model])),
        )


@pytest.mark.parametrize("identifier", ["P60174-1", "P60174.2", "TIM"])
def test_invalid_canonical_accession_fails_before_discovery(identifier):
    class Forbidden:
        def annotations(self, *args):
            raise AssertionError("Invalid accession must not access a source")

    with pytest.raises(ConnectorError):
        get_annotations(identifier, client=Forbidden())


@pytest.mark.parametrize("limit", [0, -1, True, 3.5])
def test_bad_limit_fails_before_discovery(limit):
    with pytest.raises(ArgumentError):
        get_annotations("P60174", limit=limit)


def test_unstated_artifact_is_unqueried_and_does_not_credit_score_access(monkeypatch):
    from sabueso.tools.db import alphamissense

    models = native_models()
    models[0].pop("amAnnotationsUrl")
    # A native isoform URL never substitutes for an absent canonical artifact.
    models[1]["amAnnotationsUrl"] = "https://evil.example/isoform.csv"

    def forbidden(*args, **kwargs):
        raise AssertionError("Unstated canonical artifact must not be downloaded")

    monkeypatch.setattr(alphamissense, "urlopen", forbidden)
    result = get_annotations(
        "P60174", client=FixtureAlphaMissenseClient(alphafold_client=Discovery(models))
    )
    assert result["record"]["availability"] == "not_stated"
    assert result["record"]["artifact"] is None and map_variants(result) == []
    assert all(
        a["source"] != "AlphaMissense" for a in result["acquisition_trace"]["records"]
    )


def test_all_rows_are_checked_before_cap_and_missing_fixture_is_unavailable(tmp_path):
    directory = tmp_path / "alphamissense"
    directory.mkdir()
    (directory / "AF-P60174-F1-aa-substitutions.csv").write_text(
        HEADER + "M1A,0.2,LBen\nA1C,0.2,LBen\n"
    )
    client = FixtureAlphaMissenseClient(tmp_path, alphafold_client=Discovery())
    with pytest.raises(ConnectorError):
        get_annotations("P60174", limit=1, client=client)
    with pytest.raises(ConnectorError) as unavailable:
        get_annotations(
            "P60174",
            client=FixtureAlphaMissenseClient(
                tmp_path / "absent", alphafold_client=Discovery()
            ),
        )
    assert (
        unavailable.value.acquisition_trace["records"][-1]["outcome"] == "unavailable"
    )


def test_header_only_csv_is_an_empty_artifact_with_incomplete_grid(tmp_path):
    directory = tmp_path / "alphamissense"
    directory.mkdir()
    (directory / "AF-P60174-F1-aa-substitutions.csv").write_text(HEADER)
    result = get_annotations(
        "P60174",
        client=FixtureAlphaMissenseClient(tmp_path, alphafold_client=Discovery()),
    )
    assert result["acquisition_trace"]["records"][-1]["outcome"] == "empty"
    assert result["record"]["artifact"]["coverage"]["complete_grid"] is False
    assert map_variants(result) == []


def test_native_route_failure_is_not_absence(monkeypatch):
    from sabueso.tools.db import _http

    def unavailable(request, timeout):
        raise HTTPError(request.full_url, 404, "artifact missing", Message(), None)

    monkeypatch.setattr(_http, "_urlopen", unavailable)
    with pytest.raises(ConnectorError) as failed:
        get_annotations(
            "P60174", client=OnlineAlphaMissenseClient(alphafold_client=Discovery())
        )
    assert failed.value.acquisition_trace["records"][-1]["outcome"] == "failed"


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="Other"),
        lambda e: e.update(version="v6"),
        lambda e: e.update(truncated=False),
        lambda e: e["record"]["artifact"].update(sha256="0" * 64),
        lambda e: e["record"]["artifact"].update(total=True),
        lambda e: e["record"]["artifact"].update(total=4731.0),
        lambda e: e["record"]["artifact"]["rows"][0].update(am_pathogenicity="0.9"),
    ],
)
def test_mapping_refuses_changed_source_support_and_scope(change):
    envelope = get_annotations("P60174", limit=1, client=FixtureAlphaMissenseClient())
    change(envelope)
    with pytest.raises(ConnectorError):
        map_variants(envelope)


def test_entry_id_alone_suffices_and_mapping_never_reacquires(monkeypatch):
    from sabueso.tools.db import alphamissense

    envelope = get_annotations("P60174", limit=1, client=FixtureAlphaMissenseClient())
    envelope["record"]["discovery"]["record"][0].pop("modelEntityId")

    def forbidden(*args, **kwargs):
        raise AssertionError("Saved mapping must not acquire anything")

    monkeypatch.setattr(alphamissense, "get_prediction", forbidden)
    assert len(map_variants(envelope)) == 1


def test_online_discovery_and_csv_are_separately_observed_and_archive_replayed(
    tmp_path, monkeypatch
):
    from sabueso import RetrievalArchive
    from sabueso.tools.db import _http

    calls = []
    raw_csv = (ROOT / "AF-P60174-F1-aa-substitutions.csv").read_bytes()
    raw_models = (ROOT / "alphafold/P60174.json").read_bytes()

    def download(request, timeout):
        calls.append(request.full_url)
        if "/api/prediction/" in request.full_url:
            return Response(raw_models, "application/json")
        return Response(raw_csv, "text/csv")

    monkeypatch.setattr(_http, "_urlopen", download)
    archive = RetrievalArchive(tmp_path / "am.db")
    with archive.recording():
        original = get_annotations("P60174", limit=2)
    accesses = original["acquisition_trace"]["records"]
    assert len(calls) == 2
    assert [a["source"] for a in accesses] == ["AlphaFold DB", "AlphaMissense"]
    assert all(a["network_attempts"] == 1 for a in accesses)
    assert (
        original["record"]["artifact"]["sha256"] == hashlib.sha256(raw_csv).hexdigest()
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Archive replay must not query the network")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_annotations("P60174", limit=2)
    assert replay["record"]["artifact"] == original["record"]["artifact"]
    assert (
        replay["record"]["discovery"]["retrieved_at"]
        == original["record"]["discovery"]["retrieved_at"]
    )
    assert replay["retrieved_at"] == original["retrieved_at"]
    assert map_variants(replay) == map_variants(original)
    assert all(
        a["network_attempts"] == 0 for a in replay["acquisition_trace"]["records"]
    )
