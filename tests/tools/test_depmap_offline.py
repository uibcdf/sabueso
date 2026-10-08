"""DepMap original model CSV, fixed release, native rows and failure semantics."""

import copy
import csv
import gzip
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms
from sabueso.mappings.depmap import (
    ARTIFACT,
    COLUMNS,
    MAPPED,
    RELEASE,
    SHA256,
    URL,
    map_model,
    parse_models,
    response_query,
)
from sabueso.tools.db.depmap import FixtureDepMapClient, SnapshotDepMapClient, get_model

PATH = Path("temp_data/depmap") / ARTIFACT
ROWS = parse_models(PATH.read_text())
ROW = next(r["fields"] for r in ROWS if r["fields"][0] == "ACH-000019")


def csv_text(rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(COLUMNS)
    writer.writerows(rows)
    return output.getvalue()


NATIVE = csv_text([ROW])


class Client:
    def __init__(self, text=NATIVE, **context):
        self.text, self.context = text, context

    def model(self, identifier, release=RELEASE):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(text=NATIVE, **context):
    return get_model("ACH-000019", client=Client(text, **context))


def metadata():
    return {"source": "DepMap", "kind": "model", "query": response_query("ACH-000019")}


def test_full_original_public_release_hash_metadata_grant_and_mcf7_context():
    raw = PATH.read_bytes()
    assert len(raw) == 645696 and hashlib.sha256(raw).hexdigest() == SHA256
    native_metadata = json.loads(
        Path("temp_data/depmap/24Q4__figshare_27993248__v1.json").read_text()
    )
    assert (
        native_metadata["title"] == "DepMap 24Q4 Public"
        and native_metadata["version"] == 1
    )
    assert native_metadata["license"]["name"] == "CC BY 4.0"
    artifact = next(f for f in native_metadata["files"] if f["name"] == "Model.csv")
    assert artifact["download_url"] == URL
    assert hashlib.md5(raw).hexdigest() == artifact["computed_md5"]
    envelope = get_model("ACH-000019", client=FixtureDepMapClient())
    before = copy.deepcopy(envelope)
    assert (
        envelope["record"].encode() == raw
        and len(parse_models(envelope["record"])) == 2105
    )
    a = map_model(envelope)[0]
    value = a["asserted_value"]
    assert value["CellLineName"] == "MCF7" and value["ModelID"] == "ACH-000019"
    assert a["subject_ref"] == "depmap:model:ACH-000019"
    assert (
        set(value) == set(MAPPED)
        and "Age" not in value
        and "FormulationID" not in value
    )
    assert a["source"]["version"] is None
    assert a["source_metadata"]["selected_dataset"]["article_version"] == 1
    assert a["source_metadata"]["native_row"]["fields"] == ROW
    assert a["source_metadata"]["received_export_count"] == 2105
    a["asserted_value"].clear()
    assert envelope == before


def test_not_listed_is_not_failed_acquisition_or_gene_essentiality():
    envelope = get_model("ACH-999999", client=FixtureDepMapClient())
    assert map_model(envelope) == []
    trace = envelope["acquisition_trace"]["records"][0]
    assert trace["outcome"] == "not_found" and trace["received_export_count"] == 2105


def test_duplicate_conflicting_native_rows_quoted_names_and_blank_metadata_survive():
    second = list(ROW)
    second[COLUMNS.index("CellLineName")] = 'different, "quoted"\nname'
    second[COLUMNS.index("RRID")] = ""
    second[COLUMNS.index("DepmapModelType")] = "future-native-type"
    assertions = map_model(read(csv_text([ROW, ROW, second])))
    assert len(assertions) == len({a["id"] for a in assertions}) == 3
    assert assertions[2]["asserted_value"]["CellLineName"] == second[2]
    assert assertions[2]["asserted_value"]["RRID"] == ""


@pytest.mark.parametrize(
    "text",
    [
        None,
        {},
        "",
        "<html>verification</html>",
        NATIVE.replace("ModelID", "model_id", 1),
        NATIVE + "\n",
        NATIVE + "broken,row\n",
        NATIVE + '"unterminated',
        NATIVE.replace("ACH-000019", "ach-000019"),
        NATIVE.replace("MCF7", "bad\x00name"),
    ],
)
def test_all_native_header_and_late_rows_validate_before_selection(text):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        "",
        "MCF7",
        "ach-000019",
        "ACH-19",
        "ACH-000019/",
        "P60174",
        "ACH-000019 ACH-000020",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_exact_model_identity_with_and_without_digestion(identifier, skip):
    with pytest.raises((ConnectorError, ArgumentError)):
        get_model(identifier, client=Client(), skip_digestion=skip)


@pytest.mark.parametrize("release", [None, "current", "25Q2", "24Q4.v2", "../24Q4"])
@pytest.mark.parametrize("skip", [False, True])
def test_unqualified_release_is_not_silently_substituted(release, skip):
    with pytest.raises((ConnectorError, ArgumentError)):
        get_model("ACH-000019", release=release, client=Client(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"version": "current"},
        {"truncated": True},
        {"source": "other"},
        {"kind": "dependencies"},
        {"query": response_query("ACH-000001")},
    ],
)
def test_wrong_envelope_is_not_resealed(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_native_csv_hash_time_terms_and_untouched_declaration(
    tmp_path, compressed
):
    raw = PATH.read_bytes()
    if compressed:
        raw = gzip.compress(raw)
    path = tmp_path / ("native.csv.gz" if compressed else "native.csv")
    path.write_bytes(raw)
    declaration = metadata()
    declaration.update(
        retrieved_at="2026-10-07T22:00:00+00:00",
        terms={"licence": "caller declaration"},
    )
    before = copy.deepcopy(declaration)
    envelope = get_model(
        "ACH-000019",
        client=SnapshotDepMapClient(
            path,
            source_metadata=declaration,
            expected_sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    assert envelope["retrieved_at"] == declaration["retrieved_at"]
    assert envelope["snapshot_receipt"]["source_access_observed"] is False
    assert envelope["snapshot_receipt"]["declared_terms"] == declaration["terms"]
    assert declaration == before
    with pytest.raises(ConnectorError):
        get_model(
            "ACH-000019",
            client=SnapshotDepMapClient(
                path, source_metadata=declaration, expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "Other"),
        ("kind", "dependencies"),
        ("query", response_query("ACH-000001")),
        ("version", "new"),
    ],
)
def test_supplied_source_query_revision_are_bound(tmp_path, field, value):
    path = tmp_path / "native.csv"
    path.write_bytes(PATH.read_bytes())
    declaration = metadata()
    declaration[field] = value
    with pytest.raises(ConnectorError):
        get_model(
            "ACH-000019", client=SnapshotDepMapClient(path, source_metadata=declaration)
        )


def test_missing_fixture_http_failure_and_changed_release_digest_fail(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_model("ACH-000019", client=FixtureDepMapClient(tmp_path))

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 403, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_model("ACH-000019")

    def changed(request, **kwargs):
        response = io.BytesIO(NATIVE.encode())
        response.status = 200
        response.headers = Message()
        return response

    monkeypatch.setattr(_http, "_urlopen", changed)
    with pytest.raises(ConnectorError, match="digest changed"):
        get_model("ACH-000019")


def test_fixed_native_file_one_get_and_zero_network_replay(tmp_path, monkeypatch):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "archive.sqlite")
    with archive.recording():
        first = get_model("ACH-000019")
    assert calls == [URL] and first["download_sha256"] == SHA256

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay attempted network")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_model("ACH-000019")
    assert first["record"] == replay["record"]
    assert first["retrieved_at"] == replay["retrieved_at"]
    assert map_model(first) == map_model(replay)
    assert replay["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["DepMap"]["licence"] == "CC-BY-4.0"
