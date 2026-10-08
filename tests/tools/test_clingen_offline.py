"""ClinGen native export scope, independent classifications and licensed replay."""

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
from sabueso.mappings.clingen import COLUMNS, map_gene_validity, parse_export
from sabueso.tools.db.clingen import (
    FixtureClinGenClient,
    SnapshotClinGenClient,
    get_gene_validity,
)

PATH = Path("temp_data/clingen/gene_validity.csv")
GENE = "HGNC:1100"


def native():
    return PATH.read_bytes().decode("utf-8")


class Client:
    def __init__(self, text, **context):
        self.text = text
        self.context = context

    def gene_validity(self, identifier):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def metadata():
    return {
        "source": "ClinGen",
        "kind": "gene_validity",
        "query": {"hgnc_id": GENE, "dataset": "gene_disease_validity"},
        "retrieved_at": "2026-10-06T12:00:00+00:00",
    }


def small_export():
    """Authored counterexample input retains native preamble and two BRCA1 rows."""
    rows = list(csv.reader(io.StringIO(native())))
    return rows[:6] + [r for r in rows[6:] if r[1] == GENE]


def encode(rows):
    stream = io.StringIO(newline="")
    csv.writer(stream, quoting=csv.QUOTE_ALL, lineterminator="\n").writerows(rows)
    return stream.getvalue()


def test_native_brca1_declarations_preserve_two_diseases_and_inheritance_contexts():
    envelope = get_gene_validity(GENE, client=FixtureClinGenClient())
    before = copy.deepcopy(envelope)
    assertions = map_gene_validity(envelope)
    assert envelope["record"] == native()
    assert len(assertions) == len({a["id"] for a in assertions}) == 2
    fields = [a["asserted_value"] for a in assertions]
    assert {r["DISEASE ID (MONDO)"] for r in fields} == {
        "MONDO:0700268",
        "MONDO:0054748",
    }
    assert {r["MOI"] for r in fields} == {"AD", "AR"}
    assert {r["SOP"] for r in fields} == {"SOP7", "SOP10"}
    assert {r["CLASSIFICATION"] for r in fields} == {"Definitive"}
    assert fields == [
        r["fields"]
        for r in parse_export(native())["rows"]
        if r["fields"]["GENE ID (HGNC)"] == GENE
    ]
    for a in assertions:
        assert a["subject_ref"] == "clingen:HGNC:1100"
        assert a["source"]["version"] is None
        assert a["source_metadata"]["received_export_rows"] == 3702
        assert a["source_metadata"]["native_file_created"] == "2026-10-06"
        assert "knowledge_class" not in a and "protein_ref" not in a["asserted_value"]
        assert tuple(a["asserted_value"]) == COLUMNS
    assert before == envelope
    assertions[0]["asserted_value"].clear()
    assert before == envelope
    access = envelope["acquisition_trace"]["records"][0]
    assert access["count"] == 2 and access["received_export_rows"] == 3702
    assert access["network_attempts"] == 0 and access["retrieved_at"] is None
    assert access["snapshot_receipt"]["source_access_observed"] is False


def test_legacy_report_namespace_and_unknown_classification_timezone_survive():
    envelope = get_gene_validity("HGNC:428", client=FixtureClinGenClient())
    assertions = map_gene_validity(envelope)
    legacy = next(
        a for a in assertions if "CGGCIEX:" in a["asserted_value"]["ONLINE REPORT"]
    )
    assert legacy["asserted_value"]["CLASSIFICATION DATE"] == "2017-02-10T00:00:00"
    assert legacy["asserted_value"]["SOP"] == "SOP4"
    assert legacy["retrieved_at"] is None
    assert legacy["source"]["version"] is None


def test_not_listed_is_distinct_from_explicit_no_known_disease_relationship():
    envelope = get_gene_validity("HGNC:12009", client=FixtureClinGenClient())
    assert map_gene_validity(envelope) == []
    access = envelope["acquisition_trace"]["records"][0]
    assert access["outcome"] == "not_found" and access["received_export_rows"] == 3702
    assert access["native_result_declaration"] == "not_listed_in_received_export"
    row = next(
        r["fields"]
        for r in parse_export(native())["rows"]
        if r["fields"]["CLASSIFICATION"] == "No Known Disease Relationship"
    )
    assertions = map_gene_validity(
        get_gene_validity(row["GENE ID (HGNC)"], client=FixtureClinGenClient())
    )
    assert any(
        a["asserted_value"]["CLASSIFICATION"] == "No Known Disease Relationship"
        for a in assertions
    )


def test_repeated_conflicting_occurrences_unknown_labels_and_quoted_text_are_not_collapsed():
    rows = small_export()
    repeated = copy.deepcopy(rows[6])
    repeated[2] = 'Disease, "quoted"\nsecond line'
    repeated[4:7] = [
        "native future inheritance",
        "native future SOP",
        "native future classification",
    ]
    rows.append(repeated)
    assertions = map_gene_validity(get_gene_validity(GENE, client=Client(encode(rows))))
    assert len(assertions) == len({a["id"] for a in assertions}) == 3
    assert (
        assertions[-1]["asserted_value"]["CLASSIFICATION"]
        == "native future classification"
    )
    assert assertions[-1]["asserted_value"]["DISEASE LABEL"] == repeated[2]
    assert (
        assertions[-1]["asserted_value"]["ONLINE REPORT"]
        == assertions[0]["asserted_value"]["ONLINE REPORT"]
    )
    assert [a["source_metadata"]["native_row_index"] for a in assertions] == [0, 1, 2]


@pytest.mark.parametrize(
    "identifier",
    [
        "BRCA1",
        "P38398",
        "1100",
        "HGNC:01100",
        "hgnc:1100",
        "HGNC:1100.1",
        "HGNC:1100/HGNC:428",
        "HGNC:1100?x=1",
        "HGNC:1100,HGNC:428",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_exact_gene_identifier_is_required_even_without_digestion(identifier, skip):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_gene_validity(identifier, client=Client(native()), skip_digestion=skip)


@pytest.mark.parametrize(
    "text",
    [
        None,
        "",
        "<html>unavailable</html>",
        "No result found.",
        "GENE SYMBOL,GENE ID (HGNC)\nBRCA1,HGNC:1100\n",
        [],
        {},
    ],
)
def test_missing_native_header_is_failure_not_empty_curation(text):
    with pytest.raises(ConnectorError):
        get_gene_validity(GENE, client=Client(text))


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r[0].__setitem__(0, "other dataset"),
        lambda r: r[1].__setitem__(0, "FILE CREATED: 2026-02-30"),
        lambda r: r[1].__setitem__(1, "unexpected preamble"),
        lambda r: r[2].__setitem__(0, "WEBPAGE: https://other.example/"),
        lambda r: r[3].__setitem__(0, "not separator"),
        lambda r: r[4].__setitem__(0, "GENE NAME"),
        lambda r: r[5].__setitem__(0, "not separator"),
        lambda r: r[6].pop(),
        lambda r: r[6].__setitem__(1, "HGNC:01100"),
        lambda r: r[6].__setitem__(3, "MONDO:1"),
        lambda r: r[6].__setitem__(7, "https://other.example/report"),
        lambda r: r[6].__setitem__(8, "not a date"),
        lambda r: r[6].__setitem__(9, ""),
    ],
)
def test_complete_native_preamble_shape_and_context_are_validated(change):
    rows = small_export()
    change(rows)
    with pytest.raises(ConnectorError):
        get_gene_validity(GENE, client=Client(encode(rows)))


def test_unrelated_malformed_row_is_not_hidden_by_local_gene_selection():
    rows = small_export()
    unrelated = copy.deepcopy(rows[6])
    unrelated[1] = "HGNC:428"
    unrelated[3] = "malformed disease"
    rows.append(unrelated)
    with pytest.raises(ConnectorError):
        map_gene_validity(get_gene_validity(GENE, client=Client(encode(rows))))


@pytest.mark.parametrize(
    "context", [{"version": "2026-10-06"}, {"truncated": True}, {"truncated": None}]
)
def test_native_date_is_not_a_revision_and_unqualified_cuts_fail(context):
    with pytest.raises(ConnectorError):
        get_gene_validity(GENE, client=Client(native(), **context))


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "dosage_sensitivity"),
        ("query", {"hgnc_id": GENE, "dataset": "other"}),
        ("version", "2026-10-06"),
        ("truncated", True),
    ],
)
def test_mapping_requires_exact_qualified_envelope(key, value):
    envelope = get_gene_validity(GENE, client=FixtureClinGenClient())
    envelope[key] = value
    with pytest.raises(ConnectorError):
        map_gene_validity(envelope)


def test_bound_gzip_snapshot_keeps_original_bytes_time_and_declared_terms(tmp_path):
    path = tmp_path / "gene_validity.csv.gz"
    path.write_bytes(gzip.compress(PATH.read_bytes()))
    declared = metadata()
    declared["terms"] = {"licence": "CC0-1.0"}
    client = SnapshotClinGenClient(
        path,
        source_metadata=declared,
        expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    declared["query"]["hgnc_id"] = "HGNC:428"
    envelope = get_gene_validity(GENE, client=client)
    assert envelope["record"] == native()
    assert envelope["retrieved_at"] == metadata()["retrieved_at"]
    receipt = envelope["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert receipt["source_access_observed"] is False
    assert receipt["declared_terms"] == {"licence": "CC0-1.0"}
    assert receipt["compression"] == "gzip"
    assert all(
        a["retrieved_at"] == envelope["retrieved_at"]
        for a in map_gene_validity(envelope)
    )
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_gene_validity(
            GENE,
            client=SnapshotClinGenClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "other"),
        ("query", {"hgnc_id": "HGNC:428", "dataset": "gene_disease_validity"}),
        ("version", "2026-10-06"),
    ],
)
def test_supplied_snapshot_declarations_are_exactly_bound(tmp_path, key, value):
    path = tmp_path / "gene_validity.csv"
    path.write_bytes(PATH.read_bytes())
    declared = metadata()
    declared[key] = value
    with pytest.raises(ConnectorError):
        get_gene_validity(
            GENE, client=SnapshotClinGenClient(path, source_metadata=declared)
        )


def test_missing_fixture_and_corrupt_gzip_are_not_source_negatives(tmp_path):
    with pytest.raises(ConnectorError):
        get_gene_validity(GENE, client=FixtureClinGenClient(tmp_path))
    path = tmp_path / "gene_validity.csv.gz"
    path.write_bytes(b"invalid gzip")
    with pytest.raises(ConnectorError):
        get_gene_validity(
            GENE, client=SnapshotClinGenClient(path, source_metadata=metadata())
        )


@pytest.mark.parametrize("code", [404, 410, 429, 503])
def test_http_failure_does_not_mean_no_curation(monkeypatch, code):
    from sabueso.tools.db import clingen

    def fail(*args, **kwargs):
        raise HTTPError("https://search.clinicalgenome.org/", code, "failure", {}, None)

    monkeypatch.setattr(clingen, "urlopen", fail)
    with pytest.raises(ConnectorError):
        get_gene_validity(GENE)


def test_one_get_archive_replay_retains_time_scope_and_cc0_without_report_acquisition(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http as http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "text/csv"
        return response

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "clingen.db")
    with archive.recording():
        first = get_gene_validity(GENE)

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Replay/mapping must not acquire linked reports or sequences."
        )

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_gene_validity(GENE)
    assert calls == ["https://search.clinicalgenome.org/kb/gene-validity/download"]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_gene_validity(first) == map_gene_validity(second)
    observed = first["acquisition_trace"]["records"][0]
    replayed = second["acquisition_trace"]["records"][0]
    assert observed["network_attempts"] == observed["received_responses"] == 1
    assert replayed["network_attempts"] == 0 and replayed["access"] == "replay"
    assert observed["response_identity"] == replayed["response_identity"]
    assert source_terms()["ClinGen"]["licence"] == "CC0-1.0"
    assert retention("ClinGen")["keep"] == "yes"
    assert retention("ClinGen")["conditions"] == []
