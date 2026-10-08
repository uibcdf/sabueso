"""Native FDA OOPD tables, scientific limits, binding, failures and replay."""

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
from sabueso.core.terms import retention, source_terms, verdict
from sabueso.mappings.fda_orphan import (
    SOURCE,
    URL_ROOT,
    map_page,
    parse_page,
    response_query,
)
from sabueso.tools.db.fda_orphan import (
    FixtureFDAOrphanClient,
    SnapshotFDAOrphanClient,
    get_page,
)

RAW = Path("temp_data/fda_orphan/page__106597.html").read_bytes()
NATIVE = RAW.decode()


class Client:
    def __init__(self, text=NATIVE, **context):
        self.text, self.context = text, context

    def page(self, identifier):
        return {"record": self.text, "version": None, **self.context}


def read(text=NATIVE, **context):
    return get_page("106597", client=Client(text, **context))


def metadata():
    return {"source": SOURCE, "kind": "page", "query": response_query("106597")}


def test_original_pages_preserve_designation_and_each_approval_independently():
    for key, count, sha in [
        (
            "476815",
            1,
            "549798ff1dada54a7d34d52876d13962136392ef903db59dda2fda2a196e08f4",
        ),
        (
            "106597",
            4,
            "3afd99f87e17caeaf2d91469c76c2db7b61e16ae93060f8f6c3d121ce9998d23",
        ),
    ]:
        raw = Path(f"temp_data/fda_orphan/page__{key}.html").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == sha
        envelope = get_page(key, client=FixtureFDAOrphanClient())
        before = copy.deepcopy(envelope)
        assertions = map_page(envelope)
        assert len(assertions) == count
        assert len({a["id"] for a in assertions}) == count
        assert assertions[0]["asserted_value"]["kind"] == "designation"
        for a in assertions:
            assert a["subject_ref"] == "fda:oopd_page:" + key
            assert a["source"]["version"] is None
            assert (
                a["source_metadata"]["native_table"]["raw_html"] in envelope["record"]
            )
            assert (
                "HTML_does_not_echo_locator"
                in a["source_metadata"]["mapping_scope"]["identity"]
            )
            assert "protein_ref" not in a["asserted_value"]
            assert "curated" not in a["asserted_value"]
        assertions[0]["asserted_value"]["fields"].clear()
        assert envelope == before


def test_dates_blank_exclusivity_and_native_repeated_names_are_not_reconstructed():
    assertions = map_page(read())
    fields = [
        dict((f["label"], f["value"]) for f in a["asserted_value"]["fields"])
        for a in assertions
    ]
    assert fields[0]["Date Designated"] == "08/19/1997"
    assert [f["Marketing Approval Date"] for f in fields[1:]] == [
        "04/28/2006",
        "05/24/2010",
        "08/01/2014",
    ]
    assert fields[1]["Exclusivity Protected Indication*"] == ""
    assert fields[2]["Exclusivity End Date"] == "N/A"
    assert "last reported by the sponsor to OOPD" in fields[0]["Sponsor"]
    assert fields[3]["Trade Name"] == "1. Myozyme 2. Lumizyme"
    assert [a["asserted_value"]["native_ordinal"] for a in assertions] == [
        None,
        "1",
        "2",
        "3",
    ]
    no_approval = get_page("476815", client=FixtureFDAOrphanClient())
    a = map_page(no_approval)[0]
    assert a["source_metadata"]["empty_approval_tables"] == 1
    assert (
        dict((f["label"], f["value"]) for f in a["asserted_value"]["fields"])[
            "FDA Orphan Approval Status"
        ]
        == "Not FDA Approved for Orphan Indication"
    )


def test_repeated_conflicting_tables_and_labels_keep_all_occurrences():
    row = parse_page(NATIVE)["records"][1]["raw_html"]
    changed = row.replace("04/28/2006", "future-source-date")
    text = NATIVE.replace(row, row + changed, 1)
    a = map_page(read(text))
    assert len(a) == 5 and len({x["id"] for x in a}) == 5
    assert (
        a[1]["asserted_value"]["native_ordinal"]
        == a[2]["asserted_value"]["native_ordinal"]
        == "1"
    )
    assert any(
        f["value"] == "future-source-date" for f in a[2]["asserted_value"]["fields"]
    )
    field = parse_page(NATIVE)["records"][0]["fields"][0]["raw_html"]
    text = NATIVE.replace(
        field, field + field.replace("Generic Name:", "Future Native Label:"), 1
    )
    fields = map_page(read(text))[0]["asserted_value"]["fields"]
    assert len(fields) == 7 and fields[1]["label"] == "Future Native Label"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "<html>Error</html>",
        Path("temp_data/fda_orphan/search_form.html").read_bytes().decode(),
    ],
    ids=["empty", "error-page", "returned-search-form"],
)
def test_empty_error_or_returned_form_is_never_a_designation(text):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "old,new",
    [
        ("Search Orphan Drug Designations and Approvals", "Other FDA database"),
        (
            'summary="Two-column table with up to 11 rows, representing one orphan drug. Row headers label the data fields within record."',
            'summary="search page"',
        ),
        ("Date Designated:", "Other Date:"),
        ("Marketing approved:", "Other Section:"),
        ('class="resultstable"', 'class="resultstable" class="other"'),
        ('id="Generic name for Record Number 1"', 'id="one" id="two"'),
    ],
)
def test_unqualified_native_sections_or_attributes_fail(old, new):
    assert old in NATIVE
    with pytest.raises(ConnectorError):
        read(
            NATIVE.replace(old, new)
            if old == "Search Orphan Drug Designations and Approvals"
            else NATIVE.replace(old, new, 1)
        )


def test_late_table_errors_fail_before_mapping_good_earlier_records():
    row = parse_page(NATIVE)["records"][-1]["raw_html"]
    broken = row.replace("Marketing Approval Date:", "Wrong Late Field:")
    with pytest.raises(ConnectorError):
        read(NATIVE.replace(row, broken, 1))
    with pytest.raises(ConnectorError):
        read(NATIVE.replace(row, row[:-8], 1))


@pytest.mark.parametrize(
    "identifier",
    [
        "0",
        "-1",
        "0106597",
        "106597?x=1",
        "1/2",
        "١",
        "9999999999999",
        "FDA:106597",
        True,
        106597,
        None,
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_numeric_page_query_is_exact_with_or_without_digestion(identifier, skip):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_page(identifier, client=Client(), skip_digestion=skip)


def test_standard_identifier_digestion_trims_whitespace_before_page_validation():
    assert get_page(" 106597 ", client=Client())["query"] == response_query("106597")
    with pytest.raises(ConnectorError):
        get_page(" 106597 ", client=Client(), skip_digestion=True)


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "search"},
        {"query": response_query("476815")},
        {"truncated": True},
        {"truncated": None},
        {"version": "2026"},
    ],
)
def test_client_scope_revision_or_cut_is_not_resealed(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_html_gzip_hash_time_and_caller_terms(tmp_path, compressed):
    data = gzip.compress(RAW) if compressed else RAW
    path = tmp_path / ("page.html.gz" if compressed else "page.html")
    path.write_bytes(data)
    declared = {
        **metadata(),
        "retrieved_at": "2026-10-08T05:25:35+00:00",
        "terms": {"licence": "caller-note"},
    }
    client = SnapshotFDAOrphanClient(
        path, source_metadata=declared, expected_sha256=hashlib.sha256(data).hexdigest()
    )
    envelope = get_page("106597", client=client)
    assert envelope["record"].encode() == RAW
    assert envelope["retrieved_at"] == declared["retrieved_at"]
    receipt = envelope["snapshot_receipt"]
    assert receipt["source_access_observed"] is False
    assert receipt["declared_terms"] == declared["terms"]
    assert receipt["compression"] == ("gzip" if compressed else None)
    assert map_page(envelope)[0]["source_metadata"]["snapshot_receipt"] == receipt
    with pytest.raises(ConnectorError):
        get_page(
            "106597",
            client=SnapshotFDAOrphanClient(
                path, source_metadata=declared, expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "search"),
        ("query", response_query("476815")),
        ("version", "2026"),
    ],
)
def test_foreign_snapshot_binding_fails(tmp_path, key, value):
    path = tmp_path / "page.html"
    path.write_bytes(RAW)
    with pytest.raises(ConnectorError):
        get_page(
            "106597",
            client=SnapshotFDAOrphanClient(
                path, source_metadata={**metadata(), key: value}
            ),
        )


def test_missing_failed_and_malformed_access_never_mean_not_designated(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_page("106597", client=FixtureFDAOrphanClient(directory=tmp_path))

    def fail(request, **kwargs):
        raise HTTPError(
            request.full_url, 404, "blocked", {}, io.BytesIO(b"Too many requests")
        )

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_page("106597")
    path = tmp_path / "broken.html.gz"
    path.write_bytes(b"not gzip")
    with pytest.raises(ConnectorError):
        get_page(
            "106597", client=SnapshotFDAOrphanClient(path, source_metadata=metadata())
        )


def test_one_page_get_and_zero_network_replay_preserve_original_support(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    urls = []
    headers = Message()
    headers["Content-Type"] = "text/html;charset=UTF-8"

    def wire(request, **kwargs):
        urls.append(request.full_url)
        assert request.get_method() == "GET" and request.data is None
        return _http.Answer(RAW, 200, headers, "")

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "archive.sqlite")
    with archive.recording():
        first = get_page("106597")
    with archive.replaying():
        replay = get_page("106597")
    assert urls == [URL_ROOT + "106597"]
    assert first["retrieved_at"] == replay["retrieved_at"]
    assert first["download_sha256"] == replay["download_sha256"]
    assert map_page(first) == map_page(replay)
    assert first["acquisition_trace"]["records"][0]["network_attempts"] == 1
    assert replay["acquisition_trace"]["records"][0]["network_attempts"] == 0


def test_fda_terms_are_their_own_policy_with_exceptions_and_requested_credit():
    terms = source_terms()[SOURCE]
    assert terms["licence"] == "US-PD"
    assert (
        terms["statement"]
        == "https://www.fda.gov/about-fda/about-website/website-policies"
    )
    assert verdict(SOURCE, "redistribution")["verdict"] == "allowed"
    assert retention(SOURCE)["licence"] == "US-PD"
    assert any("otherwise noted" in c for c in terms["caveats"])
