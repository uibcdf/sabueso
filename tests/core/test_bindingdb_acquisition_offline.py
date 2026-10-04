"""BindingDB REST/fixture/mirror access retains original attribution (#108).

Network examples and indexed mirror rows here are synthetic. The card test uses
only frozen public responses declared in temp_data/NOTICE.md.
"""

import hashlib
import io
import json
import sqlite3
import zipfile
from datetime import timedelta
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import ackredit
import pytest

import sabueso
from sabueso.core import attribution as adapter
from sabueso.core.card import Card
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, bindingdb
from sabueso.tools.db.bindingdb_mirror import BindingDBMirror, MirrorBindingDBClient
from sabueso.tools.db.unichem import FixtureUniChemClient

DATA = Path("temp_data")
ROWS = [
    {
        "monomerid": "12",
        "affinity_type": "IC50",
        "affinity": ">100000",
        "pmid": "1",
        "doi": "10.1234/synthetic",
    },
    {
        "monomerid": "11",
        "affinity_type": "Ki",
        "affinity": "5",
        "pmid": "1",
        "doi": "10.1234/synthetic",
    },
    {
        "monomerid": "11",
        "affinity_type": "IC50",
        "affinity": "20",
        "pmid": "1",
        "doi": "10.1234/synthetic",
    },
]


@pytest.fixture(autouse=True)
def independent_workflow():
    with ackredit.session("BindingDB observation regression"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()


def serve(monkeypatch, *, error=None, records=None):
    calls = []
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)

    def response(request, timeout):
        calls.append(request)
        if error == "timeout":
            raise URLError(TimeoutError("synthetic timeout"))
        if error:
            raise HTTPError(
                request.full_url, error, "synthetic failure", Message(), None
            )
        return Response(
            {
                "getLindsByUniprotsResponse": {
                    "affinities": ROWS if records is None else records
                }
            }
        )

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def record(result):
    (observed,) = result["acquisition_trace"]["records"]
    return observed


@pytest.fixture()
def mirror(tmp_path):
    columns = [
        "BindingDB Reactant_set_id",
        "BindingDB MonomerID",
        "Ligand SMILES",
        "Ligand InChI Key",
        "Ki (nM)",
        "IC50 (nM)",
        "Kd (nM)",
        "EC50 (nM)",
        "PMID",
        "Article DOI",
        "ChEMBL ID of Ligand",
        "PubChem CID",
        "Curation/DataSource",
        "UniProt (SwissProt) Primary ID of Target Chain 1",
    ]
    cells = [
        [
            "1",
            "11",
            "CCO",
            "SYNTHETIC-A",
            "5",
            "20",
            "",
            "",
            "1",
            "10.1234/synthetic",
            "CHEMBL1",
            "1",
            "ChEMBL",
            "P60174",
        ],
        [
            "2",
            "12",
            "CCN",
            "SYNTHETIC-B",
            "",
            ">100000",
            "",
            "",
            "",
            "",
            "",
            "",
            "BindingDB",
            "P60174",
        ],
    ]
    archive = tmp_path / "synthetic.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "BindingDB_All.tsv",
            "\t".join(columns) + "\n" + "".join("\t".join(row) + "\n" for row in cells),
        )
    directory = tmp_path / "mirror"
    info = BindingDBMirror().install(
        "202609",
        directory,
        from_file=archive,
        md5=hashlib.md5(archive.read_bytes()).hexdigest(),
    )
    return MirrorBindingDBClient(directory), info


def test_rest_query_caps_original_pointers_and_citation_roles(monkeypatch):
    calls = serve(monkeypatch)
    result = bindingdb.get_affinities("P60174", limit=1)
    observed = record(result)
    assert result["record"] == [ROWS[2]] and result["truncated"]
    assert observed["query"] == {
        "accession": "P60174",
        "cutoff": bindingdb.DEFAULT_CUTOFF,
        "limit": 1,
    }
    assert parse_qs(urlsplit(calls[0].full_url).query)["cutoff"] == [
        str(bindingdb.DEFAULT_CUTOFF)
    ]
    assert (
        observed["count"] == 1
        and observed["total_count"] == 3
        and observed["truncated"]
    )
    assert observed["record_order"] == "bindingdb_record_order@1"
    assert observed["source_version"] == {"value": None, "basis": "not_stated"}
    assert observed["cutoff_scope"] == {
        "quantity": {"value": bindingdb.DEFAULT_CUTOFF, "unit": "nM"},
        "basis": "submitted_to_rest",
    }
    assert observed["pages"][0]["count"] == 3
    assert observed["requests"][0]["response_sha256"]
    assert observed["provider"]["status"] == "available"
    assert observed["publications"] == [{"doi": "10.1234/synthetic", "pmid": "1"}]
    assert "measurement_origin_not_stated" in observed["bibliography_gaps"]
    portable = ackredit.Attribution.from_dict(observed["provider"]["attribution"])
    assert "BindingDB in 2024" in portable.report(format="bibtex")
    roles = [role for use in portable.to_dict()["uses"] for role in use["roles"]]
    assert {
        "resource_access",
        "resource_description",
        "measurement_primary_citation",
    } <= set(roles)
    citation = next(
        b for b in observed["bibliography"] if b.get("doi") == "10.1234/synthetic"
    )
    assert "title" not in citation and "authors" not in citation


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archive_keeps_original_retrieval_hashes_queries_and_citations(
    tmp_path, monkeypatch, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "requests.db")
    with archive.recording():
        first = bindingdb.get_affinities("P60174")
    with (
        archive.replaying() if mode == "replay" else archive.reusing(timedelta(days=1))
    ):
        second = bindingdb.get_affinities("P60174")
    one, two = record(first), record(second)
    assert len(calls) == 1 and first["record"] == second["record"]
    assert two["access"] == mode and two["network_attempts"] == 0
    for key in (
        "retrieved_at",
        "source_version",
        "response_identity",
        "pages",
        "bibliography",
    ):
        assert one[key] == two[key]
    assert one["requests"][0]["retrieval_ref"] == two["requests"][0]["retrieval_ref"]


def test_recovered_http_and_unreadable_json_retries_remain_observable(monkeypatch):
    serve(monkeypatch)
    original = _http._urlopen
    attempts = []

    def intermittent(request, timeout):
        attempts.append(request)
        if len(attempts) == 1:
            raise HTTPError(
                request.full_url, 500, "synthetic transient failure", Message(), None
            )
        if len(attempts) == 2:
            answer = io.BytesIO(b"synthetic unreadable JSON")
            answer.status, answer.headers = 200, Message()
            return answer
        return original(request, timeout)

    monkeypatch.setattr(_http, "_urlopen", intermittent)
    observed = record(bindingdb.get_affinities("P60174"))
    assert observed["outcome"] == "received" and observed["network_attempts"] == 3
    assert [reason for r in observed["requests"] for reason in r["retries"]] == [
        "HTTP 500",
        "unreadable_body",
    ]


@pytest.mark.parametrize("error", [400, 404, 500, "timeout"])
def test_http_errors_preserve_connector_failure_instead_of_inventing_absence(
    monkeypatch, error
):
    serve(monkeypatch, error=error)
    with pytest.raises(ConnectorError) as caught:
        bindingdb.get_affinities("P60174")
    observed = caught.value.acquisition_trace["records"][0]
    assert observed["outcome"] == "failed"
    assert observed["provider"]["status"] == "not_attempted"
    assert observed["requests"][-1]["outcome"] == "failed"


def test_decoded_empty_response_missing_fixture_and_offline_unqueried_are_distinct(
    tmp_path, monkeypatch
):
    calls = serve(monkeypatch, records=[])
    with pytest.raises(RecordNotFoundError) as caught:
        bindingdb.get_affinities("P60174")
    empty = caught.value.acquisition_trace["records"][0]
    assert empty["outcome"] == "empty" and empty["count"] == 0
    assert (
        empty["provider"]["status"] == "available" and empty["pages"][0]["count"] == 0
    )
    with pytest.raises(RecordNotFoundError) as caught:
        bindingdb.get_affinities(
            "P60174", client=bindingdb.FixtureBindingDBClient(tmp_path)
        )
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "unavailable"
    directory = tmp_path / "bindingdb"
    directory.mkdir()
    (directory / "P60174.json").write_text(
        json.dumps({"getLindsByUniprotsResponse": {"affinities": []}})
    )
    with pytest.raises(RecordNotFoundError) as caught:
        bindingdb.get_affinities(
            "P60174",
            client=bindingdb.FixtureBindingDBClient(
                tmp_path, retrieved_at="synthetic original time"
            ),
        )
    empty_fixture = caught.value.acquisition_trace["records"][0]
    assert (
        empty_fixture["outcome"] == "empty"
        and empty_fixture["retrieved_at"] == "synthetic original time"
    )
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    with archive.replaying(), pytest.raises(ConnectorError) as caught:
        bindingdb.get_affinities("P60174")
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "not_queried"
    assert len(calls) == 1


def test_mirror_queries_keep_manifest_release_origins_cutoff_and_empty_scope(mirror):
    client, info = mirror
    result = bindingdb.get_affinities("P60174", client=client, limit=1)
    observed = record(result)
    assert observed["access"] == "mirror" and observed["requests"] == []
    assert observed["network_attempts"] == observed["received_responses"] == 0
    assert observed["source_version"]["value"] == "202609"
    assert observed["source_version"]["basis"] == "installed_mirror_release"
    assert observed["mirror"]["manifest"] == info
    assert observed["mirror"]["manifest_identity"]["hash"].startswith("sha256:")
    assert observed["retrieved_at"] == info["installed_at"]
    assert observed["retrieved_at_basis"] == "mirror_installation_time"
    assert observed["cutoff_scope"]["basis"] == "applied_to_local_index"
    assert observed["record_origins"][0]["data_source"] == "ChEMBL"
    assert not any(
        b.get("doi") == "10.1093/nar/gkad1004" for b in observed["bibliography"]
    )
    assert observed["provider"]["status"] == "available" and observed["truncated"]
    with sabueso.attribution() as run:
        result = client.ligands(accession="P60174", cutoff=50)
    assert len(result["record"]) == 2 and run.acquisitions[0]["cutoff_scope"][
        "quantity"
    ] == {"value": 50, "unit": "nM"}
    with pytest.raises(RecordNotFoundError) as caught:
        bindingdb.get_affinities("P52270", client=client)
    empty = caught.value.acquisition_trace["records"][0]
    assert empty["outcome"] == "empty" and empty["source_version"]["value"] == "202609"
    assert empty["access"] == "mirror" and empty["provider"]["status"] == "available"


def test_corrupt_mirror_query_is_failed_with_known_manifest_and_no_success_credit(
    mirror,
):
    client, _ = mirror
    (client.directory / "index.sqlite").write_bytes(b"synthetic corrupt index")
    with pytest.raises(sqlite3.DatabaseError) as caught:
        bindingdb.get_affinities("P60174", client=client)
    observed = caught.value.acquisition_trace["records"][0]
    assert (
        observed["outcome"] == "failed"
        and observed["provider"]["status"] == "not_attempted"
    )
    assert (
        observed["access"] == "mirror"
        and observed["source_version"]["value"] == "202609"
    )
    assert observed["pages"] == []


def test_received_data_survives_client_ordering_failure_without_relabeling_exception(
    monkeypatch,
):
    serve(monkeypatch, records=[{**ROWS[0], "monomerid": "synthetic invalid integer"}])
    with pytest.raises(ValueError) as caught:
        bindingdb.get_affinities("P60174")
    observed = caught.value.acquisition_trace["records"][0]
    assert observed["outcome"] == "partial" and observed["incomplete"]
    assert (
        observed["count"] == 1
        and observed["count_basis"] == "received_affinities_before_completion"
    )
    assert observed["provider"]["status"] == "available"


def test_original_pointer_forms_do_not_conflict_with_full_host_citations(monkeypatch):
    serve(
        monkeypatch, records=[ROWS[0], {**ROWS[1], "doi": ""}, {**ROWS[2], "pmid": "2"}]
    )
    with ackredit.capture("host") as host:
        original = {
            "id": "doi:10.1234/synthetic",
            "type": "article",
            "title": "Synthetic full citation",
            "authors": ["Example, A"],
            "year": 2020,
        }
        ackredit.register_item(**original)
        ackredit.track_item(original["id"], roles=["original_reference"])
        observed = record(bindingdb.get_affinities("P60174"))
    assert observed["provider"]["status"] == "available"
    pointers = [
        b
        for b in observed["bibliography"]
        if b["id"].startswith("sabueso:bindingdb-primary-citation:")
    ]
    assert len(pointers) == 3 and len({b["id"] for b in pointers}) == 3
    assert (
        next(
            b for b in host.attribution.to_dict()["items"] if b["id"] == original["id"]
        )
        == original
    )


def test_fixture_card_refresh_and_saved_readers_keep_support_outside_runtime(tmp_path):
    options = {
        "resolver": EntityResolver(FixtureUniProtClient(DATA)),
        "bindingdb": {},
        "bindingdb_client": bindingdb.FixtureBindingDBClient(DATA),
        "unichem_client": FixtureUniChemClient(DATA),
    }
    card, resolution = sabueso.resolve("P60174", **options)
    observed = next(
        r for r in card.acquisition_trace["records"] if r["source"] == "BindingDB"
    )
    assert observed["access"] == "fixture" and observed["count"] > 0
    assert observed["cutoff_scope"]["basis"] == "fixture_not_reapplied"
    assert card.acquisition_trace == resolution.acquisition_trace
    assert "acquisition_trace" not in card.to_dict()
    card.to_json(str(tmp_path / "card.json"))
    before = ackredit.get_attribution().to_dict()
    restored = Card.from_json(str(tmp_path / "card.json"))
    assert (
        restored.snapshot_id() == card.snapshot_id()
        and restored.acquisition_trace is None
    )
    ackredit.Attribution.from_dict(observed["provider"]["attribution"]).report(
        format="bibtex"
    )
    assert json.loads(json.dumps(observed))["bibliography"] == observed["bibliography"]
    assert ackredit.get_attribution().to_dict() == before
    refreshed, resolution = sabueso.refresh_card(card, **options)
    assert refreshed.acquisition_trace["card_ref"] == refreshed.pinned_ref()
    assert any(
        r["source"] == "BindingDB" for r in resolution.acquisition_trace["records"]
    )


def test_provider_failure_preserves_scientific_result_and_custom_client_gap(
    monkeypatch,
):
    serve(monkeypatch)
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic provider failure")),
    )
    with pytest.warns(Warning, match="Attribution failed"):
        result = bindingdb.get_affinities("P60174")
    assert (
        len(result["record"]) == 3 and record(result)["provider"]["status"] == "failed"
    )

    class Custom:
        def ligands(self, accession, limit):
            return {"record": [], "retrieved_at": "synthetic", "total_count": 0}

    assert (
        bindingdb.get_affinities("P60174", client=Custom())["acquisition_trace"][
            "records"
        ]
        == []
    )


@pytest.mark.parametrize("body", [b"", b'""'])
def test_documented_empty_strings_retain_evaluated_empty_receipts(monkeypatch, body):
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)

    def response(request, timeout):
        answer = io.BytesIO(body)
        answer.status, answer.headers = 200, Message()
        return answer

    monkeypatch.setattr(_http, "_urlopen", response)
    with pytest.raises(RecordNotFoundError) as caught:
        bindingdb.get_affinities("P60174")
    observed = caught.value.acquisition_trace["records"][0]
    assert (
        observed["outcome"] == "empty" and observed["provider"]["status"] == "available"
    )
    assert observed["requests"][0]["status"] == 200
    assert (
        observed["network_attempts"] == 1 and observed["requests"][0]["retries"] == []
    )
    assert (
        observed["requests"][0]["response_sha256"] == hashlib.sha256(body).hexdigest()
    )


@pytest.mark.parametrize(
    "body",
    [
        b" ",
        b"<html>busy</html>",
        b"null",
        b"{}",
        b'"busy"',
        b'{"getLindsByUniprotsResponse":{"affinities":null}}',
        b'{"getLindsByUniprotsResponse":{"affinities":[1]}}',
    ],
)
def test_malformed_or_unexpected_responses_remain_failed(monkeypatch, body):
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)

    def response(request, timeout):
        answer = io.BytesIO(body)
        answer.status, answer.headers = 200, Message()
        return answer

    monkeypatch.setattr(_http, "_urlopen", response)
    with pytest.raises(ConnectorError) as caught:
        bindingdb.get_affinities("P60174")
    observed = caught.value.acquisition_trace["records"][0]
    assert observed["outcome"] == "failed"
    assert observed["provider"]["status"] == "not_attempted"


@pytest.mark.parametrize("body", [b"", b'""'])
def test_empty_forms_keep_original_archive_identities_and_fixture_absence(
    monkeypatch, tmp_path, body
):
    def response(request, timeout):
        answer = io.BytesIO(body)
        answer.status, answer.headers = 200, Message()
        return answer

    monkeypatch.setattr(_http, "_urlopen", response)
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    with archive.recording(), pytest.raises(RecordNotFoundError) as caught:
        bindingdb.get_affinities("P60174")
    original = caught.value.acquisition_trace["records"][0]
    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("no new network")
    )
    with archive.replaying(), pytest.raises(RecordNotFoundError) as caught:
        bindingdb.get_affinities("P60174")
    replayed = caught.value.acquisition_trace["records"][0]
    assert replayed["outcome"] == "empty" and replayed["network_attempts"] == 0
    assert replayed["retrieved_at"] == original["retrieved_at"]
    assert (
        replayed["requests"][0]["retrieval_ref"]
        == original["requests"][0]["retrieval_ref"]
    )
    path = tmp_path / "bindingdb" / "P60174.json"
    path.parent.mkdir()
    path.write_bytes(body)
    with pytest.raises(RecordNotFoundError) as caught:
        bindingdb.get_affinities(
            "P60174", client=bindingdb.FixtureBindingDBClient(tmp_path)
        )
    observed = caught.value.acquisition_trace["records"][0]
    assert observed["outcome"] == "empty" and observed["access"] == "fixture"


def test_nested_collectors_keep_independent_fixture_receipts():
    with sabueso.attribution() as outer:
        with sabueso.attribution() as inner:
            result = bindingdb.get_affinities(
                "P60174", client=bindingdb.FixtureBindingDBClient(DATA)
            )
    assert (
        outer.acquisitions
        == inner.acquisitions
        == result["acquisition_trace"]["records"]
    )
    changed = inner.acquisitions
    changed[0]["query"].clear()
    assert inner.acquisitions[0]["query"]


@pytest.mark.parametrize("body", [b"", b'""'])
def test_empty_forms_on_cards_are_source_answers_without_failure_warning(
    monkeypatch, body, recwarn
):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    def response(request, timeout):
        answer = io.BytesIO(body)
        answer.status, answer.headers = 200, Message()
        return answer

    monkeypatch.setattr(_http, "_urlopen", response)
    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient(DATA)),
        bindingdb={},
        bindingdb_client=bindingdb.OnlineBindingDBClient(),
        unichem_client=FixtureUniChemClient(DATA),
    )
    outcome = next(e for e in card.quality["enrichments"] if e["source"] == "BindingDB")
    assert outcome["status"] == "not_found"
    assert not any(issubclass(w.category, EnrichmentFailedWarning) for w in recwarn)
    assert (
        next(
            r for r in card.acquisition_trace["records"] if r["source"] == "BindingDB"
        )["outcome"]
        == "empty"
    )


@pytest.mark.parametrize("body", [b"", b'""'])
def test_declared_empty_strings_with_unexpected_status_are_failed(monkeypatch, body):
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)

    def response(request, timeout):
        answer = io.BytesIO(body)
        answer.status, answer.headers = 204, Message()
        return answer

    monkeypatch.setattr(_http, "_urlopen", response)
    with pytest.raises(ConnectorError) as caught:
        bindingdb.get_affinities("P60174")
    observed = caught.value.acquisition_trace["records"][0]
    assert (
        observed["outcome"] == "failed"
        and observed["provider"]["status"] == "not_attempted"
    )
