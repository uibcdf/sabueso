"""Native DrugCentral occurrences, composite target scope and unchanged replay."""

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
from sabueso.mappings.drugcentral import COLUMNS, map_target_relations, parse_export
from sabueso.tools.db.drugcentral import (
    URL,
    FixtureDrugCentralClient,
    SnapshotDrugCentralClient,
    get_target_relations,
)

PATH = Path("temp_data/drugcentral/target_relations.tsv.gz")
TARGET = "P00533"


def native():
    return gzip.decompress(PATH.read_bytes()).decode("utf-8")


def small():
    rows = parse_export(native())["rows"]
    return [list(COLUMNS)] + [
        list(r["fields"].values()) for r in rows if TARGET in r["accessions"]
    ][:2]


def encode(rows):
    s = io.StringIO(newline="")
    csv.writer(s, delimiter="\t", quoting=csv.QUOTE_ALL).writerows(rows)
    return s.getvalue()


class Client:
    def __init__(self, text, **context):
        self.text = text
        self.context = context

    def target_relations(self, identifier):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def metadata():
    return {
        "source": "DrugCentral",
        "kind": "target_relations",
        "query": {"accession": TARGET, "dataset": "drug_target_interactions"},
        "retrieved_at": "2026-10-06T12:00:00+00:00",
    }


def test_full_native_export_and_egfr_observations_preserve_raw_support():
    raw = PATH.read_bytes()
    assert len(raw) == 956583
    assert (
        hashlib.sha256(raw).hexdigest()
        == "1908684983a79a067a44da952e1f6fd26b0f34cc36560cd9be0f0843bbfee1e1"
    )
    e = get_target_relations(TARGET, client=FixtureDrugCentralClient())
    before = copy.deepcopy(e)
    a = map_target_relations(e)
    assert len(a) == len({x["id"] for x in a}) == 80
    assert e["record"] == native()
    assert [x["asserted_value"] for x in a] == [
        r["fields"] for r in parse_export(native())["rows"] if TARGET in r["accessions"]
    ]
    assert sum(x["asserted_value"]["MOA"] == "1" for x in a) == 18
    assert all(x["asserted_value"]["ACT_UNIT"] == "" for x in a)
    assert a[0]["asserted_value"]["ACT_VALUE"] == "5.218"
    assert a[0]["asserted_value"]["ACT_TYPE"] == "IC50"
    assert a[0]["asserted_value"]["RELATION"] == "="
    assert a[0]["asserted_value"]["STRUCT_ID"] == "249"
    assert all(x["subject_ref"] == "drugcentral:target:P00533" for x in a)
    assert all(x["source"]["version"] is None and x["retrieved_at"] is None for x in a)
    assert all(
        "knowledge_class" not in x and "protein_ref" not in x["asserted_value"]
        for x in a
    )
    trace = e["acquisition_trace"]["records"][0]
    assert trace["count"] == 80 and trace["received_export_rows"] == 22364
    assert trace["network_attempts"] == 0
    assert e["snapshot_receipt"]["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert before == e
    a[0]["asserted_value"].clear()
    assert before == e


def test_composite_targets_remain_one_observation_without_potency_transfer():
    e = get_target_relations("P00918", client=FixtureDrugCentralClient())
    a = map_target_relations(e)
    composites = [x for x in a if "|" in x["asserted_value"]["ACCESSION"]]
    assert composites
    for x in composites:
        row = x["asserted_value"]
        assert x["subject_ref"] == "drugcentral:target:" + row["ACCESSION"]
        assert "P00918" in x["source_metadata"]["native_target_accessions"]
        assert len(x["source_metadata"]["native_target_accessions"]) > 1
        assert row["ACT_UNIT"] == ""


def test_not_listed_is_not_no_drugs_or_negative_interaction():
    e = get_target_relations("P60174", client=FixtureDrugCentralClient())
    assert map_target_relations(e) == []
    trace = e["acquisition_trace"]["records"][0]
    assert trace["outcome"] == "not_found" and trace["received_export_rows"] == 22364
    assert trace["native_result_declaration"] == "not_listed_in_received_export"


def test_repeated_conflicting_and_future_labels_survive_quoted_tsv():
    rows = small()
    rows.append(copy.deepcopy(rows[1]))
    changed = copy.deepcopy(rows[1])
    changed[7] = "0"
    changed[13] = "future label"
    changed[10] = 'native\tcomment\nwith "quotes"'
    rows.append(changed)
    a = map_target_relations(get_target_relations(TARGET, client=Client(encode(rows))))
    assert len(a) == len({x["id"] for x in a}) == 4
    assert a[0]["asserted_value"] == a[2]["asserted_value"]
    assert a[-1]["asserted_value"]["ACT_VALUE"] == "0"
    assert a[-1]["asserted_value"]["MOA"] == "future label"
    assert a[-1]["asserted_value"]["ACT_COMMENT"] == changed[10]


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        "",
        "EGFR",
        "p00533",
        "P00533-1",
        "P00533|P00918",
        "P00533?x=1",
        "../P00533",
        "P00533\nother",
    ],
)
def test_query_rejects_nonexact_native_base_accessions(identifier):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_target_relations(identifier, client=Client(encode(small())))


def test_backend_identity_checks_survive_skipped_digestion():
    with pytest.raises(ConnectorError):
        get_target_relations(
            " P00533 ", client=Client(encode(small())), skip_digestion=True
        )


@pytest.mark.parametrize(
    "text",
    [
        None,
        "",
        "<html>error</html>",
        "No result found.",
        "ACCESSION\tMOA\nP00533\t1\n",
        [],
        {},
        '"unclosed',
    ],
)
def test_malformed_document_is_not_a_source_negative(text):
    with pytest.raises(ConnectorError):
        get_target_relations(TARGET, client=Client(text))


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r[0].__setitem__(0, "OTHER"),
        lambda r: r[1].pop(),
        lambda r: r[1].append("extra"),
        lambda r: r[1].__setitem__(1, "0"),
        lambda r: r[1].__setitem__(1, "249.0"),
        lambda r: r[1].__setitem__(4, "P00533|"),
        lambda r: r[1].__setitem__(4, "P00533|BAD"),
        lambda r: r[1].__setitem__(4, "P00533-1"),
        lambda r: r[1].__setitem__(0, ""),
    ],
)
def test_entire_export_identity_and_shape_fail_closed(change):
    rows = small()
    change(rows)
    with pytest.raises(ConnectorError):
        get_target_relations(TARGET, client=Client(encode(rows)))


def test_unrelated_malformed_row_is_validated_before_selection():
    rows = small()
    rows[2][4] = "P00918"
    rows[2][1] = "bad"
    with pytest.raises(ConnectorError):
        get_target_relations(TARGET, client=Client(encode(rows)))


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "other"),
        ("query", {"accession": TARGET, "dataset": "other"}),
        ("version", "2027"),
        ("truncated", True),
    ],
)
def test_mapper_rejects_unqualified_scope_even_without_public_lookup(key, value):
    e = get_target_relations(TARGET, client=Client(encode(small())))
    e[key] = value
    with pytest.raises(ConnectorError):
        map_target_relations(e)


@pytest.mark.parametrize(
    "context", [{"version": "2027"}, {"truncated": True}, {"truncated": None}]
)
def test_website_version_and_unqualified_cuts_are_not_supported(context):
    with pytest.raises(ConnectorError):
        get_target_relations(TARGET, client=Client(encode(small()), **context))


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "other"),
        ("query", {"accession": "P00918", "dataset": "drug_target_interactions"}),
        ("version", "2027"),
    ],
)
def test_supplied_snapshot_bindings_are_exact(tmp_path, key, value):
    p = tmp_path / "export.tsv"
    p.write_text(encode(small()), encoding="utf-8", newline="")
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get_target_relations(
            TARGET, client=SnapshotDrugCentralClient(p, source_metadata=m)
        )


@pytest.mark.parametrize("compressed", [False, True])
def test_snapshot_original_time_byte_hash_and_declared_terms(tmp_path, compressed):
    b = encode(small()).encode()
    b = gzip.compress(b) if compressed else b
    p = tmp_path / ("export.tsv.gz" if compressed else "export.tsv")
    p.write_bytes(b)
    m = metadata()
    m["terms"] = {"licence": "CC-BY-SA-4.0"}
    c = SnapshotDrugCentralClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(b).hexdigest()
    )
    m["query"]["accession"] = "P00918"
    e = get_target_relations(TARGET, client=c)
    receipt = e["snapshot_receipt"]
    assert e["retrieved_at"] == metadata()["retrieved_at"]
    assert receipt["document_sha256"] == hashlib.sha256(b).hexdigest()
    assert receipt["declared_terms"] == {"licence": "CC-BY-SA-4.0"}
    assert receipt["source_access_observed"] is False
    assert receipt["compression"] == ("gzip" if compressed else None)
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_target_relations(
            TARGET,
            client=SnapshotDrugCentralClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


def test_unavailable_fixture_and_corrupt_gzip_are_not_not_found(tmp_path):
    with pytest.raises(ConnectorError):
        get_target_relations(TARGET, client=FixtureDrugCentralClient(tmp_path))
    p = tmp_path / "bad.tsv.gz"
    p.write_bytes(b"not gzip")
    with pytest.raises(ConnectorError):
        get_target_relations(
            TARGET, client=SnapshotDrugCentralClient(p, source_metadata=metadata())
        )


def test_online_failure_is_recorded_as_failure(monkeypatch):
    from sabueso.tools.db import _http as http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 503, "Unavailable", {}, None)

    monkeypatch.setattr(http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_target_relations(TARGET)


def test_single_get_archive_replay_preserves_compressed_and_text_identity(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http as http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "application/gzip"
        return response

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "drugcentral.db")
    with archive.recording():
        first = get_target_relations(TARGET)

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay/mapping must not acquire linked source data.")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_target_relations(TARGET)
    assert calls == [URL]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_target_relations(first) == map_target_relations(second)
    observed = first["acquisition_trace"]["records"][0]
    replayed = second["acquisition_trace"]["records"][0]
    assert observed["network_attempts"] == observed["received_responses"] == 1
    assert replayed["network_attempts"] == 0 and replayed["access"] == "replay"
    assert observed["response_identity"] == replayed["response_identity"]
    assert source_terms()["DrugCentral"]["licence"] == "CC-BY-SA-4.0"
    assert retention("DrugCentral")["keep"] == "yes"
