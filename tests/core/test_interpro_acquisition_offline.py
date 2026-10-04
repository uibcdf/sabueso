"""InterPro site observation retains native annotation scope and original credit.

Wire cases are synthetic; card cases use declared frozen public responses.
"""

import io
import json
from copy import deepcopy
from datetime import timedelta
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError

import ackredit
import pytest

import sabueso
from sabueso.core import attribution as adapter
from sabueso.core.card import Card
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, interpro

SIGNATURE = {
    "accession": "cd00311",
    "source_database": "cdd",
    "name": "TIM",
    "locations": [
        {
            "description": "synthetic site",
            "fragments": [{"start": 14, "end": 14, "residues": "K"}],
        }
    ],
}
RESIDUES = {"cd00311": SIGNATURE}
DEFAULT = object()


@pytest.fixture(autouse=True)
def independent_workflow():
    with ackredit.session("InterPro observation"):
        yield


class Response(io.BytesIO):
    def __init__(self, payload, version="110.0", *, raw=False, status=200):
        super().__init__(payload if raw else json.dumps(payload).encode())
        self.status = status
        self.headers = Message()
        if version is not None:
            self.headers["InterPro-Version"] = str(version)


def serve(
    monkeypatch, *, payload=DEFAULT, version="110.0", error=None, raw=False, status=200
):
    calls = []
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)

    def response(request, timeout):
        calls.append(request)
        if error == "timeout":
            raise URLError(TimeoutError("synthetic timeout"))
        if isinstance(error, int):
            headers = Message()
            headers["InterPro-Version"] = "110.0"
            raise HTTPError(request.full_url, error, "synthetic", headers, None)
        return Response(
            b"not JSON"
            if error == "malformed"
            else RESIDUES
            if payload is DEFAULT
            else payload,
            version,
            raw=raw or error == "malformed",
            status=status,
        )

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def lookup(accession="P52270", client=None):
    return interpro.get_site_residues(accession, client=client)


def event(result):
    (record,) = result["acquisition_trace"]["records"]
    return record


def fixture(tmp_path, saved):
    directory = tmp_path / "interpro"
    directory.mkdir()
    (directory / "residues__P52270.json").write_text(
        json.dumps(saved), encoding="utf-8"
    )
    return interpro.FixtureInterProClient(
        tmp_path, retrieved_at="original fixture time"
    )


def test_native_signature_query_release_and_resource_bibliography(monkeypatch):
    calls = serve(monkeypatch)
    with ackredit.capture("enclosing annotation workflow") as host:
        result = lookup()
    record = event(result)
    assert result["record"] == RESIDUES and result["version"] == "110.0"
    assert record["source"] == "InterPro" and record["operation"] == "site_residues"
    assert record["query"] == {"accession": "P52270"}
    assert record["outcome"] == "received" and record["count"] == 1
    assert record["count_basis"] == "source_returned_signature_records_not_mapped_sites"
    assert record["source_version"] == {
        "value": "110.0",
        "basis": "response_header_release",
    }
    assert record["response_identity"]["hash"] == digest(canonical_json(RESIDUES))
    (entry,) = record["entries"]
    assert entry["signature_key"] == "cd00311"
    assert entry["signature_metadata"] == {
        k: SIGNATURE[k] for k in ("accession", "name", "source_database")
    }
    assert (
        entry["location_record_count"] == 1
        and entry["locations"] == SIGNATURE["locations"]
    )
    assert len(calls) == record["network_attempts"] == 1
    request = record["requests"][0]
    assert request["url"] == interpro.INTERPRO_API + "/protein/uniprot/P52270/?residues"
    assert request["method"] == "GET" and request["response_sha256"]
    assert "not consulted" in record["annotation_context"]["reference_basis"]
    assert record["bibliography_gaps"] == [
        "member_database_signature_and_site_citations_not_returned"
    ]
    paper = next(
        b for b in record["bibliography"] if b.get("doi") == "10.1093/nar/gkae1082"
    )
    assert paper["year"] == 2025 and len(paper["authors"]) == 34
    assert paper["pages"] == "D444-D456"
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    uses = portable.to_dict()["uses"]
    assert {role for use in uses for role in use["roles"]} == {
        "executed_software",
        "resource_access",
        "resource_description",
    }
    assert {use["item_id"] for use in uses if "executed_software" in use["roles"]} == {
        record["bibliography"][0]["id"]
    }
    assert "gkae1082" in portable.report(format="bibtex")
    assert any(
        use["context"].get("annotation_context") == record["annotation_context"]
        for use in host.attribution.to_dict()["uses"]
    )


@pytest.mark.parametrize("version", [None, "0", "110.0"])
def test_unstated_header_release_is_not_inferred_from_member_or_signature(
    monkeypatch, version
):
    serve(monkeypatch, version=version)
    record = event(lookup())
    assert record["source_version"] == {
        "value": version,
        "basis": "response_header_release" if version is not None else "not_stated",
    }


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archive_retains_native_release_original_time_and_wire_identity(
    monkeypatch, tmp_path, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "interpro.db")
    with archive.recording():
        original = event(lookup())
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        reused = event(lookup())
    assert (
        reused["access"] == mode and reused["network_attempts"] == 0 and len(calls) == 1
    )
    for key in (
        "query",
        "retrieved_at",
        "source_version",
        "response_identity",
        "entries",
        "pages",
        "annotation_context",
    ):
        assert reused[key] == original[key]
    for key in ("response_sha256", "retrieved_at", "retrieval_ref"):
        assert reused["requests"][0][key] == original["requests"][0][key]
    assert reused["provider"]["status"] == "available"


@pytest.mark.parametrize("body,status", [(b"{}", 200), (b"", 200), (b"", 204)])
def test_declared_empty_answers_preserve_original_exception_and_ambiguous_absence(
    monkeypatch, body, status
):
    calls = serve(monkeypatch, payload=body, raw=True, status=status)
    with pytest.raises(RecordNotFoundError) as caught:
        lookup()
    record = caught.value.acquisition_trace["records"][0]
    assert record["outcome"] == "empty" and record["count"] == 0
    assert record["provider"]["status"] == "available"
    assert record["source_version"]["value"] == "110.0" and len(calls) == 1
    assert record["response_identity"]["hash"] == digest(canonical_json({}))
    assert "cannot_be_distinguished" in record["annotation_context"]["absence_basis"]


@pytest.mark.parametrize("error", [204, 404, 500, "timeout", "malformed"])
def test_original_http_absence_and_failures_keep_wire_facts_and_versions(
    monkeypatch, error
):
    calls = serve(monkeypatch, error=error)
    with (
        sabueso.attribution() as run,
        pytest.raises(
            RecordNotFoundError if error in (204, 404) else ConnectorError
        ) as caught,
    ):
        lookup()
    (record,) = run.acquisitions
    assert caught.value.acquisition_trace["records"] == [record]
    assert record["outcome"] == (
        "not_found" if error == 404 else "empty" if error == 204 else "failed"
    )
    assert record["network_attempts"] == len(calls) == (3 if error == 500 else 1)
    assert record["source_version"]["value"] == (
        None if error == "timeout" else "110.0"
    )
    assert record["provider"]["status"] == (
        "available" if error in (204, 404) else "not_attempted"
    )
    assert record["response_identity"] == {"basis": "not_received", "hash": None}
    assert not record["completed_pages"]


@pytest.mark.parametrize("mode", ["reuse", "replay"])
@pytest.mark.parametrize("body", [b"{}", b""])
def test_archived_empty_response_retains_original_hash_time_and_release(
    monkeypatch, tmp_path, mode, body
):
    calls = serve(monkeypatch, payload=body, raw=True)
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    with archive.recording(), pytest.raises(RecordNotFoundError) as original:
        lookup()
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        with pytest.raises(RecordNotFoundError) as reused:
            lookup()
    a, b = [e.value.acquisition_trace["records"][0] for e in (original, reused)]
    assert b["access"] == mode and b["network_attempts"] == 0 and len(calls) == 1
    assert b["outcome"] == "empty" and b["provider"]["status"] == "available"
    for key in ("retrieved_at", "source_version", "response_identity", "pages"):
        assert a[key] == b[key]
    assert a["requests"][0]["response_sha256"] == b["requests"][0]["response_sha256"]


@pytest.mark.parametrize("mode", ["missing", "offline", "simulated"])
def test_local_unavailable_unqueried_and_failed_access_stay_distinct(tmp_path, mode):
    client = (
        None
        if mode == "offline"
        else interpro.FixtureInterProClient(
            tmp_path, failing={"P52270"} if mode == "simulated" else ()
        )
    )
    archive = sabueso.RetrievalArchive(tmp_path / "missing.db")
    with (
        archive.replaying(),
        pytest.raises(
            ConnectorError if mode != "missing" else RecordNotFoundError
        ) as caught,
    ):
        lookup(client=client)
    record = caught.value.acquisition_trace["records"][0]
    assert (
        record["outcome"]
        == {"missing": "unavailable", "offline": "not_queried", "simulated": "failed"}[
            mode
        ]
    )
    assert (
        record["network_attempts"] == 0
        and record["provider"]["status"] == "not_attempted"
    )
    assert record["response_identity"]["hash"] is None and not record["pages"]


@pytest.mark.parametrize("residues", [{}, None, [], [SIGNATURE]])
def test_fixture_empty_and_unexpected_shapes_do_not_change_raw_returns(
    tmp_path, residues
):
    result = lookup(client=fixture(tmp_path, {"version": 0, "residues": residues}))
    record = event(result)
    assert result["record"] == residues and result["version"] == "0"
    assert record["source_version"] == {"value": 0, "basis": "fixture_declared_release"}
    assert record["outcome"] == ("empty" if residues == {} else "unobserved")
    assert record["count"] == (0 if residues == {} else None)
    assert record["retrieved_at"] == "original fixture time"


@pytest.mark.parametrize("residues", [None, [], [SIGNATURE], "unexpected"])
def test_decoded_non_maps_have_no_completed_annotation_credit(monkeypatch, residues):
    serve(monkeypatch, payload=residues)
    if residues:
        result = lookup()
        assert result["record"] == residues
        record = event(result)
    else:
        with pytest.raises(RecordNotFoundError) as caught:
            lookup()
        record = caught.value.acquisition_trace["records"][0]
    assert record["outcome"] == "unobserved" and record["count"] is None
    assert record["provider"]["status"] == "not_attempted" and record["pages"]
    assert record["response_identity"]["hash"] == digest(canonical_json(residues))


@pytest.mark.parametrize("good", [True, False])
def test_partial_signature_maps_retain_only_actual_completed_credit(monkeypatch, good):
    residues = {"invalid": None, **(RESIDUES if good else {})}
    serve(monkeypatch, payload=residues)
    result = lookup()
    record = event(result)
    assert result["record"] == residues and record["count"] == len(residues)
    assert record["outcome"] == ("partial" if good else "unobserved")
    assert record["provider"]["status"] == ("available" if good else "not_attempted")
    assert bool(record["completed_pages"]) == good


@pytest.mark.parametrize(
    "saved,error", [({}, KeyError), ([], AttributeError), (None, AttributeError)]
)
def test_broken_fixture_envelopes_preserve_original_failure_without_empty_credit(
    tmp_path, saved, error
):
    with pytest.raises(error) as caught:
        lookup(client=fixture(tmp_path, saved))
    record = caught.value.acquisition_trace["records"][0]
    assert record["outcome"] == "unobserved" and record["count"] is None
    assert record["provider"]["status"] == "not_attempted" and record["pages"]


def test_malformed_fixture_has_no_decoded_identity_or_credit(tmp_path):
    fixture(tmp_path, {})
    (tmp_path / "interpro/residues__P52270.json").write_text(
        "not JSON", encoding="utf-8"
    )
    with pytest.raises(json.JSONDecodeError) as caught:
        lookup(client=interpro.FixtureInterProClient(tmp_path))
    record = caught.value.acquisition_trace["records"][0]
    assert record["outcome"] == "failed" and not record["pages"]
    assert record["provider"]["status"] == "not_attempted"


@pytest.mark.parametrize("accession", ["P52270", "P60174"])
def test_public_cards_refresh_pins_and_saved_readers_remain_inert(tmp_path, accession):
    options = {
        "resolver": EntityResolver(FixtureUniProtClient("temp_data")),
        "family_sites": True,
        "interpro_client": interpro.FixtureInterProClient(
            "temp_data", retrieved_at="original"
        ),
    }
    card, resolution = sabueso.resolve(accession, **options)
    (record,) = [
        r for r in card.acquisition_trace["records"] if r["source"] == "InterPro"
    ]
    saved = json.loads(
        Path(f"temp_data/interpro/residues__{accession}.json").read_text()
    )
    assert record["source_version"] == {
        "value": saved["version"],
        "basis": "fixture_declared_release",
    }
    assert record["count"] == len(saved["residues"]) == 1
    assert card.acquisition_trace == resolution.acquisition_trace
    assert card.acquisition_trace["card_ref"] == card.pinned_ref()
    assert "acquisition_trace" not in card.to_dict()
    detached = card.acquisition_trace
    detached["records"].clear()
    assert card.acquisition_trace["records"]
    assertions = [
        a
        for a in card.source_assertion_store.to_list()
        if a["source"]["name"] == "InterPro"
    ]
    assert len(assertions) == 3 and all(
        a["source"]["version"] == "110.0" for a in assertions
    )
    assert all(a["source_metadata"]["member_database"] == "cdd" for a in assertions)
    card.to_json(str(tmp_path / "card.json"))
    before = ackredit.get_attribution().to_dict()
    restored = Card.from_json(str(tmp_path / "card.json"))
    assert (
        restored.snapshot_id() == card.snapshot_id()
        and restored.acquisition_trace is None
    )
    assert restored.to_dict() == card.to_dict()
    ackredit.Attribution.from_dict(record["provider"]["attribution"]).report(
        format="bibtex"
    )
    assert ackredit.get_attribution().to_dict() == before
    refreshed, resolution = sabueso.refresh_card(card, **options)
    assert refreshed.acquisition_trace["card_ref"] == refreshed.pinned_ref()
    assert (
        len(
            [
                r
                for r in resolution.acquisition_trace["records"]
                if r["source"] == "InterPro"
            ]
        )
        == 1
    )


def test_provider_failure_nested_collectors_and_custom_client_gaps(monkeypatch):
    serve(monkeypatch)
    with sabueso.attribution() as outer, sabueso.attribution() as inner:
        result = lookup()
    assert (
        outer.acquisitions
        == inner.acquisitions
        == result["acquisition_trace"]["records"]
    )
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic provider failure")),
    )
    with pytest.warns(Warning, match="Attribution failed"):
        result = lookup()
    assert (
        result["record"] == RESIDUES and event(result)["provider"]["status"] == "failed"
    )

    class Custom:
        def site_residues(self, accession):
            return {"residues": RESIDUES, "version": "custom", "retrieved_at": "custom"}

    result = lookup(client=Custom())
    assert result["record"] == RESIDUES and result["acquisition_trace"]["records"] == []
    assert (
        result["acquisition_trace"]["coverage"]["other_sources_and_custom_clients"]
        == "not_observed"
    )


@pytest.mark.parametrize("local", [True, False])
def test_direct_client_envelopes_and_signature_forms_remain_unchanged(
    monkeypatch, tmp_path, local
):
    residues = deepcopy(RESIDUES)
    residues["cd00311"]["accession"] = "different-source-form"
    serve(monkeypatch, payload=residues)
    client = (
        fixture(tmp_path, {"version": "110.0", "residues": residues})
        if local
        else interpro.OnlineInterProClient()
    )
    with sabueso.attribution() as run:
        raw = client.site_residues("P52270")
    assert (
        set(raw) == {"accession", "retrieved_at", "version", "residues"}
        and raw["residues"] == residues
    )
    entry = run.acquisitions[0]["entries"][0]
    assert (
        entry["signature_key"] == "cd00311"
        and entry["signature_metadata"]["accession"] == "different-source-form"
    )


def test_concurrent_annotation_queries_keep_original_contexts(monkeypatch):
    serve(monkeypatch)
    with (
        sabueso.attribution() as run,
        ackredit.capture("parallel annotation queries") as host,
    ):
        results = _http.gather(lookup, ["P52270", "P60174"], workers=2)
    assert {r["query"]["accession"] for r in run.acquisitions} == {"P52270", "P60174"}
    assert {event(result)["query"]["accession"] for _, result in results} == {
        "P52270",
        "P60174",
    }
    assert {
        use["context"]["query"]["accession"]
        for use in host.attribution.to_dict()["uses"]
        if use["context"].get("source") == "InterPro"
    } == {"P52270", "P60174"}
