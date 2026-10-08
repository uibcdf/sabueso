"""Native mapped-gene page boundaries, original statistics and source-scoped replay."""

import copy
import gzip
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms
from sabueso.mappings.gwas_catalog import URL, map_associations, response_query
from sabueso.tools.db.gwas_catalog import (
    FixtureGwasCatalogClient,
    SnapshotGwasCatalogClient,
    get_associations,
)

PATH = Path("temp_data/gwas_catalog/associations__HBB__size2__page0.json")


def native():
    return json.loads(PATH.read_bytes())


class Client:
    def __init__(self, record, **context):
        self.record, self.context = record, context

    def associations(self, identifier, limit, page):
        return {
            "record": self.record,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(record, **context):
    return get_associations("HBB", limit=2, client=Client(record, **context))


def metadata():
    return {
        "source": "GWAS Catalog",
        "kind": "mapped_gene_associations",
        "query": response_query("HBB", 2, 0),
    }


def page_link(page, **query):
    return {"href": URL + "?" + urlencode({**response_query("HBB", 2, page), **query})}


def test_native_page_keeps_independent_studies_and_underflow_support_without_projection():
    raw = PATH.read_bytes()
    assert len(raw) == 2485
    assert (
        hashlib.sha256(raw).hexdigest()
        == "14f63516b1a620e3e41ddbd681acf507bc88f5685229103ece6c61a172b05786"
    )
    e = get_associations("HBB", limit=2, client=FixtureGwasCatalogClient())
    before = copy.deepcopy(e)
    a = map_associations(e)
    assert len(a) == 2 and e["truncated"] is True and e["record"] == native()
    assert [s["asserted_value"]["accession_id"] for s in a] == [
        "GCST90476345",
        "GCST90480668",
    ]
    assert a[0]["asserted_value"]["pvalue_mantissa"] == 1
    assert a[0]["asserted_value"]["pvalue_exponent"] == -323
    assert a[0]["asserted_value"]["p_value"] == 1e-323
    assert a[0]["asserted_value"]["beta"] == "3.451 unit decrease"
    assert a[0]["asserted_value"]["risk_frequency"] == "0.9997"
    for s, row in zip(a, native()["_embedded"]["associations"]):
        assert s["asserted_value"] == s["source_metadata"]["native_association"] == row
        assert s["subject_ref"] == f"gwas:association:{row['association_id']}"
        assert s["acquisition"] == {"method": "database"}
        assert s["source"]["version"] is s["retrieved_at"] is None
        assert row["mapped_genes"] == ["HBB"] and row["pubmed_id"] == "39024449"
        assert s["source_metadata"]["page"]["totalElements"] == 279
        assert s["source_metadata"]["native_page_links"] == e["record"]["_links"]
        assert not any(
            k in row for k in ("protein_ref", "evidence_class", "assembly", "unit")
        )
    trace = e["acquisition_trace"]["records"]
    assert (
        len(trace) == 1 and trace[0]["count"] == 2 and trace[0]["network_attempts"] == 0
    )
    assert trace[0]["truncated"] is True
    a[0]["asserted_value"]["snp_allele"].clear()
    a[0]["source_metadata"]["native_association"].clear()
    assert e == before


def test_received_empty_page_declares_zero_filter_hits_without_gene_absence():
    path = PATH.with_name("associations__TPI1__size2__page0.json")
    assert len(path.read_bytes()) == 198
    assert (
        hashlib.sha256(path.read_bytes()).hexdigest()
        == "4dde3abd2cc12114cc229c93e6acb95e07d1467d2ebee03b3c18376ae1df92b7"
    )
    e = get_associations("TPI1", limit=2, client=FixtureGwasCatalogClient())
    assert map_associations(e) == [] and e["truncated"] is False
    assert "_embedded" not in e["record"]
    assert e["acquisition_trace"]["records"][0]["outcome"] == "empty"


def test_mixed_case_official_symbol_is_preserved_without_uppercasing_native_context():
    p = native()
    for row in p["_embedded"]["associations"]:
        row["mapped_genes"] = ["C11orf74"]
    for link in p["_links"].values():
        link["href"] = link["href"].replace("mapped_gene=HBB", "mapped_gene=C11orf74")
    e = get_associations("C11orf74", limit=2, client=Client(p))
    assert e["query"]["mapped_gene"] == "C11orf74"
    assert map_associations(e)[0]["asserted_value"]["mapped_genes"] == ["C11orf74"]


def test_duplicate_association_ids_conflicting_values_and_native_future_context_survive():
    p = native()
    rows = p["_embedded"]["associations"]
    rows[1] = copy.deepcopy(rows[0])
    a = map_associations(read(p))
    assert a[0]["id"] != a[1]["id"] and a[0]["subject_ref"] == a[1]["subject_ref"]
    rows[1].update(
        beta="3.451 unit increase",
        risk_frequency="NR",
        future={"literal": None},
        multi_snp_haplotype=True,
    )
    rows[1]["mapped_genes"] = ["OTHER", "HBB", "HBB"]
    rows[1]["snp_allele"].append({"rs_id": "rs2", "effect_allele": "T", "future": None})
    rows[1]["efo_traits"] *= 2
    a = map_associations(read(p))
    assert a[0]["asserted_value"]["beta"] != a[1]["asserted_value"]["beta"]
    assert [s["asserted_value"] for s in a] == rows


def test_null_missing_empty_and_zero_statistics_are_not_replaced_or_recomputed():
    p = native()
    row = p["_embedded"]["associations"][0]
    row.update(
        p_value=0.0,
        pvalue_exponent=-999,
        pvalue_mantissa=1,
        ci_lower=0,
        ci_upper=None,
        range="",
        risk_frequency=None,
    )
    row.pop("beta")
    a = map_associations(read(p))[0]["asserted_value"]
    assert a == row and a["p_value"] == 0 and a["pvalue_exponent"] == -999
    assert a["ci_lower"] == 0 and a["ci_upper"] is None and "beta" not in a
    assert a["range"] == "" and a["risk_frequency"] is None


def test_manual_page_keeps_distinct_query_identity_and_complete_page_can_be_received():
    p = native()
    p["page"]["number"] = 1
    p["_links"].update(self=page_link(1), next=page_link(2), prev=page_link(0))
    first = map_associations(read(native()))
    e = get_associations("HBB", limit=2, page=1, client=Client(p))
    a = map_associations(e)
    assert (
        a[0]["asserted_value"] == first[0]["asserted_value"]
        and a[0]["id"] != first[0]["id"]
    )
    assert a[0]["source_metadata"]["page"]["number"] == 1 and e["truncated"] is True
    p = native()
    p["page"].update(totalElements=2, totalPages=1)
    p["_links"].pop("next")
    p["_links"]["last"] = page_link(0)
    assert read(p)["truncated"] is False


def test_last_and_beyond_range_pages_never_claim_full_coverage():
    p = native()
    p["page"]["number"] = 139
    p["_embedded"]["associations"].pop()
    p["_links"].update(self=page_link(139), prev=page_link(138))
    p["_links"].pop("next")
    assert (
        get_associations("HBB", limit=2, page=139, client=Client(p))["truncated"]
        is True
    )
    p["page"]["number"] = 140
    p.pop("_embedded")
    p["_links"].update(self=page_link(140), prev=page_link(139))
    e = get_associations("HBB", limit=2, page=140, client=Client(p))
    assert map_associations(e) == [] and e["truncated"] is True


@pytest.mark.parametrize("value", ["hbb", "HBB1", "HBB.1", "prefixHBB", " HBB", "HBB "])
def test_similar_symbols_and_whitespace_in_source_rows_do_not_match(value):
    p = native()
    p["_embedded"]["associations"][1]["mapped_genes"] = [value]
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "key,value",
    [
        ("association_id", True),
        ("association_id", 0),
        ("association_id", "226316756"),
        ("accession_id", "HBB"),
        ("mapped_genes", "HBB"),
        ("reported_trait", [None]),
        ("locations", [11]),
        ("snp_effect_allele", {}),
        ("pvalue_exponent", -323.0),
        ("pvalue_mantissa", True),
        ("p_value", float("nan")),
        ("p_value", "1e-323"),
        ("ci_lower", True),
        ("beta", 3.451),
        ("risk_frequency", 0.9997),
        ("multi_snp_haplotype", 0),
        ("snp_interaction", "false"),
        ("efo_traits", ["EFO_0004305"]),
        ("snp_allele", [{"rs_id": "rs1"}]),
        ("future", float("inf")),
        ("_links", {}),
    ],
)
def test_full_native_row_validation_precedes_mapping(key, value):
    p = native()
    p["_embedded"]["associations"][1][key] = value
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "key,value",
    [
        ("size", 3),
        ("size", True),
        ("number", 1),
        ("number", 0.0),
        ("totalElements", 1),
        ("totalElements", -1),
        ("totalPages", 139),
        ("totalPages", None),
    ],
)
def test_native_page_metadata_is_required_and_matches_received_coverage(key, value):
    p = native()
    p["page"][key] = value
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "link",
    [
        page_link(0),
        page_link(2),
        page_link(1, mapped_gene="TPI1"),
        page_link(1, extended_geneset="true"),
        page_link(1, size=20),
        {
            "href": "http://www.ebi.ac.uk/gwas/rest/api/v2/associations?mapped_gene=HBB&extended_geneset=false&page=1&size=2"
        },
        {
            "href": "https://other.example/associations?mapped_gene=HBB&extended_geneset=false&page=1&size=2"
        },
        {"href": page_link(1)["href"] + "&page=2"},
        {"href": page_link(1)["href"] + "#other"},
        {"href": page_link(1)["href"] + "&sort=p_value"},
    ],
)
def test_continuation_links_cannot_cycle_or_change_host_query_or_gene_set(link):
    p = native()
    p["_links"]["next"] = link
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_next",
        "missing_self",
        "missing_rows",
        "empty_rows",
        "array_page",
        "unknown_embedded",
        "wrong_self",
        "wrong_last",
        "prev_first",
    ],
)
def test_broken_hal_scope_is_not_a_valid_empty_or_complete_page(mutation):
    p = native()
    if mutation.startswith("missing_") and mutation != "missing_rows":
        p["_links"].pop(mutation.removeprefix("missing_"))
    elif mutation == "missing_rows":
        p.pop("_embedded")
    elif mutation == "empty_rows":
        p["_embedded"]["associations"] = []
    elif mutation == "array_page":
        p["page"] = []
    elif mutation == "unknown_embedded":
        p["_embedded"] = {"other": []}
    elif mutation == "wrong_self":
        p["_links"]["self"] = page_link(1)
    elif mutation == "wrong_last":
        p["_links"]["last"] = page_link(140)
    elif mutation == "prev_first":
        p["_links"]["prev"] = page_link(0)
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize("payload", [None, {}, [], {"detail": "blocked"}, {"page": {}}])
def test_non_native_or_application_error_body_is_not_a_negative(payload):
    with pytest.raises(ConnectorError):
        read(payload)


@pytest.mark.parametrize(
    "arguments",
    [
        {"identifier": "hbb"},
        {"identifier": "HBB?x"},
        {"identifier": "HBB/"},
        {"identifier": "HBB TPI1"},
        {"limit": 0},
        {"limit": 501},
        {"limit": True},
        {"limit": 2.0},
        {"page": -1},
        {"page": True},
        {"page": 0.0},
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_unsafe_query_or_bad_page_limit_never_reaches_client(arguments, skip):
    class Forbidden:
        def associations(self, *args):
            pytest.fail("Invalid request reached client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_associations(
            **{"identifier": "HBB", "limit": 2, **arguments},
            client=Forbidden(),
            skip_digestion=skip,
        )


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "summary_statistics"},
        {"version": "2.0"},
        {"truncated": False},
        {"truncated": None},
        {"query": {**response_query("HBB", 2, 0), "extended_geneset": "true"}},
        {"query": {**response_query("HBB", 2, 0), "page": 0.0}},
    ],
)
def test_client_context_cannot_override_native_query_revision_or_cut(context):
    with pytest.raises(ConnectorError):
        read(native(), **context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "summary_statistics"),
        ("version", "2.0"),
        ("truncated", False),
        ("truncated", None),
        ("query", {**response_query("HBB", 2, 0), "extended_geneset": "true"}),
    ],
)
def test_mapping_refuses_wrong_envelope_context(key, value):
    e = read(native())
    e[key] = value
    with pytest.raises(ConnectorError):
        map_associations(e)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_snapshot_preserves_original_bytes_time_terms_and_no_remote_credit(
    tmp_path, compressed
):
    raw = PATH.read_bytes()
    raw = gzip.compress(raw) if compressed else raw
    p = tmp_path / ("native.json.gz" if compressed else "native.json")
    p.write_bytes(raw)
    m = metadata()
    m.update(
        retrieved_at="2026-10-07T12:00:00+00:00",
        terms={"licence": "NO-OWN-RESTRICTIONS"},
    )
    client = SnapshotGwasCatalogClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    m["query"]["mapped_gene"] = "TPI1"
    e = get_associations("HBB", limit=2, client=client)
    assert e["record"] == native() and e["retrieved_at"] == "2026-10-07T12:00:00+00:00"
    receipt = e["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["declared_terms"] == {"licence": "NO-OWN-RESTRICTIONS"}
    assert receipt["source_access_observed"] is False
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_associations(
            "HBB",
            limit=2,
            client=SnapshotGwasCatalogClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "summary_statistics"),
        ("version", "2.0"),
        ("query", response_query("HBB", 2, 1)),
        ("query", {**response_query("HBB", 2, 0), "page": 0.0}),
    ],
)
def test_snapshot_scope_must_match_exact_standard_gene_query(tmp_path, key, value):
    p = tmp_path / "native.json"
    p.write_bytes(PATH.read_bytes())
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get_associations(
            "HBB", limit=2, client=SnapshotGwasCatalogClient(p, source_metadata=m)
        )


@pytest.mark.parametrize(
    "raw",
    [b'{"page":{},"page":{}}', b'{"extra":NaN}', b"\xff", b"<html>blocked</html>"],
)
def test_malformed_original_json_fails_explicitly(tmp_path, raw):
    p = tmp_path / "native.json"
    p.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_associations(
            "HBB",
            limit=2,
            client=SnapshotGwasCatalogClient(p, source_metadata=metadata()),
        )


def test_unavailable_fixture_and_snapshot_are_not_empty(tmp_path):
    for c, size in [
        (FixtureGwasCatalogClient(tmp_path), 2),
        (FixtureGwasCatalogClient(), 20),
        (
            SnapshotGwasCatalogClient(
                tmp_path / "missing.json", source_metadata=metadata()
            ),
            2,
        ),
    ]:
        with pytest.raises(ConnectorError):
            get_associations("HBB", limit=size, client=c)


@pytest.mark.parametrize("status", [404, 429, 503])
def test_failed_http_is_not_a_native_empty_page(monkeypatch, status):
    from sabueso.tools.db import _http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, status, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_associations("HBB", limit=2)


def test_one_get_archive_replay_never_follows_next_study_or_variant(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        r = io.BytesIO(PATH.read_bytes())
        r.status = 200
        r.headers = Message()
        r.headers["Content-Type"] = "application/json"
        return r

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "gwas.db")
    with archive.recording():
        first = get_associations("HBB", limit=2)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay fetched continuation or support")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_associations("HBB", limit=2)
    assert len(calls) == 1 and calls[0].startswith(URL)
    assert parse_qs(urlsplit(calls[0]).query) == {
        k: [str(v)] for k, v in response_query("HBB", 2, 0).items()
    }
    assert (
        first["record"] == second["record"] == native()
        and first["retrieved_at"] == second["retrieved_at"]
    )
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_associations(first) == map_associations(second)
    assert first["acquisition_trace"]["records"][0]["network_attempts"] == 1
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["GWAS Catalog"]["licence"] == "NO-OWN-RESTRICTIONS"
