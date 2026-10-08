"""Native monthly CIViC items, complete profile scope and original-time replay."""

import copy
import csv
import gzip
import hashlib
import io
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import retention, source_terms
from sabueso.mappings.civic import (
    COLUMNS,
    map_molecular_profile_items,
    parse_export,
    response_query,
)
from sabueso.tools.db.civic import (
    FixtureCIViCClient,
    SnapshotCIViCClient,
    export_url,
    get_molecular_profile_items,
)

RELEASE = "01-Oct-2026"
PATH = Path(f"temp_data/civic/{RELEASE}-AcceptedClinicalEvidenceSummaries.tsv")


def native():
    return PATH.read_text(encoding="utf-8")


def small():
    return [list(COLUMNS)] + [
        list(x["fields"].values())
        for x in parse_export(native())["rows"]
        if x["fields"]["molecular_profile_id"] == "12"
    ][:2]


def encode(rows):
    s = io.StringIO(newline="")
    csv.writer(s, delimiter="\t", quoting=csv.QUOTE_ALL).writerows(rows)
    return s.getvalue()


class Client:
    def __init__(self, text, **context):
        self.text, self.context = text, context

    def molecular_profile_items(self, identifier, release):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": release,
            **self.context,
        }


def get(identifier="12", **kwargs):
    return get_molecular_profile_items(identifier, release=RELEASE, **kwargs)


def metadata():
    return {
        "source": "CIViC",
        "kind": "molecular_profile_items",
        "query": response_query("12", RELEASE),
        "version": RELEASE,
        "retrieved_at": "2026-10-06T12:00:00+00:00",
    }


def test_full_native_monthly_export_preserves_every_braf_item_and_conflict():
    assert len(PATH.read_bytes()) == 4154685
    assert (
        hashlib.sha256(PATH.read_bytes()).hexdigest()
        == "a618939c33c7cc9cc530be5f0a51fc330b29ad46b3f9a5bebeddcd871375e086"
    )
    e = get(client=FixtureCIViCClient())
    before = copy.deepcopy(e)
    a = map_molecular_profile_items(e)
    assert len(a) == len({x["id"] for x in a}) == 93
    assert [x["asserted_value"] for x in a] == [
        x["fields"]
        for x in parse_export(native())["rows"]
        if x["fields"]["molecular_profile_id"] == "12"
    ]
    assert {x["asserted_value"]["evidence_direction"] for x in a} == {
        "Supports",
        "Does Not Support",
    }
    assert {x["asserted_value"]["is_flagged"] for x in a} == {"false"}
    assert all(
        x["subject_ref"] == "civic:molecular_profile:12"
        and x["source"]["version"] == RELEASE
        for x in a
    )
    assert all(
        x["retrieved_at"] is None
        and "knowledge_class" not in x
        and "protein_ref" not in x["asserted_value"]
        for x in a
    )
    trace = e["acquisition_trace"]["records"][0]
    assert (
        trace["received_export_rows"] == 4940
        and trace["count"] == 93
        and trace["network_attempts"] == 0
    )
    assert e["record"] == native() and e == before
    a[0]["asserted_value"].clear()
    assert e == before


def test_accepted_flagged_item_keeps_its_editorial_flag():
    items = map_molecular_profile_items(get("32", client=FixtureCIViCClient()))
    flagged = [x for x in items if x["asserted_value"]["evidence_id"] == "31"]
    assert len(flagged) == 1
    assert flagged[0]["asserted_value"]["evidence_status"] == "accepted"
    assert flagged[0]["asserted_value"]["is_flagged"] == "true"
    assert flagged[0]["subject_ref"] == "civic:molecular_profile:32"


def test_combination_profile_keeps_variants_therapies_and_direction_atomic():
    a = map_molecular_profile_items(get("5969", client=FixtureCIViCClient()))
    assert len(a) == 1
    row = a[0]["asserted_value"]
    assert row["molecular_profile"] == "ALK F1174L AND RANBP2::ALK Fusion"
    assert row["therapies"] == "Crizotinib" and row["significance"] == "Resistance"
    assert (
        row["evidence_id"] == "32"
        and a[0]["subject_ref"] == "civic:molecular_profile:5969"
    )


def test_repeated_conflicting_and_future_labels_preserve_native_occurrences():
    r = small()
    r.append(copy.deepcopy(r[1]))
    r.append(copy.deepcopy(r[1]))
    r[-1][8] = "Future direction"
    r[-1][10] = "Future significance"
    r[-1][5] = "Therapy A,Therapy B"
    r[-1][11] = 'quoted\ttext\nwith "context"'
    a = map_molecular_profile_items(get(client=Client(encode(r))))
    assert len(a) == len({x["id"] for x in a}) == 4
    assert a[0]["asserted_value"] == a[2]["asserted_value"]
    assert a[3]["asserted_value"]["therapies"] == "Therapy A,Therapy B"
    assert a[3]["asserted_value"]["evidence_statement"] == r[-1][11]
    assert a[3]["asserted_value"]["evidence_direction"] == "Future direction"


def test_not_listed_is_not_negative_clinical_association():
    e = get("999999999", client=FixtureCIViCClient())
    assert map_molecular_profile_items(e) == []
    assert (
        e["acquisition_trace"]["records"][0]["native_result_declaration"]
        == "not_listed_in_received_export"
    )


@pytest.mark.parametrize(
    "identifier", ["0", "012", "BRAF", "P15056", "12,13", "12/", "12.0", 12, None]
)
def test_exact_native_profile_identity_refuses_ambiguous_queries(identifier):
    with pytest.raises((ArgumentError, ConnectorError)):
        get(identifier, client=Client(encode(small())))


@pytest.mark.parametrize(
    "release",
    [
        "nightly",
        "latest",
        "2026-10-01",
        "02-Oct-2026",
        "01-Foo-2026",
        "01-Oct-0000",
        "01-Oct-2026/",
        None,
    ],
)
def test_explicit_monthly_release_rejects_implicit_or_malformed_selectors(release):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_molecular_profile_items(
            "12", release=release, client=Client(encode(small()))
        )


def test_backend_scope_survives_skipped_digestion():
    assert (
        len(map_molecular_profile_items(get(" 12 ", client=Client(encode(small())))))
        == 2
    )
    with pytest.raises(ConnectorError):
        get(" 12 ", client=Client(encode(small())), skip_digestion=True)
    with pytest.raises(ConnectorError):
        get_molecular_profile_items(
            "12",
            release=" nightly ",
            client=Client(encode(small())),
            skip_digestion=True,
        )


@pytest.mark.parametrize(
    "text", [None, "", "<html>error</html>", "No result found.", '"unclosed', []]
)
def test_malformed_document_is_not_not_found(text):
    with pytest.raises(ConnectorError):
        get(client=Client(text))


@pytest.mark.parametrize(
    "column,value",
    [
        ("molecular_profile_id", "012"),
        ("evidence_id", "0"),
        ("evidence_status", "submitted"),
        ("molecular_profile", ""),
        ("evidence_civic_url", "https://civicdb.org/links/evidence_items/OTHER"),
        (
            "molecular_profile_civic_url",
            "https://civicdb.org/links/molecular_profiles/13",
        ),
    ],
)
def test_complete_export_validates_unrelated_rows_before_selection(column, value):
    rows = small()
    rows[2][1] = "13"
    rows[2][23] = "https://civicdb.org/links/molecular_profiles/13"
    rows[2][COLUMNS.index(column)] = (
        value if column != "molecular_profile_civic_url" else "bad"
    )
    with pytest.raises(ConnectorError):
        get(client=Client(encode(rows)))


@pytest.mark.parametrize(
    "change",
    [lambda r: r[0].reverse(), lambda r: r[1].pop(), lambda r: r[1].append("extra")],
)
def test_full_native_shape_is_required(change):
    rows = small()
    change(rows)
    with pytest.raises(ConnectorError):
        get(client=Client(encode(rows)))


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "assertions"),
        ("query", response_query("13", RELEASE)),
        ("version", "01-Sep-2026"),
    ],
)
def test_supplied_snapshot_binds_source_kind_query_and_monthly_release(
    tmp_path, key, value
):
    p = tmp_path / "native.tsv"
    p.write_text(encode(small()), encoding="utf-8", newline="")
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get(client=SnapshotCIViCClient(p, source_metadata=m))


@pytest.mark.parametrize("compressed", [False, True])
def test_snapshot_byte_hash_original_time_and_terms_survive(tmp_path, compressed):
    b = encode(small()).encode()
    b = gzip.compress(b) if compressed else b
    p = tmp_path / ("native.tsv.gz" if compressed else "native.tsv")
    p.write_bytes(b)
    m = metadata()
    m["terms"] = {"licence": "CC0-1.0"}
    c = SnapshotCIViCClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(b).hexdigest()
    )
    m["query"]["molecular_profile_id"] = "13"
    e = get(client=c)
    assert e["retrieved_at"] == metadata()["retrieved_at"] and e["version"] == RELEASE
    assert e["snapshot_receipt"]["document_sha256"] == hashlib.sha256(b).hexdigest()
    assert e["snapshot_receipt"]["declared_terms"] == {"licence": "CC0-1.0"}
    assert e["snapshot_receipt"]["source_access_observed"] is False
    with pytest.raises(ConnectorError, match="SHA-256"):
        get(
            client=SnapshotCIViCClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            )
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "assertions"),
        ("version", None),
        ("truncated", True),
        ("truncated", None),
        (
            "query",
            {"molecular_profile_id": "12", "release": RELEASE, "dataset": "submitted"},
        ),
    ],
)
def test_direct_mapping_refuses_unqualified_scope(key, value):
    e = get(client=Client(encode(small())))
    e[key] = value
    with pytest.raises(ConnectorError):
        map_molecular_profile_items(e)


@pytest.mark.parametrize(
    "context",
    [
        {"version": None},
        {"version": "nightly"},
        {"truncated": True},
        {"truncated": None},
    ],
)
def test_public_lookup_refuses_unqualified_revisions_and_cuts(context):
    with pytest.raises(ConnectorError):
        get(client=Client(encode(small()), **context))


def test_missing_and_corrupt_supplied_files_are_access_failures(tmp_path):
    with pytest.raises(ConnectorError):
        get(client=FixtureCIViCClient(tmp_path))
    p = tmp_path / "bad.tsv.gz"
    p.write_bytes(b"not gzip")
    with pytest.raises(ConnectorError):
        get(client=SnapshotCIViCClient(p, source_metadata=metadata()))


@pytest.mark.parametrize("status", [404, 503])
def test_http_error_is_not_empty_accepted_export(monkeypatch, status):
    from sabueso.tools.db import _http as http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, status, "Unavailable", {}, None)

    monkeypatch.setattr(http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get()


def test_one_get_archive_replay_preserves_full_native_text_time_and_release(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http as http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "text/tab-separated-values"
        return response

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "civic.db")
    with archive.recording():
        first = get()

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay must not contact CIViC or linked sources.")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        second = get()
    assert calls == [export_url(RELEASE)]
    assert first["record"] == second["record"] == native()
    assert (
        first["retrieved_at"] == second["retrieved_at"]
        and first["version"] == second["version"] == RELEASE
    )
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_molecular_profile_items(first) == map_molecular_profile_items(second)
    assert first["acquisition_trace"]["records"][0]["network_attempts"] == 1
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert second["acquisition_trace"]["records"][0]["access"] == "replay"
    assert (
        source_terms()["CIViC"]["licence"] == "CC0-1.0"
        and retention("CIViC")["keep"] == "yes"
    )
