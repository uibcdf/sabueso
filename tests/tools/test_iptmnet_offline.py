"""Native iPTMnet HTML groups, hidden support, failure states and archive replay."""

import copy
import gzip
import hashlib
import io
from collections import Counter
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms, verdict
from sabueso.mappings.iptmnet import (
    URL_ROOT,
    map_substrate_report,
    parse_substrate_report,
    response_query,
)
from sabueso.tools.db.iptmnet import (
    FixtureIPTMnetClient,
    SnapshotIPTMnetClient,
    get_substrate_report,
)

PATH = Path("temp_data/iptmnet/entry__P60174.html")
RAW = PATH.read_bytes()
NATIVE = RAW.decode()


class Client:
    def __init__(self, html=NATIVE, **context):
        self.html, self.context = html, context

    def substrate_report(self, identifier):
        return {"record": self.html, "version": None, **self.context}


def read(html=NATIVE, **context):
    return get_substrate_report("P60174", client=Client(html, **context))


def metadata():
    return {
        "source": "iPTMnet",
        "kind": "substrate_report",
        "query": response_query("P60174"),
    }


def test_original_reports_keep_all_distinct_groups_and_raw_html_support():
    for ac, sha, counts in [
        (
            "P60174",
            "13c3f90770bff2cbc34463508d453758fe518ebf9069491d229a7a623d6a9f90",
            {"P60174": 62, "P60174-1": 7, "P60174-3": 3},
        ),
        (
            "Q15796",
            "82833fa0fa7a1a6da2a9a7821c79eb8592211b7b86056cc53ad5584f1c681300",
            {"Q15796": 42, "Q15796-1": 15, "Q15796-2": 3},
        ),
    ]:
        raw = Path(f"temp_data/iptmnet/entry__{ac}.html").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == sha
        e = get_substrate_report(ac, client=FixtureIPTMnetClient())
        before = copy.deepcopy(e)
        a = map_substrate_report(e)
        assert Counter(x["asserted_value"]["native_group"] for x in a) == counts
        assert len({x["id"] for x in a}) == sum(counts.values())
        for x in a:
            assert (
                x["subject_ref"]
                == "iptmnet:report_group:" + x["asserted_value"]["native_group"]
            )
            assert x["source"]["version"] is None
            assert x["source_metadata"]["native_row"]["raw_html"] in e["record"]
            assert "curated" not in x["asserted_value"]
        a[0]["asserted_value"].clear()
        assert e == before


def test_native_unplaced_site_hidden_pmids_and_source_score_are_not_inferred():
    e = get_substrate_report("Q15796", client=FixtureIPTMnetClient())
    a = map_substrate_report(e)
    assert a[0]["asserted_value"]["Site"] == ""
    assert a[0]["asserted_value"]["Score"] == "score1"
    assert a[0]["subject_ref"] == "iptmnet:report_group:Q15796"
    pmids = a[1]["source_metadata"]["native_row"]["cells"][6]["links"]
    assert [p["text"] for p in pmids] == [
        "19413330",
        "22814378",
        "22223895",
        "20068231",
    ]
    zero = next(x for x in a if x["asserted_value"]["Score"] == "score0")
    assert zero["asserted_value"]["Score"] == "score0"
    assert "confidence" not in zero["asserted_value"]


def test_repeated_conflicting_rows_and_hidden_link_occurrences_survive():
    parsed = parse_substrate_report(NATIVE, "P60174")
    row = parsed["rows"][0]["raw_html"]
    changed = row.replace("Acetylation", "future-native-modification")
    html = NATIVE.replace(row, row + row + changed, 1)
    a = map_substrate_report(read(html))
    assert len(a) == 74 and len({x["id"] for x in a}) == 74
    assert a[2]["asserted_value"]["PTM Type"] == "future-native-modification"
    assert (
        a[0]["source_metadata"]["native_row"]["raw_html"]
        == a[1]["source_metadata"]["native_row"]["raw_html"]
    )


def test_explicit_empty_panels_differ_from_missing_panels(tmp_path):
    parsed = parse_substrate_report(NATIVE, "P60174")
    html = NATIVE
    for row in parsed["rows"]:
        html = html.replace(row["raw_html"], "", 1)
    path = tmp_path / "empty-report.html"
    path.write_text(html, encoding="utf-8", newline="")
    e = get_substrate_report(
        "P60174", client=SnapshotIPTMnetClient(path, source_metadata=metadata())
    )
    assert map_substrate_report(e) == []
    trace = e["acquisition_trace"]["records"][0]
    assert (
        trace["outcome"] == "not_found" and trace["received_groups"] == parsed["groups"]
    )
    with pytest.raises(ConnectorError):
        read(html.replace('id="asSubTabPanel"', 'id="missingPanel"'))


@pytest.mark.parametrize(
    "old,new",
    [
        ('id="asSubTable-P60174-3"', 'id="asSubTable-P60174-2"'),
        ('aria-controls="asSub-P60174-3"', 'aria-controls="asSub-P31749"'),
        ("<th>PMID</th>", "<th>Publication</th>"),
        (
            'href="https://www.uniprot.org/uniprot/P60174" title="To UniProt">P60174',
            'href="https://www.uniprot.org/uniprot/P31749" title="To UniProt">P31749',
        ),
        ('id="request"', 'id="otherRequest"'),
        ('id="asSubTabPanel"', 'id="asSubTabPanel" id="other"'),
    ],
)
def test_wrong_identity_tabs_headers_and_duplicate_attributes_fail(old, new):
    assert old in NATIVE
    with pytest.raises(ConnectorError):
        read(NATIVE.replace(old, new))


def test_malformed_late_group_fails_before_mapping_any_good_rows():
    parsed = parse_substrate_report(NATIVE, "P60174")
    last = parsed["rows"][-1]["raw_html"]
    with pytest.raises(ConnectorError):
        read(NATIVE.replace(last, last.replace("</td>", "</th>", 1)))
    with pytest.raises(ConnectorError):
        read(
            NATIVE.replace(
                last, last.replace("<td>", "<th>", 1).replace("</td>", "</th>", 1)
            )
        )


@pytest.mark.parametrize(
    "html",
    [
        None,
        "",
        "<html>Service unavailable</html>",
        NATIVE[: NATIVE.index('id="asSubTable-P60174-3"')],
    ],
)
def test_error_empty_and_partial_reports_never_mean_no_modification(html):
    with pytest.raises(ConnectorError):
        read(html)


@pytest.mark.parametrize(
    "identifier",
    [None, "", "p60174", "P60174-1", "uniprot:P60174", "P60174/", "P60174 P31749"],
)
@pytest.mark.parametrize("skip", [False, True])
def test_exact_base_query_with_or_without_digestion(identifier, skip):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_substrate_report(identifier, client=Client(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"source": "Other"},
        {"kind": "substrate_api"},
        {"query": response_query("P31749")},
        {"version": "current"},
        {"truncated": True},
    ],
)
def test_client_scope_revision_or_cut_not_resealed(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_html_snapshot_hash_time_and_declared_terms(tmp_path, compressed):
    raw = gzip.compress(RAW) if compressed else RAW
    path = tmp_path / ("report.html.gz" if compressed else "report.html")
    path.write_bytes(raw)
    declaration = metadata()
    declaration.update(
        retrieved_at="2026-10-07T22:00:00+00:00", terms={"licence": "caller declared"}
    )
    before = copy.deepcopy(declaration)
    e = get_substrate_report(
        "P60174",
        client=SnapshotIPTMnetClient(
            path,
            source_metadata=declaration,
            expected_sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    assert e["record"].encode() == RAW
    assert e["retrieved_at"] == declaration["retrieved_at"]
    assert e["snapshot_receipt"]["source_access_observed"] is False
    assert (
        e["snapshot_receipt"]["declared_terms"] == declaration["terms"]
        and declaration == before
    )
    with pytest.raises(ConnectorError):
        get_substrate_report(
            "P60174",
            client=SnapshotIPTMnetClient(
                path, source_metadata=declaration, expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "Other"),
        ("kind", "substrate_api"),
        ("query", response_query("P31749")),
        ("version", "new"),
    ],
)
def test_foreign_snapshot_binding_fails(tmp_path, key, value):
    path = tmp_path / "report.html"
    path.write_bytes(RAW)
    declaration = metadata()
    declaration[key] = value
    with pytest.raises(ConnectorError):
        get_substrate_report(
            "P60174", client=SnapshotIPTMnetClient(path, source_metadata=declaration)
        )


def test_missing_and_failed_access_are_not_empty_modification_tables(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_substrate_report("P60174", client=FixtureIPTMnetClient(tmp_path))

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 403, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_substrate_report("P60174")


def test_one_native_html_get_and_zero_network_replay_preserve_all_support(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(RAW)
        response.status = 200
        response.headers = Message()
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "archive.sqlite")
    with archive.recording():
        first = get_substrate_report("P60174")
    with archive.replaying():
        replay = get_substrate_report("P60174")
    assert calls == [URL_ROOT + "P60174/"]
    assert replay["retrieved_at"] == first["retrieved_at"]
    assert map_substrate_report(replay) == map_substrate_report(first)
    assert replay["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["iPTMnet"]["licence"] == "CC-BY-NC-SA-4.0"
    assert verdict("iPTMnet", "commercial_product")["verdict"] == "restricted"
