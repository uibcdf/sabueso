"""PubChem access preserves source revisions, original pointers and failure scope.

HTTP responses below are synthetic protocol examples; frozen compound/assay data
used by the fixture-client tests are public and declared in temp_data/NOTICE.md.
"""

import io
import json
from datetime import timedelta
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs

import ackredit
import pytest

import sabueso
from sabueso.core import attribution as adapter
from sabueso.core.card import Card
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, pubchem, pubchem_bioassay

DATA = Path("temp_data")


@pytest.fixture(autouse=True)
def independent_workflow():
    with ackredit.session("PubChem observation regression"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload):
        super().__init__(
            (payload if isinstance(payload, str) else json.dumps(payload)).encode()
        )
        self.headers = Message()


def serve(monkeypatch, *, error=None, fail_at=None, empty=False, rows=2):
    calls = []
    monkeypatch.setattr(_http.time, "sleep", lambda _: None)
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)
    monkeypatch.setattr(pubchem_bioassay.time, "sleep", lambda _: None)

    def response(request, timeout):
        calls.append(request)
        url = request.full_url
        if error or (fail_at and fail_at(url)):
            if error == "timeout":
                raise URLError(TimeoutError("slow synthetic response"))
            code = error or 500
            raise HTTPError(
                url,
                code,
                "synthetic failure",
                Message(),
                io.BytesIO(b'{"Fault":{"Message":"synthetic invalid structure"}}'),
            )
        if url.endswith("concise/CSV"):
            return Response(
                "AID,SID,CID,Target Accession,Activity Value [uM],Assay Type,PubMed ID\n"
                + "".join(
                    f"{i},{i},{i},P60174,{i},Confirmatory,{i}\n"
                    for i in range(1, (0 if empty else rows) + 1)
                )
                + ("" if empty else "999,999,999,P52270,1,Confirmatory,999\n")
            )
        if "/summary/" in url:
            aids = url.split("/aid/")[1].split("/")[0].split(",")
            return Response(
                {
                    "AssaySummaries": {
                        "AssaySummary": [
                            {
                                "AID": int(a),
                                "Version": 1,
                                "Revision": 0,
                                "LastDataChange": {"Year": 2025, "Month": 1, "Day": 1},
                                "SourceName": "ChEMBL",
                                "SourceID": "synthetic-assay-" + a,
                            }
                            for a in aids
                        ]
                    }
                }
            )
        if "/property/InChIKey/" in url:
            cids = url.split("/cid/")[1].split("/")[0].split(",")
            return Response(
                {
                    "PropertyTable": {
                        "Properties": [
                            {"CID": int(c), "InChIKey": "SYNTHETIC-NOT-AN-IDENTITY"}
                            for c in cids
                        ]
                    }
                }
            )
        if "/property/" in url:
            return Response(
                {
                    "PropertyTable": {
                        "Properties": []
                        if empty
                        else [{"CID": 5978, "MolecularFormula": "C46H56N4O10"}]
                    }
                }
            )
        assert request.get_method() == "POST"
        assert parse_qs(request.data.decode()) == {"smiles": ["C/C=C\\C"]}
        return Response({"IdentifierList": {"CID": [0] if empty else [5978]}})

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def lookup(kind):
    if kind == "compound":
        return pubchem.get_compound("5978")
    if kind == "structure":
        return pubchem.get_structure_match("C/C=C\\C")
    return pubchem_bioassay.get_assays("P60174", limit=2)


def record(result):
    (observed,) = result["acquisition_trace"]["records"]
    return observed


@pytest.mark.parametrize("kind", ["compound", "structure", "assays"])
def test_native_queries_responses_and_distinct_citation_roles(monkeypatch, kind):
    calls = serve(monkeypatch)
    result = lookup(kind)
    observed = record(result)
    assert observed["outcome"] == "received"
    assert observed["count"] == (2 if kind == "assays" else 1)
    assert observed["network_attempts"] == len(calls)
    assert all(r.get("response_sha256") for r in observed["requests"])
    assert observed["provider"]["status"] == "available"
    portable = ackredit.Attribution.from_dict(observed["provider"]["attribution"])
    assert "PubChem 2025 update" in portable.report(format="text")
    uses = portable.to_dict()["uses"]
    assert any("resource_description" in u["roles"] for u in uses)
    assert any("resource_access" in u["roles"] for u in uses)
    if kind == "assays":
        assert observed["query"] == {"accession": "P60174", "limit": 2}
        assert observed["source_version"]["basis"] == "per_assay_revision"
        assert observed["source_version"]["value"]["1"]["Revision"] == 0
        assert observed["assays"][0]["depositor"]["SourceName"] == "ChEMBL"
        assert observed["publication_ids"] == ["1", "2"]
        assert observed["total_count"] == 2 and not observed["truncated"]
        assert observed["row_order"] == "pubchem_row_order@1"
        assert any("measurement_primary_citation" in u["roles"] for u in uses)
        pointers = [
            b
            for b in observed["bibliography"]
            if b["id"].startswith("sabueso:pubchem-primary-citation:")
        ]
        assert len(pointers) == 2 and all(
            "authors" not in p and "title" not in p for p in pointers
        )
        assert (
            "assay_depositor_bibliography_not_declared" in observed["bibliography_gaps"]
        )
        assert not any(
            b.get("doi") == "10.1093/nar/gkad1004" for b in observed["bibliography"]
        )
    else:
        assert observed["source_version"] == {"value": None, "basis": "not_stated"}
        assert observed["query"] == (
            {"cid": "5978"}
            if kind == "compound"
            else {"notation": "smiles", "structure": "C/C=C\\C"}
        )
        if kind == "structure":
            assert observed["requests"][0]["method"] == "POST"
            assert observed["requests"][0]["request_sha256"]


@pytest.mark.parametrize("mode", ["reuse", "replay"])
@pytest.mark.parametrize("kind", ["compound", "structure", "assays"])
def test_archive_preserves_original_responses_revisions_and_retrieval_times(
    tmp_path, monkeypatch, mode, kind
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "responses.db")
    with archive.recording():
        original = lookup(kind)
    count = len(calls)
    manager = (
        archive.replaying() if mode == "replay" else archive.reusing(timedelta(days=1))
    )
    with manager:
        reused = lookup(kind)
    one, two = record(original), record(reused)
    assert len(calls) == count and two["network_attempts"] == 0
    assert two["access"] == mode
    assert original["record"] == reused["record"]
    for key in (
        "retrieved_at",
        "source_version",
        "response_identity",
        "pages",
        "bibliography",
    ):
        assert one[key] == two[key]
    assert [r["retrieval_ref"] for r in one["requests"]] == [
        r["retrieval_ref"] for r in two["requests"]
    ]


def test_bioassay_chunks_and_caps_do_not_hide_source_rows(monkeypatch):
    calls = serve(monkeypatch, rows=101)
    result = pubchem_bioassay.get_assays("P60174", limit=101)
    observed = record(result)
    assert len(calls) == 6  # one CSV, three summary chunks, two compound chunks
    assert [p["count"] for p in observed["pages"]] == [101, 50, 50, 1, 100, 1]
    assert observed["pages"][0]["returned_rows"] == 102  # another target stays separate
    calls = serve(monkeypatch, rows=2)
    result = pubchem_bioassay.get_assays("P60174", limit=1)
    observed = record(result)
    assert (
        observed["count"] == 1
        and observed["total_count"] == 2
        and observed["truncated"]
    )
    assert len(observed["aids"]) == 2 and len(observed["assays"]) == 1
    assert observed["publication_ids"] == ["1"]


@pytest.mark.parametrize(
    "stage,error", [("summary", 500), ("properties", 500), ("properties", 404)]
)
def test_received_rows_and_revisions_survive_later_failure(monkeypatch, stage, error):
    serve(
        monkeypatch,
        fail_at=lambda u: "/summary/" in u if stage == "summary" else "/property/" in u,
    )
    if error == 404:
        serve(monkeypatch, fail_at=lambda u: "/property/" in u)
        original = _http._urlopen

        def missing(request, timeout):
            if "/property/" in request.full_url:
                raise HTTPError(
                    request.full_url, 404, "synthetic missing compound", Message(), None
                )
            return original(request, timeout)

        monkeypatch.setattr(_http, "_urlopen", missing)
    expected = RecordNotFoundError if error == 404 else ConnectorError
    with sabueso.attribution() as run, pytest.raises(expected):
        pubchem_bioassay.get_assays("P60174")
    (observed,) = run.acquisitions
    assert observed["outcome"] == "partial" and observed["incomplete"]
    assert observed["count"] == 2
    assert observed["count_basis"] == "received_target_rows_before_completion"
    assert observed["provider"]["status"] == "available"
    assert observed["publication_ids"] == ["1", "2"]
    assert observed["requests"][-1]["outcome"] == "failed"
    assert observed["source_version"]["basis"] == (
        "not_stated" if stage == "summary" else "per_assay_revision"
    )


@pytest.mark.parametrize("kind", ["compound", "structure", "assays"])
def test_empty_received_response_has_no_positive_statement(monkeypatch, kind):
    serve(monkeypatch, empty=True)
    if kind == "assays":
        with pytest.raises(RecordNotFoundError) as caught:
            lookup(kind)
        observed = caught.value.acquisition_trace["records"][0]
    else:
        observed = record(lookup(kind))
    assert observed["outcome"] == "empty" and observed["count"] == 0
    assert observed["provider"]["status"] == "available"


@pytest.mark.parametrize("kind", ["compound", "structure", "assays"])
@pytest.mark.parametrize(
    "error,outcome",
    [(404, "not_found"), (400, "rejected"), (500, "failed"), ("timeout", "failed")],
)
def test_absence_rejection_and_failure_are_distinct(monkeypatch, kind, error, outcome):
    serve(monkeypatch, error=error)
    if kind == "structure" and error in {400, 404}:
        result = lookup(kind)
        observed = record(result)
        assert result["record"]["cids"] == []
        assert bool(result["record"]["fault"]) == (error == 400)
    else:
        expected = (
            RecordNotFoundError
            if error == 404 or (error == 400 and kind == "compound")
            else ConnectorError
        )
        with pytest.raises(expected) as caught:
            lookup(kind)
        observed = caught.value.acquisition_trace["records"][0]
    # BioAssay still treats HTTP 400 as a connector failure, preserving its API.
    assert observed["outcome"] == (
        "failed" if kind == "assays" and error == 400 else outcome
    )
    assert observed["provider"]["status"] == (
        "available" if error == 404 else "not_attempted"
    )


def test_fixture_unavailability_and_unqueried_archive_are_not_absence(tmp_path):
    for call in (
        lambda: pubchem.get_compound(
            "5978", client=pubchem.FixturePubChemClient(tmp_path)
        ),
        lambda: pubchem.get_structure_match(
            "C", client=pubchem.FixturePubChemClient(tmp_path)
        ),
        lambda: pubchem_bioassay.get_assays(
            "P60174", client=pubchem_bioassay.FixturePubChemBioAssayClient(tmp_path)
        ),
    ):
        with pytest.raises(RecordNotFoundError) as caught:
            call()
        assert caught.value.acquisition_trace["records"][0]["outcome"] == "unavailable"
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    with archive.replaying(), pytest.raises(ConnectorError) as caught:
        pubchem.get_compound("5978")
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "not_queried"


def test_fixture_cards_refresh_and_saved_readers_preserve_scientific_payload(tmp_path):
    client = pubchem_bioassay.FixturePubChemBioAssayClient(DATA)
    card, resolution = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient(DATA)),
        pubchem_bioassay=True,
        pubchem_bioassay_client=client,
    )
    observed = next(
        r
        for r in card.acquisition_trace["records"]
        if r["source"] == "PubChem BioAssay"
    )
    assert observed["access"] == "fixture" and observed["network_attempts"] == 0
    assert observed["source_version"]["value"]["214625"]["Revision"] == 1
    assert observed["assays"][0]["depositor"]["SourceName"] == "ChEMBL"
    assert card.acquisition_trace == resolution.acquisition_trace
    assert "acquisition_trace" not in card.to_dict()
    card.to_json(str(tmp_path / "card.json"))
    before = ackredit.get_attribution().to_dict()
    restored = Card.from_json(str(tmp_path / "card.json"))
    portable = ackredit.Attribution.from_dict(observed["provider"]["attribution"])
    assert "PubChem 2025 update" in portable.report(format="text")
    assert (
        restored.snapshot_id() == card.snapshot_id()
        and restored.acquisition_trace is None
    )
    assert (
        json.loads(json.dumps(observed))["source_version"] == observed["source_version"]
    )
    assert ackredit.get_attribution().to_dict() == before
    refreshed, resolution = sabueso.refresh_card(
        card,
        resolver=EntityResolver(FixtureUniProtClient(DATA)),
        pubchem_bioassay_client=client,
    )
    assert refreshed.acquisition_trace["card_ref"] == refreshed.pinned_ref()
    assert any(
        r["source"] == "PubChem BioAssay"
        for r in resolution.acquisition_trace["records"]
    )


def test_provider_failure_keeps_original_response_and_custom_client_gap(monkeypatch):
    serve(monkeypatch)
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic provider failure")),
    )
    with pytest.warns(Warning, match="Attribution failed"):
        result = pubchem.get_compound("5978")
    assert result["record"]["PropertyTable"]["Properties"][0]["CID"] == 5978
    assert record(result)["provider"]["status"] == "failed"

    class Custom:
        def compound(self, cid):
            return {"retrieved_at": "fixture", "record": {"synthetic": cid}}

    result = pubchem.get_compound("5978", client=Custom())
    assert result["acquisition_trace"]["records"] == []
    assert (
        result["acquisition_trace"]["coverage"]["other_sources_and_custom_clients"]
        == "not_observed"
    )


def test_recovered_http_and_unreadable_json_attempts_are_retained(monkeypatch):
    calls = serve(monkeypatch)
    original = _http._urlopen
    attempts = []

    def intermittent(request, timeout):
        attempts.append(request)
        if len(attempts) == 1:
            raise HTTPError(
                request.full_url, 500, "synthetic transient failure", Message(), None
            )
        if len(attempts) == 2:
            return Response("synthetic unreadable JSON")
        return original(request, timeout)

    monkeypatch.setattr(_http, "_urlopen", intermittent)
    observed = record(pubchem.get_compound("5978"))
    assert observed["outcome"] == "received"
    assert observed["network_attempts"] == 3 and len(calls) == 1
    assert [reason for r in observed["requests"] for reason in r["retries"]] == [
        "HTTP 500",
        "unreadable_body",
    ]
    assert len(observed["pages"]) == 1


def test_fixture_compound_shapes_structure_faults_and_context_isolation(tmp_path):
    client = pubchem.FixturePubChemClient(DATA)
    with sabueso.attribution() as outer:
        legacy = record(pubchem.get_compound("5978", client=client))
        with sabueso.attribution() as inner:
            table = record(pubchem.get_compound("3717450", client=client))
    assert legacy["outcome"] == table["outcome"] == "received"
    assert legacy["count"] == table["count"] == 1
    assert len(outer.acquisitions) == 2 and len(inner.acquisitions) == 1
    assert outer.acquisitions[1] == inner.acquisitions[0]
    assert inner.acquisitions[0]["access"] == "fixture"
    lookups = json.loads((DATA / "pubchem" / "structures.json").read_text())["lookups"]
    for saved in lookups:
        result = pubchem.get_structure_match(
            saved["query"], notation=saved["kind"], client=client
        )
        observed = record(result)
        assert observed["outcome"] == (
            "rejected"
            if result["record"]["fault"]
            else "received"
            if result["record"]["cids"]
            else "empty"
        )
    directory = tmp_path / "pubchem_bioassay"
    directory.mkdir()
    (directory / "P60174.json").write_text(
        json.dumps({"concise": {}, "summaries": [], "inchikeys": {}})
    )
    empty = record(
        pubchem_bioassay.get_assays(
            "P60174", client=pubchem_bioassay.FixturePubChemBioAssayClient(tmp_path)
        )
    )
    assert empty["outcome"] == "empty" and empty["count"] == 0


def test_missing_assay_revision_remains_unknown_and_zero_versions_survive(monkeypatch):
    serve(monkeypatch)
    original = _http._urlopen

    def versions(request, timeout):
        if "/summary/" in request.full_url:
            return Response(
                {
                    "AssaySummaries": {
                        "AssaySummary": [
                            {"AID": 1, "Version": 0, "Revision": 0},
                            {"AID": 2, "Version": 1},
                        ]
                    }
                }
            )
        return original(request, timeout)

    monkeypatch.setattr(_http, "_urlopen", versions)
    observed = record(pubchem_bioassay.get_assays("P60174"))
    assert observed["source_version"]["value"] == {"1": {"Version": 0, "Revision": 0}}
    assert observed["assays"][1]["source_version"] == {
        "value": None,
        "basis": "not_stated",
    }
    assert observed["assays"][1]["revision_metadata"] == {"Version": 1}


def test_incomplete_pubmed_pointer_preserves_previously_credited_full_citation(
    monkeypatch,
):
    serve(monkeypatch)
    with ackredit.capture("host with an original publication") as host:
        original = {
            "id": "pubmed:1",
            "type": "article",
            "title": "Synthetic original citation",
            "authors": ["Example, A"],
            "year": 2020,
        }
        ackredit.register_item(**original)
        ackredit.track_item("pubmed:1", roles=["original_reference"])
        observed = record(pubchem_bioassay.get_assays("P60174"))
    assert observed["provider"]["status"] == "available"
    items = {item["id"]: item for item in host.attribution.to_dict()["items"]}
    assert items["pubmed:1"] == original
    pointer = next(
        b
        for b in observed["bibliography"]
        if b.get("url") == "https://pubmed.ncbi.nlm.nih.gov/1/"
    )
    assert pointer["id"] != "pubmed:1" and items[pointer["id"]] == pointer
    assert "PubChem 2025 update" in host.attribution.report(format="bibtex")
