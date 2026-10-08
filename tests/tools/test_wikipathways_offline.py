"""Exact native pathway xrefs, heterogeneous cells, coverage and original replay."""

import copy
import gzip
import hashlib
import io
import json
from email.message import Message
from functools import lru_cache
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import retention, source_terms
from sabueso.mappings.wikipathways import map_pathway_cross_references, response_query
from sabueso.tools.db.wikipathways import (
    URL,
    FixtureWikiPathwaysClient,
    SnapshotWikiPathwaysClient,
    get_pathways_by_xref,
)

PATH = Path("temp_data/wikipathways/findPathwaysByXref.json")
TARGET = "uniprot:P60174"


@lru_cache
def native():
    return json.loads(PATH.read_bytes())


def small():
    return {"pathwayInfo": copy.deepcopy(native()["pathwayInfo"][:2])}


class Client:
    def __init__(self, payload, **context):
        self.payload, self.context = payload, context

    def pathway_cross_references(self, identifier):
        return {
            "record": self.payload,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def metadata():
    return {
        "source": "WikiPathways",
        "kind": "pathway_cross_references",
        "query": response_query(TARGET),
        "retrieved_at": "2026-10-06T12:00:00+00:00",
    }


def test_full_native_export_retains_exact_pathways_revisions_and_original_scope():
    b = PATH.read_bytes()
    assert len(b) == 12084935
    assert (
        hashlib.sha256(b).hexdigest()
        == "09da862b2d2dc08c98c0a0d98640892c076668d5ad251ee373502dcf89bbce22"
    )
    e = get_pathways_by_xref(TARGET, client=FixtureWikiPathwaysClient())
    before = copy.deepcopy(e)
    a = map_pathway_cross_references(e)
    assert [s["asserted_value"]["id"] for s in a] == [
        "WP143",
        "WP1946",
        "WP2456",
        "WP4018",
        "WP4628",
        "WP5178",
        "WP534",
        "WP5355",
        "WP5570",
    ]
    assert len({s["id"] for s in a}) == 9
    assert e["record"] == native() and len(e["record"]["pathwayInfo"]) == 2218
    for s in a:
        assert s["subject_ref"] == "wikipathways:" + s["asserted_value"]["id"]
        assert s["source_metadata"]["query_xref"] == TARGET
        assert (
            s["source_metadata"]["native_pathway_revision"]
            == s["asserted_value"]["revision"]
        )
        assert s["source"]["version"] is None and s["retrieved_at"] is None
        assert "knowledge_class" not in s and "protein_ref" not in s["asserted_value"]
    assert e["acquisition_trace"]["records"][0]["count"] == 9
    assert e["acquisition_trace"]["records"][0]["received_export_rows"] == 2218
    assert e["snapshot_receipt"]["document_sha256"] == hashlib.sha256(b).hexdigest()
    assert e == before
    a[0]["asserted_value"].clear()
    assert e == before


def test_native_misplaced_prefixes_are_kept_in_original_field_without_repair():
    row = next(r for r in native()["pathwayInfo"] if r["id"] == "WP1584")
    assert "uniprot:Q05655" in row["wikidata"]
    p = {"pathwayInfo": [copy.deepcopy(row)]}
    a = map_pathway_cross_references(
        get_pathways_by_xref("uniprot:Q05655", client=Client(p))
    )
    assert len(a) == 1 and a[0]["asserted_value"] == row
    assert {
        m["field"] for m in a[0]["source_metadata"]["matched_xref_occurrences"]
    } == {"wikidata"}
    assert "hgnc.symbol:PRKCD" in a[0]["asserted_value"]["uniprot"]


def test_substrings_case_namespaces_names_and_version_stripping_are_not_joins():
    p = small()
    row = p["pathwayInfo"][0]
    row["name"] = "P60174"
    row["description"] = TARGET
    row["uniprot"] = "uniprot:P601740;uniprot:P60174-2;uniprot:p60174;other:P60174"
    row["ensembl"] = "ensembl:ENSG00000111669.5"
    row["hgnc"] = "hgnc.symbol:TPI1"
    p["pathwayInfo"] = [row]
    assert (
        map_pathway_cross_references(get_pathways_by_xref(TARGET, client=Client(p)))
        == []
    )
    assert (
        map_pathway_cross_references(
            get_pathways_by_xref("ensembl:ENSG00000111669", client=Client(p))
        )
        == []
    )
    assert (
        len(
            map_pathway_cross_references(
                get_pathways_by_xref("ensembl:ENSG00000111669.5", client=Client(p))
            )
        )
        == 1
    )
    assert (
        len(
            map_pathway_cross_references(
                get_pathways_by_xref("uniprot:P60174-2", client=Client(p))
            )
        )
        == 1
    )


def test_alias_positions_repeated_pathways_species_and_conflicts_survive():
    p = small()
    row = p["pathwayInfo"][0]
    row["uniprot"] = "uniprot:Q05655;" + TARGET + ", ; " + TARGET
    row["ensembl"] = ""  # Native blank aliases/free text elsewhere are legal too.
    row["additional_native_context"] = {"original": True}
    p["pathwayInfo"] = [row, copy.deepcopy(row), copy.deepcopy(row)]
    p["pathwayInfo"][2]["species"] = "Different native species"
    p["pathwayInfo"][2]["revision"] = "2026-10-06"
    a = map_pathway_cross_references(get_pathways_by_xref(TARGET, client=Client(p)))
    assert len(a) == len({s["id"] for s in a}) == 3
    assert a[0]["asserted_value"] == a[1]["asserted_value"]
    assert len({s["subject_ref"] for s in a}) == 1
    assert a[2]["asserted_value"]["species"] == "Different native species"
    assert a[0]["source_metadata"]["matched_xref_occurrences"] == [
        {
            "field": "uniprot",
            "group_index": 0,
            "alias_index": 1,
            "native_token": TARGET,
        },
        {
            "field": "uniprot",
            "group_index": 1,
            "alias_index": 1,
            "native_token": " " + TARGET,
        },
    ]


@pytest.mark.parametrize(
    "identifier",
    [
        "P60174",
        "TPI1",
        "hgnc.symbol:TPI1",
        "UNIPROT:P60174",
        "uniprot:p60174",
        "uniprot:P60174,uniprot:Q05655",
        "uniprot:P60174/other",
        "uniprot:P60174-0",
        "ensembl:ENSG00000111669.",
        "ncbigene:0",
        "wikidata:q1",
        "chebi:CHEBI:15377",
        "inchikey:short",
        None,
        [TARGET],
    ],
)
def test_exact_supported_namespaced_identifier_is_required(identifier):
    with pytest.raises((ConnectorError, ArgumentError)):
        get_pathways_by_xref(identifier, client=Client(small()))


def test_outer_argument_digestion_does_not_override_backend_exactness():
    assert get_pathways_by_xref(" " + TARGET + " ", client=Client(small()))[
        "query"
    ] == response_query(TARGET)
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(
            " " + TARGET + " ", client=Client(small()), skip_digestion=True
        )


@pytest.mark.parametrize(
    "identifier,field",
    [
        ("ensembl:ENSG00000111669", "ensembl"),
        ("ncbigene:7167", "ncbigene"),
        ("wikidata:Q1", "wikidata"),
        ("chebi:15377", "chebi"),
        ("inchikey:XLYOFNOQVPJJNP-UHFFFAOYSA-N", "inchikey"),
    ],
)
def test_other_literal_namespaces_do_not_infer_equivalence(identifier, field):
    p = small()
    p["pathwayInfo"][0][field] = identifier
    a = map_pathway_cross_references(get_pathways_by_xref(identifier, client=Client(p)))
    assert len(a) == 1 and a[0]["source_metadata"]["query_xref"] == identifier


@pytest.mark.parametrize(
    "payload", [None, [], {}, {"pathwayInfo": {}}, {"pathwayInfo": [None]}]
)
def test_native_export_shape_is_required(payload):
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(TARGET, client=Client(payload))


@pytest.mark.parametrize(
    "key,value",
    [
        ("id", "WP0"),
        ("url", "https://other.invalid/WP10"),
        ("url", "https://www.wikipathways.org/instance/WP9999"),
        ("species", ""),
        ("revision", "2026-02-30"),
        ("revision", "latest"),
        ("uniprot", None),
        ("hgnc", []),
        ("extra", float("nan")),
    ],
)
def test_all_rows_are_validated_before_selection(key, value):
    p = small()
    p["pathwayInfo"][1][key] = value
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(TARGET, client=Client(p))


def test_not_listed_received_empty_and_failed_access_are_distinct():
    e = get_pathways_by_xref(TARGET, client=Client({"pathwayInfo": []}))
    assert map_pathway_cross_references(e) == []
    e = get_pathways_by_xref("uniprot:P00000", client=FixtureWikiPathwaysClient())
    assert map_pathway_cross_references(e) == []
    assert (
        e["acquisition_trace"]["records"][0]["native_result_declaration"]
        == "not_listed_in_received_export"
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "gpml"),
        ("query", {"xref": TARGET}),
        ("version", "2026-10-06"),
        ("truncated", True),
        ("truncated", None),
    ],
)
def test_mapping_rechecks_query_scope_and_revision_is_not_guessed(key, value):
    e = get_pathways_by_xref(TARGET, client=Client(small()))
    e[key] = value
    with pytest.raises(ConnectorError):
        map_pathway_cross_references(e)


@pytest.mark.parametrize(
    "context", [{"version": "2026-10-06"}, {"truncated": True}, {"truncated": None}]
)
def test_lookup_rejects_invented_dataset_revision_and_unknown_cuts(context):
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(TARGET, client=Client(small(), **context))


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_snapshot_hash_time_metadata_and_no_new_access_credit(
    tmp_path, compressed
):
    raw = json.dumps(small()).encode()
    raw = gzip.compress(raw) if compressed else raw
    p = tmp_path / ("native.json.gz" if compressed else "native.json")
    p.write_bytes(raw)
    m = metadata()
    m["terms"] = {"licence": "CC0-1.0"}
    c = SnapshotWikiPathwaysClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    m["query"]["xref"] = "uniprot:Q05655"
    e = get_pathways_by_xref(TARGET, client=c)
    assert e["record"] == small() and e["retrieved_at"] == metadata()["retrieved_at"]
    assert e["snapshot_receipt"]["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert e["snapshot_receipt"]["source_access_observed"] is False
    assert e["snapshot_receipt"]["declared_terms"] == {"licence": "CC0-1.0"}
    assert e["acquisition_trace"]["records"][0]["network_attempts"] == 0
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_pathways_by_xref(
            TARGET,
            client=SnapshotWikiPathwaysClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "gpml"),
        ("query", response_query("uniprot:Q05655")),
        ("version", "2026-10-06"),
    ],
)
def test_supplied_snapshot_binding_is_exact(tmp_path, key, value):
    p = tmp_path / "native.json"
    p.write_text(json.dumps(small()))
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(
            TARGET, client=SnapshotWikiPathwaysClient(p, source_metadata=m)
        )


@pytest.mark.parametrize(
    "raw",
    [
        b'{"pathwayInfo":[],"pathwayInfo":[]}',
        b'{"pathwayInfo":[],"extra":NaN}',
        b"\xff",
        b"<html>blocked</html>",
    ],
)
def test_invalid_original_json_bytes_fail_explicitly(tmp_path, raw):
    p = tmp_path / "native.json"
    p.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(
            TARGET, client=SnapshotWikiPathwaysClient(p, source_metadata=metadata())
        )


def test_missing_fixture_or_supplied_file_and_bad_gzip_are_not_empty(tmp_path):
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(TARGET, client=FixtureWikiPathwaysClient(tmp_path))
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(
            TARGET,
            client=SnapshotWikiPathwaysClient(
                tmp_path / "missing.json", source_metadata=metadata()
            ),
        )
    p = tmp_path / "native.json.gz"
    p.write_bytes(b"not gzip")
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(
            TARGET, client=SnapshotWikiPathwaysClient(p, source_metadata=metadata())
        )


@pytest.mark.parametrize("status", [404, 429, 503])
def test_failed_http_is_not_a_source_negative(monkeypatch, status):
    from sabueso.tools.db import _http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, status, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_pathways_by_xref(TARGET)


def test_one_get_archive_replay_retains_original_bytes_time_and_identity(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(json.dumps(small()).encode())
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "application/json"
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "wp.db")
    with archive.recording():
        first = get_pathways_by_xref(TARGET)

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Replay must not fetch linked GPML, pathway pages or publications."
        )

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_pathways_by_xref(TARGET)
    assert calls == [URL]
    assert first["record"] == second["record"] == small()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert first["download_sha256"] == second["download_sha256"]
    assert map_pathway_cross_references(first) == map_pathway_cross_references(second)
    observed = first["acquisition_trace"]["records"][0]
    replayed = second["acquisition_trace"]["records"][0]
    assert observed["network_attempts"] == observed["received_responses"] == 1
    assert replayed["network_attempts"] == 0 and replayed["access"] == "replay"
    assert observed["response_identity"] == replayed["response_identity"]
    assert source_terms()["WikiPathways"]["licence"] == "CC0-1.0"
    assert retention("WikiPathways")["keep"] == "yes"
