"""Native UniParc fixture and explicitly synthetic pagination integrity cases."""

import copy
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.mappings.uniparc import map_sequence_records, validate_results
from sabueso.tools.db import uniparc

CHECKSUM = "A8D44FC2C980A7677A3B54788D0FA323"


def native():
    return json.loads(
        Path(f"temp_data/uniparc/search__{CHECKSUM}.json").read_text(encoding="utf-8")
    )


def row(number=1):
    """Fictitious duplicate-sequence archive ids, solely for pagination tests."""
    result = copy.deepcopy(native()["results"][0])
    result["uniParcId"] = f"UPI{number:010X}"
    return result


class Response(io.BytesIO):
    status = 200

    def __init__(self, rows, total="1", release="test-release", link=None):
        super().__init__(json.dumps({"results": rows}).encode())
        self.headers = Message()
        if total is not None:
            self.headers["X-Total-Results"] = total
        if release is not None:
            self.headers["X-UniProt-Release"] = release
        if link is not None:
            self.headers["Link"] = link


def link(cursor="next"):
    return f'<{uniparc.URL}?query=checksum%3A{CHECKSUM}&format=json&cursor={cursor}>; rel="next"'


def test_native_fixture_keeps_original_pages_revision_scope_and_receipt():
    envelope = uniparc.get_records(
        CHECKSUM.lower(), client=uniparc.FixtureUniParcClient()
    )
    before = copy.deepcopy(envelope)
    (assertion,) = map_sequence_records(envelope)
    assert envelope == before and envelope["truncated"] is False
    assert envelope["record"]["pages"][0]["record"] == {"results": native()["results"]}
    assert assertion["subject_ref"] == "uniparc:UPI000002F08E"
    assert assertion["source"]["version"] == "2026_03"
    assert (
        assertion["asserted_value"]["uniprotkb_accessions"]
        == native()["results"][0]["uniProtKBAccessions"]
    )
    assert assertion["source_metadata"]["native_record"]["crossReferenceCount"] == 457
    (access,) = envelope["acquisition_trace"]["records"]
    assert access["network_attempts"] == 0 and access["access"] == "supplied_file"
    assert access["retrieved_at"] is None
    assert access["source_version"]["basis"] == "declared_fixture_release"
    assert (
        access["snapshot_receipt"]["document_sha256"]
        == hashlib.sha256(
            Path(f"temp_data/uniparc/search__{CHECKSUM}.json").read_bytes()
        ).hexdigest()
    )
    assert access["outcome"] == "received"


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r.update(uniParcId="P60174"),
        lambda r: r["sequence"].update(length=True),
        lambda r: r["sequence"].update(length=248),
        lambda r: r["sequence"].update(md5="0" * 32),
        lambda r: r["sequence"].update(value="MAP-"),
        lambda r: r.update(uniProtKBAccessions=["P60174-0"]),
        lambda r: r.update(uniProtKBAccessions=["P60174", "P60174"]),
        lambda r: r.update(uniProtKBAccessions=[True]),
        lambda r: r.update(uniProtKBAccessions=None),
        lambda r: r.update(unknown=float("nan")),
    ],
)
def test_malformed_native_sequence_or_references_are_refused(change):
    record = row()
    change(record)
    with pytest.raises(ConnectorError):
        validate_results([record], CHECKSUM)


def test_duplicate_archive_identity_and_wrong_source_are_refused():
    with pytest.raises(ConnectorError):
        validate_results([row(), row()], CHECKSUM)
    envelope = uniparc.get_records(CHECKSUM, client=uniparc.FixtureUniParcClient())
    envelope["source"] = "UniProt"
    with pytest.raises(ConnectorError):
        map_sequence_records(envelope)


@pytest.mark.parametrize("checksum", ["P60174", "0" * 31, None, 42])
def test_invalid_keys_fail_before_source_access(checksum):
    class Forbidden:
        def records(self, *args):
            raise AssertionError("Invalid input must not access a source")

    with pytest.raises(ArgumentError):
        uniparc.get_records(checksum, client=Forbidden())


def test_bounded_native_pagination_and_original_page_payloads(monkeypatch):
    responses = [
        Response([row(1)], total="2", link=link()),
        Response([row(2)], total="2"),
    ]
    calls = []

    def download(target, **options):
        calls.append(target)
        return responses.pop(0)

    monkeypatch.setattr(uniparc, "urlopen", download)
    envelope = uniparc.get_records(CHECKSUM, client=uniparc.OnlineUniParcClient())
    assert len(calls) == 2 and "cursor=next" in calls[1]
    assert envelope["record"]["total"] == 2 and envelope["truncated"] is False
    assert [
        p["record"]["results"][0]["uniParcId"] for p in envelope["record"]["pages"]
    ] == ["UPI0000000001", "UPI0000000002"]


def test_limit_keeps_original_page_and_explicit_subset(monkeypatch):
    monkeypatch.setattr(
        uniparc, "urlopen", lambda *a, **k: Response([row(1), row(2)], total="2")
    )
    envelope = uniparc.get_records(CHECKSUM, limit=1)
    assert envelope["truncated"] is True and len(envelope["record"]["results"]) == 1
    assert len(envelope["record"]["pages"][0]["record"]["results"]) == 2


@pytest.mark.parametrize(
    "continuation",
    [
        None,
        "<https://evil.example/uniparc/search?query=checksum%3A"
        + CHECKSUM
        + '&format=json>; rel="next"',
        "<https://rest.uniprot.org/uniparc/search?query=checksum%3A"
        + "0" * 32
        + '&format=json>; rel="next"',
        link() + "," + link("other"),
    ],
)
def test_incomplete_or_untrusted_continuation_keeps_only_valid_received_subset(
    monkeypatch, continuation
):
    calls = []

    def download(target, **options):
        calls.append(target)
        return Response([row()], total="2", link=continuation)

    monkeypatch.setattr(uniparc, "urlopen", download)
    with pytest.raises(ConnectorError) as failed:
        uniparc.get_records(CHECKSUM)
    assert len(calls) == 1
    assert failed.value.received_subset["results"] == [row()]
    assert failed.value.acquisition_trace["records"][0]["outcome"] == "partial"


@pytest.mark.parametrize(
    "second",
    [
        lambda: Response([row(2)], total="3"),
        lambda: Response([row(2)], total="2", release="other-release"),
        lambda: Response([row(1)], total="2"),
        lambda: Response([], total="2"),
    ],
)
def test_page_drift_or_duplicates_do_not_replace_original_subset(monkeypatch, second):
    responses = [Response([row()], total="2", link=link()), second()]
    monkeypatch.setattr(uniparc, "urlopen", lambda *a, **k: responses.pop(0))
    with pytest.raises(ConnectorError) as failed:
        uniparc.get_records(CHECKSUM)
    assert failed.value.received_subset["results"] == [row()]
    assert failed.value.received_subset["total"] == 2


def test_continuation_loop_stops_and_retains_received_rows(monkeypatch):
    responses = [
        Response([row()], total="3", link=link()),
        Response([row(2)], total="3", link=link()),
    ]
    monkeypatch.setattr(uniparc, "urlopen", lambda *a, **k: responses.pop(0))
    with pytest.raises(ConnectorError, match="repeats") as failed:
        uniparc.get_records(CHECKSUM)
    assert len(failed.value.received_subset["results"]) == 2


@pytest.mark.parametrize("total", [None, "nan", "-1", "0"])
def test_missing_or_false_native_total_is_failure(monkeypatch, total):
    monkeypatch.setattr(
        uniparc, "urlopen", lambda *a, **k: Response([row()], total=total)
    )
    with pytest.raises(ConnectorError) as failed:
        uniparc.get_records(CHECKSUM)
    assert failed.value.received_subset["results"] == []
    assert failed.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_empty_unavailable_and_route_failure_are_distinct(tmp_path, monkeypatch):
    monkeypatch.setattr(uniparc, "urlopen", lambda *a, **k: Response([], total="0"))
    empty = uniparc.get_records(CHECKSUM)
    assert empty["acquisition_trace"]["records"][0]["outcome"] == "empty"
    with pytest.raises(ConnectorError) as unavailable:
        uniparc.get_records(CHECKSUM, client=uniparc.FixtureUniParcClient(tmp_path))
    assert unavailable.value.acquisition_trace["records"][0]["outcome"] == "unavailable"

    def missing(*args, **kwargs):
        raise HTTPError(uniparc.URL, 404, "route missing", Message(), None)

    monkeypatch.setattr(uniparc, "urlopen", missing)
    with pytest.raises(ConnectorError) as failed:
        uniparc.get_records(CHECKSUM)
    assert failed.value.acquisition_trace["records"][0]["outcome"] == "failed"


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(total=True),
        lambda p: p.update(version=True),
        lambda p: p.update(checksum="0" * 32),
        lambda p: p.update(truncated=True),
        lambda p: p["pages"][0].update(release="other"),
        lambda p: p["pages"][0].update(total=True),
        lambda p: p["pages"][0]["record"]["results"][0].update(uniProtKBAccessions=[]),
        lambda p: p["pages"][0].update(url="https://evil.example/"),
    ],
)
def test_fixture_scope_and_page_receipts_are_validated(tmp_path, change):
    directory = tmp_path / "uniparc"
    directory.mkdir()
    payload = native()
    change(payload)
    (directory / f"search__{CHECKSUM}.json").write_text(
        json.dumps(payload), encoding="utf-8", newline=""
    )
    with pytest.raises(ConnectorError):
        uniparc.get_records(CHECKSUM, client=uniparc.FixtureUniParcClient(tmp_path))


def test_archive_replay_preserves_native_release_and_original_time(
    tmp_path, monkeypatch
):
    from sabueso import RetrievalArchive
    from sabueso.tools.db import _http

    monkeypatch.setattr(_http, "_urlopen", lambda *a, **k: Response([row()]))
    archive = RetrievalArchive(tmp_path / "uniparc.db")
    with archive.recording():
        original = uniparc.get_records(CHECKSUM)

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay must not access the network")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replay = uniparc.get_records(CHECKSUM)
    assert replay["record"] == original["record"]
    assert replay["retrieved_at"] == original["retrieved_at"]
    assert map_sequence_records(replay) == map_sequence_records(original)
    assert replay["acquisition_trace"]["records"][0]["network_attempts"] == 0
