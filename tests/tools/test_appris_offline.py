"""Native APPRIS occurrences, unknown revision/assembly scope and licensed replay."""

import copy
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
from sabueso.core.terms import retention, source_terms, verdict
from sabueso.mappings.appris import map_annotations
from sabueso.tools.db.appris import (
    FixtureApprisClient,
    SnapshotApprisClient,
    get_gene_annotations,
)

GENE = "ENSG00000111669"
PATH = Path("temp_data/appris/annotations__ENSG00000111669.json")


def native():
    return json.loads(PATH.read_bytes())


class Client:
    def __init__(self, payload, **context):
        self.payload = payload
        self.context = context

    def gene_annotations(self, identifier):
        return {
            "record": self.payload,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def metadata():
    return {
        "source": "APPRIS",
        "kind": "gene_annotations",
        "query": {
            "gene_id": GENE,
            "species": "homo_sapiens",
            "filters": "provider_default",
        },
        "retrieved_at": "2026-10-06T12:00:00+00:00",
    }


def test_all_native_occurrences_preserve_contradictory_transcript_context_and_no_mutation():
    envelope = get_gene_annotations(GENE, client=FixtureApprisClient())
    before = copy.deepcopy(envelope)
    assertions = map_annotations(envelope)
    assert len(assertions) == len({a["id"] for a in assertions}) == 1010
    assert [a["asserted_value"] for a in assertions] == native()
    principal = [
        a["asserted_value"]
        for a in assertions
        if a["asserted_value"]["type"] == "principal_isoform"
    ]
    assert len(principal) == 60
    repeated = [r for r in principal if r["transcript_id"] == "ENST00000396705"]
    assert len(repeated) == 5
    assert {r["reliability"] for r in repeated} == {"PRINCIPAL:1", "PRINCIPAL:2"}
    assert {r["start"] for r in repeated} == {"6867531", "6976695"}
    assert {r["transcript_name"] for r in repeated} == {"TPI1-202", "TPI1-008"}
    assert {r["length_na"] for r in repeated} == {"1351", "1231"}
    assert len({a["asserted_value"]["transcript_id"] for a in assertions}) == 21
    for i, a in enumerate(assertions):
        assert a["subject_ref"] == f"appris:homo_sapiens:{GENE}"
        assert a["source"]["version"] is None
        assert a["source_metadata"]["native_row_index"] == i
        assert (
            "no_grouping_selection"
            in a["source_metadata"]["mapping_scope"]["occurrences"]
        )
        assert (
            "assembly_and_sequence_axis_not_stated"
            in a["source_metadata"]["mapping_scope"]["coordinates"]
        )
        assert "knowledge_class" not in a
    firestar = next(
        a for a in assertions if a["asserted_value"]["source"] == "FIRESTAR"
    )
    assert firestar["source"]["name"] == "APPRIS"
    assert firestar["asserted_value"]["score"] == "0"
    assert "pep_position:" in firestar["asserted_value"]["note"]
    access = envelope["acquisition_trace"]["records"][0]
    assert access["count"] == 1010 and access["transcript_reference_count"] == 21
    assert access["retrieved_at"] is None and access["network_attempts"] == 0
    assert access["source_version"]["value"] is None
    assert access["snapshot_receipt"]["source_access_observed"] is False
    assert any(
        r["id"] == "url:https://appris.bioinfo.cnio.es/" for r in access["bibliography"]
    )
    assert any("assembly" in g for g in access["bibliography_gaps"])
    assertions[0]["asserted_value"].clear()
    assertions[0]["source_metadata"]["snapshot_receipt"].clear()
    assert envelope == before


def test_equal_occurrences_and_changed_response_support_never_collapse():
    rows = native()[:2]
    original = map_annotations(get_gene_annotations(GENE, client=Client(rows)))
    rows.append(copy.deepcopy(rows[0]))
    output = map_annotations(get_gene_annotations(GENE, client=Client(rows)))
    assert len(output) == len({a["id"] for a in output}) == 3
    assert output[0]["asserted_value"] == output[-1]["asserted_value"]
    assert original[0]["asserted_value"] == output[0]["asserted_value"]
    assert original[0]["id"] != output[0]["id"]


def test_empty_received_array_is_distinct_from_failure_or_gene_absence():
    e = get_gene_annotations(GENE, client=Client([]))
    assert e["record"] == [] and e["truncated"] is False
    assert map_annotations(e) == []
    import sabueso.tools.db.appris as m

    result = m._summarize({"record": []}, {"identifier": GENE}, False, [])
    assert result["outcome"] == "received" and result["count"] == 0
    assert "no_native_total" in result["coverage"]


def test_unknown_native_labels_and_missing_principal_annotations_remain_literal():
    row = native()[0]
    row.update(
        type="new_native_type",
        source="NEW_METHOD",
        score=".",
        annotation="UNKNOWN",
        note="pep_position:12,ligands:Cat_Site_Atl",
    )
    row.pop("reliability")
    (a,) = map_annotations(get_gene_annotations(GENE, client=Client([row])))
    assert a["asserted_value"] == row
    assert "reliability" not in a["asserted_value"]
    assert (
        "position" not in a["asserted_value"]
        and "evidence_class" not in a["asserted_value"]
    )


@pytest.mark.parametrize(
    "identifier",
    [
        "TPI1",
        "P60174",
        "ENST00000396705",
        GENE + ".1",
        GENE + "?ds=e87v22",
        "../" + GENE,
        GENE.lower(),
        "ENSG001",
        GENE + "," + GENE,
        "",
        None,
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_unsafe_or_unqualified_queries_refused_even_when_digestion_skipped(
    identifier, skip
):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_gene_annotations(identifier, client=Client([]), skip_digestion=skip)


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r.update(gene_id="ENSG00000141510"),
        lambda r: r.update(transcript_id="TPI1-202"),
        lambda r: r.update(transcript_id="ENST00000396705.1"),
        lambda r: r.pop("source"),
        lambda r: r.update(type=""),
        lambda r: r.update(start=12),
        lambda r: r.update(start="0"),
        lambda r: r.update(start="10", end="9"),
        lambda r: r.update(end="1.0"),
        lambda r: r.update(strand="unknown"),
        lambda r: r.update(frame="3"),
        lambda r: r.update(score=0),
        lambda r: r.update(note=None),
        lambda r: r.update(reliability=True),
        lambda r: r.update(extra=float("nan")),
    ],
)
def test_all_rows_are_validated_including_last_before_any_mapping(change):
    rows = native()[:2]
    change(rows[-1])
    with pytest.raises(ConnectorError):
        get_gene_annotations(GENE, client=Client(rows))
    e = {
        "source": "APPRIS",
        "kind": "gene_annotations",
        "query": metadata()["query"],
        "version": None,
        "truncated": False,
        "record": rows,
    }
    with pytest.raises(ConnectorError):
        map_annotations(e)


@pytest.mark.parametrize("payload", [None, {}, {"results": []}, [None], [1]])
def test_synthetic_wrappers_and_missing_response_are_not_empty_annotations(payload):
    with pytest.raises(ConnectorError):
        get_gene_annotations(GENE, client=Client(payload))


@pytest.mark.parametrize(
    "context", [{"version": "v48"}, {"truncated": True}, {"truncated": None}]
)
def test_client_cuts_and_unsupported_revision_declarations_refused(context):
    with pytest.raises(ConnectorError):
        get_gene_annotations(GENE, client=Client(native()[:1], **context))


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="Ensembl"),
        lambda e: e.update(kind="search"),
        lambda e: e.update(version="v48"),
        lambda e: e.update(truncated=True),
        lambda e: e["query"].update(species="mus_musculus"),
        lambda e: e["query"].update(filters="appris"),
        lambda e: e["query"].update(extra=True),
    ],
)
def test_mapping_rejects_changed_envelope_scope(change):
    e = get_gene_annotations(GENE, client=Client(native()[:1]))
    change(e)
    with pytest.raises(ConnectorError):
        map_annotations(e)


def test_query_bound_gzip_snapshot_checks_original_bytes_and_copies_declarations(
    tmp_path,
):
    raw = gzip.compress(PATH.read_bytes())
    path = tmp_path / "gene.json.gz"
    path.write_bytes(raw)
    m = metadata()
    client = SnapshotApprisClient(
        path, source_metadata=m, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    m["query"]["gene_id"] = "ENSG00000141510"
    e = get_gene_annotations(GENE, client=client)
    assert e["record"] == native()
    assert e["retrieved_at"] == metadata()["retrieved_at"]
    receipt = e["snapshot_receipt"]
    assert receipt["source_access_observed"] is False
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (
        receipt["compression"] == "gzip"
        and receipt["digest_verification"] == "matched_caller_digest"
    )
    assert e["acquisition_trace"]["records"][0]["network_attempts"] == 0
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_gene_annotations(
            GENE,
            client=SnapshotApprisClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m.update(source="Ensembl"),
        lambda m: m.update(kind="search"),
        lambda m: m.update(version="v48"),
        lambda m: m["query"].update(gene_id="ENSG00000141510"),
        lambda m: m["query"].update(species="mus_musculus"),
        lambda m: m["query"].update(filters="appris"),
    ],
)
def test_supplied_source_and_query_declarations_must_match(change):
    m = metadata()
    change(m)
    with pytest.raises(ConnectorError):
        get_gene_annotations(GENE, client=SnapshotApprisClient(PATH, source_metadata=m))


@pytest.mark.parametrize(
    "document", ['[{"gene_id":"a","gene_id":"b"}]', "[NaN]", "[1e999]", "{}"]
)
def test_bad_native_json_fails_instead_of_becoming_an_empty_result(tmp_path, document):
    path = tmp_path / "bad.json"
    path.write_text(document, encoding="utf-8", newline="")
    with pytest.raises(ConnectorError):
        get_gene_annotations(
            GENE, client=SnapshotApprisClient(path, source_metadata=metadata())
        )


def test_missing_fixture_is_unavailable_without_absence_claim(tmp_path):
    with pytest.raises(ConnectorError) as exc:
        get_gene_annotations(GENE, client=FixtureApprisClient(tmp_path))
    assert exc.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("code", [404, 500])
def test_http_errors_remain_failed_access(monkeypatch, code):
    import sabueso.tools.db.appris as m

    def fail(url, **kwargs):
        raise HTTPError(url, code, "failure", None, None)

    monkeypatch.setattr(m, "urlopen", fail)
    with pytest.raises(ConnectorError) as exc:
        get_gene_annotations(GENE)
    assert exc.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_single_get_archive_replay_retains_times_and_never_queries_method_or_sequence_links(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http as http

    calls = []

    class Answer(io.BytesIO):
        status = 200
        headers = Message()
        headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        calls.append(request.full_url)
        return Answer(PATH.read_bytes())

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "appris.db")
    with archive.recording():
        first = get_gene_annotations(GENE)

    def forbidden(*args, **kwargs):
        pytest.fail("Mapping/replay acquired linked support")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_gene_annotations(GENE)
    assert calls == [
        f"https://apprisws.bioinfo.cnio.es/rest/exporter/id/homo_sapiens/{GENE}?format=json"
    ]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_annotations(first) == map_annotations(second)
    a, b = [e["acquisition_trace"]["records"][0] for e in (first, second)]
    assert a["network_attempts"] == a["received_responses"] == 1
    assert b["network_attempts"] == 0 and b["access"] == "replay"
    assert a["response_identity"] == b["response_identity"]


def test_appris_noncommercial_share_alike_obligations_survive_terms_and_archives():
    t = source_terms()["APPRIS"]
    assert t["licence"] == "CC-BY-NC-SA-4.0"
    assert t["statement"] == "https://appris.bioinfo.cnio.es/partials/license.html"
    assert verdict("APPRIS", "commercial_product")["verdict"] == "restricted"
    v = verdict("APPRIS", "derived_dataset")
    assert v["verdict"] == "allowed"
    assert "share_alike" in v["obligations"] and "attribution" in v["obligations"]
    assert retention("APPRIS")["conditions"] == [
        "attribution",
        "share_alike",
        "non_commercial",
    ]
