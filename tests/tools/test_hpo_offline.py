"""HPO native disease context, opaque frequency, dated scope and acquisition."""

import copy
import gzip
import hashlib
import io
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import USES, retention, source_terms, verdict
from sabueso.mappings.hpo import (
    HEADER,
    RELEASE,
    export_url,
    map_gene_annotations,
    response_query,
)
from sabueso.tools.db.hpo import (
    FixtureHPOClient,
    SnapshotHPOClient,
    get_gene_annotations,
)

PATH = Path("temp_data/hpo/v2026-09-01/genes_to_phenotype.txt")
ID = "7167"
ROW = "7167\tTPI1\tHP:0001252\tHypotonia\t1/2\tOMIM:615512\n"
NATIVE = HEADER + "\n" + ROW


class Client:
    def __init__(self, text, **context):
        self.text, self.context = text, context

    def gene_annotations(self, identifier, release):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": release,
            **self.context,
        }


def read(text=NATIVE, identifier=ID, **context):
    return get_gene_annotations(identifier, client=Client(text, **context))


def metadata():
    return {
        "source": "HPO",
        "kind": "gene_phenotypes",
        "query": response_query(ID),
        "version": RELEASE,
    }


def test_original_complete_release_retains_disease_and_frequency_occurrences():
    raw = PATH.read_bytes()
    assert len(raw) == 20821704
    assert (
        hashlib.sha256(raw).hexdigest()
        == "507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c"
    )
    envelope = get_gene_annotations(ID, client=FixtureHPOClient())
    before = copy.deepcopy(envelope)
    assert envelope["record"].encode() == raw
    assert envelope["version"] == RELEASE and envelope["truncated"] is False
    assertions = map_gene_annotations(envelope)
    assert len(assertions) == 44
    assert len({x["id"] for x in assertions}) == 44
    assert all(x["subject_ref"] == "ncbigene:7167" for x in assertions)
    assert all(
        x["field_path"] == "annotations.gene_phenotype_associations" for x in assertions
    )
    assert all(x["source"]["version"] == RELEASE for x in assertions)
    assert all(
        x["source_metadata"]["received_export_count"] == 333983 for x in assertions
    )
    hypotonia = [
        x["asserted_value"]
        for x in assertions
        if x["asserted_value"]["hpo_id"] == "HP:0001252"
    ]
    assert [(x["frequency"], x["disease_id"]) for x in hypotonia] == [
        ("1/2", "OMIM:615512"),
        ("HP:0040281", "ORPHA:868"),
    ]
    assert any(x["asserted_value"]["frequency"] == "-" for x in assertions)
    trace = envelope["acquisition_trace"]["records"][0]
    assert trace["outcome"] == "received" and trace["count"] == 44
    assert trace["received_export_count"] == 333983 and trace["network_attempts"] == 0
    assert trace["source_version"]["value"] == RELEASE
    assert any(x["id"] == "url:https://hpo.jax.org/" for x in trace["bibliography"])
    assertions[0]["asserted_value"].clear()
    assertions[0]["source_metadata"]["native_row"]["fields"].clear()
    assert envelope == before


def test_repeated_conflicting_disease_frequency_and_future_literals_stay_independent():
    rows = [
        ROW,
        ROW,
        ROW.replace("1/2", "0/2"),
        ROW.replace("1/2", "34.6%"),
        ROW.replace("1/2", "HP:0040281").replace("OMIM:615512", "ORPHA:868"),
        ROW.replace("1/2", "future declaration"),
        ROW.replace("7167", "7168"),
    ]
    envelope = read(HEADER + "\n" + "".join(rows))
    assertions = map_gene_annotations(envelope)
    assert len(assertions) == 6 and len({x["id"] for x in assertions}) == 6
    assert [x["asserted_value"]["frequency"] for x in assertions] == [
        "1/2",
        "1/2",
        "0/2",
        "34.6%",
        "HP:0040281",
        "future declaration",
    ]
    assert [x["source_metadata"]["native_row"]["line"] for x in assertions] == list(
        range(2, 8)
    )
    assert all(x["source_metadata"]["received_export_count"] == 7 for x in assertions)
    assert not map_gene_annotations(read(HEADER + "\n" + ROW.replace("7167", "7168")))


@pytest.mark.parametrize(
    "text",
    [
        None,
        {},
        "",
        "<html>failed</html>",
        HEADER.replace("frequency", "frequency_percent") + "\n" + ROW,
        NATIVE + "malformed\n",
        NATIVE + ROW.replace("7167", "07167"),
        NATIVE + ROW.replace("HP:0001252", "HP:1252"),
        NATIVE + ROW.replace("OMIM:615512", "other:615512"),
        NATIVE + ROW.replace("TPI1", ""),
        NATIVE + ROW.replace("1/2", ""),
        NATIVE + ROW.replace("1/2", "1\x00/2"),
        NATIVE + ROW.rstrip("\n") + "\textra\n",
    ],
)
def test_bad_headers_error_bodies_and_late_unrelated_rows_fail_before_selection(text):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        True,
        7167,
        "",
        "0",
        "07167",
        "TPI1",
        "NCBIGene:7167",
        "7167/",
        "7167?x=1",
        "7167\nother",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_identifiers_fail_before_transport_even_without_digestion(
    identifier, skip
):
    class Forbidden:
        def gene_annotations(self, *args):
            pytest.fail("Invalid query reached transport")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_gene_annotations(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "release",
    [
        None,
        2026,
        "latest",
        "2026-09-01",
        "v2026-02-30",
        "v2026-13-01",
        "v2026-09-01/../",
        "v2026-09-01?x=1",
    ],
)
def test_invalid_release_never_reaches_transport(release):
    class Forbidden:
        def gene_annotations(self, *args):
            pytest.fail("Invalid release reached transport")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_gene_annotations(ID, release=release, client=Forbidden())


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "ontology"},
        {"version": None},
        {"version": "v2026-08-01"},
        {"query": {**response_query(ID), "ncbi_gene_id": "7168"}},
        {"truncated": True},
        {"truncated": None},
    ],
)
def test_custom_client_scope_release_and_cut_are_not_reassigned(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "ontology"),
        ("version", "v2026-08-01"),
        ("truncated", None),
        ("query", {"ncbi_gene_id": ID}),
        ("query", {**response_query(ID), "include_ancestors": True}),
    ],
)
def test_mapping_rejects_changed_scope_and_release(key, value):
    envelope = read()
    envelope[key] = value
    with pytest.raises(ConnectorError):
        map_gene_annotations(envelope)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_snapshot_keeps_full_text_hash_time_and_declared_terms(
    tmp_path, compressed
):
    raw = gzip.compress(NATIVE.encode()) if compressed else NATIVE.encode()
    path = tmp_path / ("original.tsv.gz" if compressed else "original.tsv")
    path.write_bytes(raw)
    scope = metadata()
    scope.update(
        retrieved_at="2026-10-07T19:25:59+00:00", terms={"licence": "HPO-CONSORTIUM"}
    )
    client = SnapshotHPOClient(
        path,
        source_metadata=scope,
        expected_sha256=hashlib.sha256(raw).hexdigest().upper(),
    )
    scope["query"]["ncbi_gene_id"] = "7168"
    envelope = get_gene_annotations(ID, client=client)
    assert (
        envelope["record"] == NATIVE
        and envelope["retrieved_at"] == "2026-10-07T19:25:59+00:00"
    )
    receipt = envelope["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["declared_terms"] == {"licence": "HPO-CONSORTIUM"}
    assert receipt["source_access_observed"] is False
    assert (
        map_gene_annotations(envelope)[0]["source_metadata"]["snapshot_receipt"]
        == receipt
    )
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_gene_annotations(
            ID,
            client=SnapshotHPOClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "ontology"),
        ("version", None),
        ("version", "v2026-08-01"),
        ("query", {**response_query(ID), "ncbi_gene_id": "7168"}),
    ],
)
def test_supplied_metadata_cannot_override_source_kind_id_or_release(
    tmp_path, key, value
):
    path = tmp_path / "native.tsv"
    path.write_text(NATIVE)
    scope = metadata()
    scope[key] = value
    with pytest.raises(ConnectorError):
        get_gene_annotations(ID, client=SnapshotHPOClient(path, source_metadata=scope))


@pytest.mark.parametrize(
    "raw,compressed",
    [
        (b"\xff", False),
        (b"", False),
        (b"<html>blocked</html>", False),
        (b"not gzip", True),
        (gzip.compress(NATIVE.encode())[:-4], True),
    ],
)
def test_unreadable_snapshots_are_not_missing_matches(tmp_path, raw, compressed):
    path = tmp_path / ("native.tsv.gz" if compressed else "native.tsv")
    path.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_gene_annotations(
            ID, client=SnapshotHPOClient(path, source_metadata=metadata())
        )


def test_missing_fixture_http_failure_and_received_not_listed_are_distinct(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_gene_annotations(ID, client=FixtureHPOClient(tmp_path))
    path = tmp_path / "native.tsv"
    path.write_text(HEADER + "\n" + ROW.replace("7167", "7168"))
    empty = get_gene_annotations(
        ID, client=SnapshotHPOClient(path, source_metadata=metadata())
    )
    assert empty["acquisition_trace"]["records"][0]["outcome"] == "not_found"
    assert not map_gene_annotations(empty)

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 404, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_gene_annotations(ID)


def test_one_dated_export_get_and_archive_replay_keep_release_with_zero_network(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(NATIVE.encode())
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "text/plain"
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "hpo.db")
    with archive.recording():
        first = get_gene_annotations(ID)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay attempted network or acquired a linked input")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_gene_annotations(ID)
    assert calls == [export_url(RELEASE)]
    assert first["record"] == second["record"] == NATIVE
    assert first["retrieved_at"] == second["retrieved_at"]
    assert first["download_sha256"] == second["download_sha256"]
    assert map_gene_annotations(first) == map_gene_annotations(second)
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert archive.sources()["HPO"]["retention"]["share"] == "unknown"


@pytest.mark.parametrize("use", USES)
def test_custom_consortium_and_input_rights_do_not_get_a_blanket_open_verdict(use):
    assert source_terms()["HPO"]["licence"] == "HPO-CONSORTIUM"
    answer = verdict("HPO", use)
    assert (
        answer["verdict"] == "unknown" and answer["reason"] == "licence_not_classified"
    )
    assert answer["caveats"]
    kept = retention("HPO")
    assert kept["keep"] == "internal" and kept["share"] == "unknown"
