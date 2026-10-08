"""Supplied files preserve bytes, literals and declared provenance without credit."""

import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.tools.source_snapshot import load_source_snapshot

META = {"source": "Synthetic", "kind": "records", "query": {"accession": "TEST"}}


@pytest.mark.parametrize(
    "suffix,text,rows",
    [
        ("json", '[{"unit":"nM","value":"0"}]', [{"unit": "nM", "value": "0"}]),
        ("jsonl", '{"value":0}\n{"value":null}\n', [{"value": 0}, {"value": None}]),
        ("ndjson", '{"value":0}\n', [{"value": 0}]),
        (
            "csv",
            "value,unit\n0,nM\n,nM\n",
            [{"value": "0", "unit": "nM"}, {"value": "", "unit": "nM"}],
        ),
        ("tsv", "value\tunit\n0\tnM\n", [{"value": "0", "unit": "nM"}]),
    ],
)
@pytest.mark.parametrize("compressed", [False, True])
def test_formats_and_raw_compressed_digest(tmp_path, suffix, text, rows, compressed):
    path = tmp_path / ("source." + suffix + (".gz" if compressed else ""))
    raw = text.encode()
    if compressed:
        raw = gzip.compress(raw)
    path.write_bytes(raw)
    result = load_source_snapshot(
        path,
        source_metadata=META,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
        records_key="results",
    )
    assert result["record"] == {"results": rows}
    assert result["retrieved_at"] is None and result["version"] is None
    receipt = result["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["digest_verification"] == "matched_caller_digest"
    assert receipt["source_access_observed"] is False
    assert "acquisition_trace" not in result


def test_metadata_is_declared_detached_and_never_redated(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('{"native":[]}', encoding="utf-8")
    metadata = {
        **META,
        "retrieved_at": "2020-01-01",
        "version": "supplied-v1",
        "terms": {"licence": "caller claim"},
    }
    result = load_source_snapshot(path, source_metadata=metadata)
    assert result["record"] == {"native": []}
    assert result["retrieved_at"] == "2020-01-01" and result["version"] == "supplied-v1"
    assert result["snapshot_receipt"]["source_metadata_basis"] == "caller_declaration"
    result["query"]["accession"] = "changed"
    result["snapshot_receipt"]["declared_terms"]["licence"] = "changed"
    assert metadata["query"]["accession"] == "TEST"
    assert metadata["terms"]["licence"] == "caller claim"


@pytest.mark.parametrize(
    "suffix,text",
    [
        ("json", '{"x":1,"x":2}'),
        ("json", '{"x":NaN}'),
        ("json", '{"x":1e999}'),
        ("jsonl", '{"x":1}\nnot-json'),
        ("csv", "x,x\n1,2\n"),
        ("csv", "x,y\n1\n"),
        ("csv", 'x,y\n"unfinished,2\n'),
        ("tsv", "x\ty\n1\t2\t3\n"),
    ],
)
def test_malformed_snapshots_are_not_empty_source_answers(tmp_path, suffix, text):
    path = tmp_path / ("bad." + suffix)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConnectorError):
        load_source_snapshot(path, source_metadata=META)


def test_digest_is_checked_before_decode_and_json_objects_cannot_be_rewritten(tmp_path):
    path = tmp_path / "data.json"
    path.write_bytes(b'{"results": []}')
    with pytest.raises(ConnectorError, match="SHA-256"):
        load_source_snapshot(path, source_metadata=META, expected_sha256="0" * 64)
    with pytest.raises(ConnectorError, match="cannot rewrite"):
        load_source_snapshot(path, source_metadata=META, records_key="results")
    with pytest.raises(FileNotFoundError):
        load_source_snapshot(tmp_path / "absent.json", source_metadata=META)


@pytest.mark.parametrize(
    "options",
    [
        {"file_format": "pickle"},
        {"expected_sha256": "bad"},
        {"source_metadata": {"source": "x"}},
        {"source_metadata": {**META, "unknown": True}},
    ],
)
def test_bad_options_fail_before_file_access(tmp_path, options):
    with pytest.raises(ArgumentError):
        load_source_snapshot(
            tmp_path / "absent.json", **{"source_metadata": META, **options}
        )


def test_loading_supplied_data_creates_no_workflow_credit(tmp_path):
    import ackredit

    path = tmp_path / "data.json"
    path.write_text(json.dumps({"data": []}), encoding="utf-8")
    with ackredit.session("supplied file"):
        with ackredit.capture("file reader") as workflow:
            load_source_snapshot(path, source_metadata=META)
    assert workflow.attribution.to_dict()["uses"] == []


@pytest.mark.parametrize("suffix", ["html", "txt"])
@pytest.mark.parametrize("compressed", [False, True])
def test_literal_formats_keep_bom_line_endings_and_content(
    tmp_path, suffix, compressed
):
    text = '\ufeff  <script>throw "do not execute";</script>\r\nN/A\r\n\r\n0\t  \r\n'
    raw = text.encode("utf-8")
    if compressed:
        raw = gzip.compress(raw)
    path = tmp_path / ("native." + suffix + (".gz" if compressed else ""))
    path.write_bytes(raw)
    result = load_source_snapshot(
        path, source_metadata=META, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    assert result["record"].encode("utf-8") == text.encode("utf-8")
    assert (
        result["snapshot_receipt"]["document_sha256"] == hashlib.sha256(raw).hexdigest()
    )
    assert result["snapshot_receipt"]["compression"] == ("gzip" if compressed else None)
    with pytest.raises(ConnectorError, match="cannot rewrite"):
        load_source_snapshot(path, source_metadata=META, records_key="rows")


def test_explicit_literal_format_and_empty_file_are_not_guessed_records(tmp_path):
    path = tmp_path / "native.download"
    path.write_bytes(b"")
    result = load_source_snapshot(path, source_metadata=META, file_format="txt")
    assert result["record"] == ""
    assert result["snapshot_receipt"]["file_format"] == "txt"
    with pytest.raises(ConnectorError, match="Snapshot format"):
        load_source_snapshot(path, source_metadata=META)


@pytest.mark.parametrize("suffix", ["json", "html", "txt"])
@pytest.mark.parametrize(
    "raw",
    [
        b"not gzip",
        gzip.compress(b"original")[:-4],
        b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\x06",
    ],
)
def test_broken_gzip_is_a_connector_failure_not_a_raw_decoder_error(
    tmp_path, suffix, raw
):
    path = tmp_path / ("broken." + suffix + ".gz")
    path.write_bytes(raw)
    with pytest.raises(ConnectorError, match="Unreadable supplied snapshot"):
        load_source_snapshot(path, source_metadata=META)


@pytest.mark.parametrize("suffix", ["html", "txt"])
def test_literal_formats_reject_non_utf8_without_lossy_repair(tmp_path, suffix):
    path = tmp_path / ("native." + suffix)
    path.write_bytes(b"\xffN/A\r\n")
    with pytest.raises(ConnectorError, match="SHA-256 mismatch"):
        load_source_snapshot(path, source_metadata=META, expected_sha256="0" * 64)
    with pytest.raises(ConnectorError, match="Unreadable supplied snapshot"):
        load_source_snapshot(path, source_metadata=META)


@pytest.mark.parametrize("source", ["fda_orphan", "iptmnet"])
def test_shared_literal_reader_matches_native_client_mapping(source):
    from sabueso.mappings import fda_orphan as fda_map
    from sabueso.mappings import iptmnet as ptm_map
    from sabueso.tools.db import fda_orphan as fda_db
    from sabueso.tools.db import iptmnet as ptm_db

    if source == "fda_orphan":
        path = Path("temp_data/fda_orphan/page__106597.html")
        mapper = fda_map.map_page
        metadata = {
            "source": fda_map.SOURCE,
            "kind": "page",
            "query": fda_map.response_query("106597"),
        }
        client = fda_db.SnapshotFDAOrphanClient
        getter = fda_db.get_page
        native_method = "page"
        identifier = "106597"
    else:
        path = Path("temp_data/iptmnet/entry__P60174.html")
        mapper = ptm_map.map_substrate_report
        metadata = {
            "source": "iPTMnet",
            "kind": "substrate_report",
            "query": ptm_map.response_query("P60174"),
        }
        client = ptm_db.SnapshotIPTMnetClient
        getter = ptm_db.get_substrate_report
        native_method = "substrate_report"
        identifier = "P60174"
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    literal = load_source_snapshot(
        path, source_metadata=metadata, expected_sha256=checksum
    )
    bound = getter(
        identifier,
        client=client(path, source_metadata=metadata, expected_sha256=checksum),
    )
    assert literal["record"].encode("utf-8") == path.read_bytes()
    # A literal envelope does not establish native completeness; only the source
    # client may qualify it for mapping. Generic loading must not bypass that gate.
    with pytest.raises(ConnectorError):
        mapper(literal)
    native = SimpleNamespace(
        **{
            native_method: lambda _: {
                "record": path.read_bytes().decode("utf-8"),
                "version": None,
            }
        }
    )
    expected = mapper(getter(identifier, client=native))
    actual = mapper(bound)
    assert actual
    # The supplied-file receipt is additional provenance, independent of native
    # fields, identity, row occurrences and response support from the native file.
    for assertion in actual:
        assertion["source_metadata"].pop("snapshot_receipt")
    assert actual == expected
    assert bound["snapshot_receipt"]["document_sha256"] == checksum
    assert bound["snapshot_receipt"]["source_access_observed"] is False
