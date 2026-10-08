"""Archived native Interactome3D metadata, representative scope and acquisition."""

import copy
import gzip
import hashlib
import io
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest
import pyunitwizard as puw

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms, verdict
from sabueso.mappings.interactome3d import (
    ARTIFACT,
    HEADER,
    RELEASE,
    URL,
    map_protein_structures,
    parse_proteins,
    response_query,
)
from sabueso.tools.db.interactome3d import (
    FixtureInteractome3DClient,
    SnapshotInteractome3DClient,
    get_protein_structures,
)

PATH = Path("temp_data/interactome3d") / ARTIFACT
ROW = "P60174\t1\t0\tStructure\t1wyi\tA\t100.0\t99.6\t2\t249\t-1.000\t-1.000\t-1.000\tP60174-EXP-1wyi_A.pdb\n"
NATIVE = HEADER + "\n" + ROW


class Client:
    def __init__(self, text=NATIVE, **context):
        self.text, self.context = text, context

    def protein_structures(self, identifier, release=RELEASE):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(text=NATIVE, identifier="P60174", **context):
    return get_protein_structures(identifier, client=Client(text, **context))


def metadata():
    return {
        "source": "Interactome3D",
        "kind": "protein_structures",
        "query": response_query("P60174"),
    }


def test_full_native_export_original_header_first_row_and_tpi1_percentages():
    raw = PATH.read_bytes()
    assert len(raw) == 1618274
    assert (
        hashlib.sha256(raw).hexdigest()
        == "bb1671bedacab71e528a18c1d7f662046fe61d299b70da791f1b61325098d83d"
    )
    envelope = get_protein_structures("P60174", client=FixtureInteractome3DClient())
    before = copy.deepcopy(envelope)
    assert envelope["record"].encode() == raw
    assert envelope["version"] is envelope["retrieved_at"] is None
    rows = parse_proteins(envelope["record"])
    assert len(rows) == 18000 and rows[0]["fields"][0] == "A0A024R1R8"
    with puw.context(standard_units=["nanometer", "ps", "K", "mole", "dalton"]):
        assertions = map_protein_structures(envelope)
    assert len(assertions) == 1
    value = assertions[0]["asserted_value"]
    assert (
        value["PDB_ID"] == "1wyi"
        and value["SEQ_BEGIN"] == "2"
        and value["SEQ_END"] == "249"
    )
    assert value["sequence_identity"] == {"value": 100.0, "unit": "percent"}
    assert value["coverage"] == {"value": 99.6, "unit": "percent"}
    assert value["GA431"] == value["MPQS"] == value["ZDOPE"] == "-1.000"
    assert "SEQ_IDENT" not in value and "COVERAGE" not in value
    assert assertions[0]["subject_ref"] == "interactome3d:protein:P60174"
    support = assertions[0]["source_metadata"]
    assert support["received_export_count"] == 18000
    assert support["native_row"]["fields"] == ROW.rstrip().split("\t")
    assert support["percentage_unit_basis"]["unit"] == "percent"
    trace = envelope["acquisition_trace"]["records"][0]
    assert trace["count"] == 1 and trace["received_export_count"] == 18000
    assert trace["outcome"] == "received" and trace["network_attempts"] == 0
    assert trace["source_version"]["value"] is None
    assert any(
        b["id"] == "url:https://interactome3d.irbbarcelona.org/"
        for b in trace["bibliography"]
    )
    support["native_row"]["fields"].clear()
    assert envelope == before


def test_native_representative_set_keeps_thirty_titin_occurrences_and_whitespace_chain():
    client = FixtureInteractome3DClient()
    assertions = map_protein_structures(get_protein_structures("Q8WZ42", client=client))
    assert len(assertions) == len({a["id"] for a in assertions}) == 30
    blank = map_protein_structures(get_protein_structures("A2VEC9", client=client))
    assert any(a["asserted_value"]["CHAIN"] == " " for a in blank)
    missing = get_protein_structures("P00000", client=client)
    assert map_protein_structures(missing) == []
    assert missing["acquisition_trace"]["records"][0]["outcome"] == "not_found"


@pytest.mark.parametrize("chain", ["", " ", "a", "1", "AA"])
def test_blank_native_case_extended_chain_labels_duplicate_models_and_zero_percent(
    chain,
):
    fields = ROW.rstrip().split("\t")
    fields[3:6] = ["Model", "1WYI", chain]
    fields[6:8] = ["0.0", "0.0"]
    fields[10:13] = ["future-score", "0.000", "-1.000"]
    row = "\t".join(fields) + "\n"
    assertions = map_protein_structures(read(HEADER + "\n" + row + row))
    assert len(assertions) == len({a["id"] for a in assertions}) == 2
    value = assertions[0]["asserted_value"]
    assert (
        value["TYPE"] == "Model"
        and value["PDB_ID"] == "1WYI"
        and value["CHAIN"] == chain
    )
    assert value["GA431"] == "future-score" and value["coverage"] == {
        "value": 0.0,
        "unit": "percent",
    }


@pytest.mark.parametrize(
    "index,replacement",
    [
        (0, "p60174"),
        (0, "uniprot:P60174"),
        (1, "-1"),
        (2, "rank"),
        (3, "Dom_dom_model"),
        (4, "not-pdb"),
        (6, "NaN"),
        (6, "inf"),
        (6, "unknown"),
        (6, "-1"),
        (7, "101"),
        (8, "0"),
        (8, "1.5"),
        (9, "1"),
        (13, ""),
        (10, "\x00"),
    ],
)
def test_every_late_row_validates_before_any_selection(index, replacement):
    fields = ROW.rstrip().split("\t")
    fields[index] = replacement
    with pytest.raises(ConnectorError):
        read(NATIVE + "\t".join(fields) + "\n")


@pytest.mark.parametrize(
    "text",
    [
        None,
        {},
        "",
        "\n",
        "<html>failed</html>",
        ROW,
        NATIVE + "\n",
        NATIVE + ROW.replace("\t1\t0", "\t1\t0\textra", 1),
    ],
)
def test_unsupported_header_html_or_row_width_is_not_a_negative_result(text):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        {},
        "",
        "p60174",
        "uniprot:P60174",
        "P60174/",
        "P60174.A",
        "P60174-0",
        "P60174 P01848",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_query_is_rejected_with_and_without_digestion(identifier, skip):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_protein_structures(identifier, client=Client(), skip_digestion=skip)


@pytest.mark.parametrize(
    "release", [None, "current", "2024_13", "2020_05", "../2024_12"]
)
@pytest.mark.parametrize("skip", [False, True])
def test_only_qualified_archive_release_is_supported(release, skip):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_protein_structures(
            "P60174", release=release, client=Client(), skip_digestion=skip
        )


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "interaction_structures"},
        {"version": "2024_12"},
        {"query": response_query("P00000")},
        {"query": {**response_query("P60174"), "set": "complete"}},
        {"truncated": True},
    ],
)
def test_custom_client_cannot_relabel_identity_scope_revision_or_cut(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "interaction_structures"),
        ("version", "2024_12"),
        ("query", {**response_query("P60174"), "set": "complete"}),
        ("truncated", True),
        ("query", {"uniprot_ac": "P60174"}),
    ],
)
def test_mapper_requires_exact_source_query_revision_and_complete_export(key, value):
    envelope = read()
    envelope[key] = value
    with pytest.raises(ConnectorError):
        map_protein_structures(envelope)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_snapshot_original_hash_time_terms_and_no_caller_mutation(
    tmp_path, compressed
):
    raw = gzip.compress(NATIVE.encode()) if compressed else NATIVE.encode()
    path = tmp_path / ("proteins.dat.gz" if compressed else "proteins.dat")
    path.write_bytes(raw)
    scope = {
        **metadata(),
        "retrieved_at": "2026-10-07T21:00:00+00:00",
        "terms": {"licence": "NOT-STATED"},
    }
    client = SnapshotInteractome3DClient(
        path, source_metadata=scope, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    scope["query"]["set"] = "complete"
    envelope = get_protein_structures("P60174", client=client)
    assert (
        envelope["record"] == NATIVE
        and envelope["retrieved_at"] == "2026-10-07T21:00:00+00:00"
    )
    receipt = envelope["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["source_access_observed"] is False and receipt["declared_terms"] == {
        "licence": "NOT-STATED"
    }
    assert (
        map_protein_structures(envelope)[0]["source_metadata"]["snapshot_receipt"]
        == receipt
    )
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_protein_structures(
            "P60174",
            client=SnapshotInteractome3DClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "interaction_structures"),
        ("version", "2024_12"),
        ("query", response_query("P00000")),
        ("query", {**response_query("P60174"), "organism": "mouse"}),
    ],
)
def test_snapshot_identity_revision_and_organism_are_not_rewritten(
    tmp_path, key, value
):
    path = tmp_path / "proteins.dat"
    path.write_text(NATIVE, encoding="utf-8", newline="")
    scope = metadata()
    scope[key] = value
    with pytest.raises(ConnectorError):
        get_protein_structures(
            "P60174", client=SnapshotInteractome3DClient(path, source_metadata=scope)
        )


@pytest.mark.parametrize(
    "raw,compressed",
    [
        (b"", False),
        (b"\xff", False),
        (b"<html>failed</html>", False),
        (b"not gzip", True),
        (gzip.compress(NATIVE.encode())[:-4], True),
    ],
)
def test_unreadable_supplied_file_is_not_not_listed(tmp_path, raw, compressed):
    path = tmp_path / ("proteins.dat.gz" if compressed else "proteins.dat")
    path.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_protein_structures(
            "P60174",
            client=SnapshotInteractome3DClient(path, source_metadata=metadata()),
        )


def test_missing_fixture_or_http_error_is_not_biological_absence(tmp_path, monkeypatch):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_protein_structures("P60174", client=FixtureInteractome3DClient(tmp_path))

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 404, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_protein_structures("P60174")


def test_one_metadata_get_and_archive_replay_preserve_original_time_hash_and_terms(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(NATIVE.encode())
        response.status = 200
        response.headers = Message()
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "archive.sqlite")
    with archive.recording():
        first = get_protein_structures("P60174")
    assert calls == [URL]
    assert first["download_sha256"] == hashlib.sha256(NATIVE.encode()).hexdigest()

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay attempted network")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_protein_structures("P60174")
    assert first["record"] == replay["record"] == NATIVE
    assert first["retrieved_at"] == replay["retrieved_at"]
    assert map_protein_structures(first) == map_protein_structures(replay)
    assert first["acquisition_trace"]["records"][0]["network_attempts"] == 1
    assert replay["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["Interactome3D"]["licence"] == "NOT-STATED"
    assert verdict("Interactome3D", "redistribution")["verdict"] == "unknown"
