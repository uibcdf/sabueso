"""Explicit bibliographic support never changes the meaning or rights of a fragment.

Wire cases are synthetic. The frozen public projection contains no abstract; test
fragments are labelled synthetic and do not claim to quote the referenced article.
"""

import io
import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import timedelta
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

import ackredit
import pytest

import sabueso
from sabueso._private.smonitor.warnings import AttributionTrackingWarning
from sabueso.core import attribution as adapter
from sabueso.core.errors import (
    ArgumentError,
    ConnectorError,
    RecordNotFoundError,
    SchemaError,
    StorageError,
)
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.terms import retention
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, europepmc

DATA = Path("temp_data")
REF = "pubmed:40832834"
DOI = "doi:10.1107/s2053230x25006454"
PMC = "pmc:PMC12400196"
SAVED = DATA / "europepmc/articles/pubmed__40832834.json"


@pytest.fixture(autouse=True)
def independent_workflow():
    with ackredit.session("article metadata support"):
        yield


def payload():
    return json.loads(SAVED.read_text(encoding="utf-8"))


class Response(io.BytesIO):
    def __init__(self, body):
        super().__init__(body if isinstance(body, bytes) else json.dumps(body).encode())
        self.status = 200
        self.headers = Message()


def serve(monkeypatch, body=None, error=None):
    calls = []
    monkeypatch.setattr(_http, "_wait", lambda *a: 0)

    def respond(request, timeout):
        calls.append(request)
        if error == "timeout":
            raise URLError(TimeoutError("synthetic timeout"))
        if isinstance(error, int):
            raise HTTPError(request.full_url, error, "synthetic", Message(), None)
        return Response(payload() if body is None else body)

    monkeypatch.setattr(_http, "_urlopen", respond)
    return calls


def event(result):
    trace = (
        result.acquisition_trace
        if isinstance(result, Exception)
        else result["acquisition_trace"]
    )
    (record,) = trace["records"]
    return record


def lookup(identifier=REF, client=None):
    return europepmc.get_article(identifier, client=client)


def metadata():
    return lookup(
        client=europepmc.FixtureEuropePMCClient(
            DATA, retrieved_at="original metadata time"
        )
    )


def extraction(envelope=None, publication=REF, text="α UniProt:P60174"):
    return sabueso.extract_literature_mentions(
        text,
        "P60174",
        publication,
        "Synthetic fragment, not a quotation",
        article_metadata=metadata() if envelope is None else envelope,
    )


def card(**options):
    return sabueso.resolve(
        "P60174", resolver=EntityResolver(FixtureUniProtClient(DATA)), **options
    )[0]


def compose(held, detail="full", aspects=("literature",)):
    return sabueso.compose_packet(
        sabueso.KnowledgeQuery("P60174", aspects=aspects, detail=detail), held
    )


@pytest.mark.parametrize(
    "identifier,native_query",
    [
        (REF, "EXT_ID:40832834 AND SRC:MED"),
        (PMC, 'PMCID:"PMC12400196"'),
        (DOI, 'DOI:"10.1107/s2053230x25006454"'),
        (DOI.upper().replace("DOI:", "doi:"), 'DOI:"10.1107/S2053230X25006454"'),
    ],
)
def test_source_stated_identity_queries_complete_citation_and_service_version(
    monkeypatch, identifier, native_query
):
    calls = serve(monkeypatch)
    with ackredit.capture("host article access") as host:
        result = lookup(identifier)
    params = parse_qs(urlparse(calls[0].full_url).query)
    assert params == {
        "query": [native_query],
        "resultType": ["core"],
        "format": ["json"],
        "pageSize": ["10"],
    }
    record = event(result)
    assert record["query"] == {"identifier": identifier}
    assert record["outcome"] == "received" and record["count"] == 1
    assert record["source_version"] == {"value": "6.9", "basis": "service_version"}
    assert record["article_context"]["article_revision"] == "not_stated"
    assert result["record"]["articles"] == payload()["resultList"]["result"]
    paper = next(c for c in record["bibliography"] if c.get("doi") == DOI[4:])
    assert (
        len(paper["authors"]) == 6 and paper["authors"][2]["family"] == "van der Giezen"
    )
    assert paper["year"] == 2025 and paper["journal"].startswith(
        "Acta crystallographica"
    )
    assert paper["volume"] == "81" and paper["number"] == "Pt 9" and paper["pages"]
    assert record["bibliography_gaps"] == []
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    assert "25006454" in portable.report(format="bibtex")
    assert any(
        "source_publication" in u["roles"] for u in host.attribution.to_dict()["uses"]
    )


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_original_archive_wire_metadata_license_and_time_survive_without_access(
    monkeypatch, tmp_path, mode
):
    original_body = payload()
    original_body["resultList"]["result"][0]["abstractText"] = (
        "Synthetic abstract retained only in private raw archive"
    )
    calls = serve(monkeypatch, original_body)
    archive = sabueso.RetrievalArchive(tmp_path / "answers.db")
    with archive.recording():
        first = lookup()
    assert "abstractText" not in json.dumps(first)
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        later = lookup()
    a, b = event(first), event(later)
    assert len(calls) == 1 and b["network_attempts"] == 0 and b["access"] == mode
    for key in (
        "query",
        "retrieved_at",
        "source_version",
        "response_identity",
        "entries",
        "pages",
        "article_context",
    ):
        assert a[key] == b[key]
    for key in ("response_sha256", "retrieved_at", "retrieval_ref"):
        assert a["requests"][0][key] == b["requests"][0][key]
    assert a["response_identity"]["hash"] == digest(canonical_json(original_body))
    assert later["record"] == first["record"]
    assert retention("Europe PMC")["share"] == "unknown"
    assert retention("Europe PMC")["licence"] == "PUBLICATION-TERMS"


@pytest.mark.parametrize(
    "body,outcome,count",
    [
        ({"version": "6.9", "hitCount": 0, "resultList": {"result": []}}, "empty", 0),
        ({}, "failed", None),
        ([], "failed", None),
        (
            {
                "version": "6.9",
                "hitCount": 1,
                "resultList": {"result": [{"id": "7", "source": "MED"}]},
            },
            "failed",
            0,
        ),
        (b"not JSON", "failed", None),
    ],
)
def test_empty_unrelated_and_unreadable_answers_do_not_invent_article_credit(
    monkeypatch, body, outcome, count
):
    serve(monkeypatch, body)
    with pytest.raises((ConnectorError, RecordNotFoundError)) as caught:
        lookup()
    record = event(caught.value)
    assert record["outcome"] == outcome and record["count"] == count
    assert not any(
        "source_publication" in use["roles"]
        for use in (record["provider"].get("attribution") or {}).get("uses", [])
    )


@pytest.mark.parametrize(
    "error,outcome",
    [(404, "not_found"), (400, "failed"), (500, "failed"), ("timeout", "failed")],
)
def test_failures_keep_original_exception_and_request_attempts(
    monkeypatch, error, outcome
):
    calls = serve(monkeypatch, error=error)
    with pytest.raises((ConnectorError, RecordNotFoundError)) as caught:
        lookup()
    record = event(caught.value)
    assert record["outcome"] == outcome and record["network_attempts"] == len(calls)
    assert record["source_version"]["value"] is None
    assert len(calls) == (3 if error == 500 else 1)


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_evaluated_empty_archive_keeps_original_service_version(
    monkeypatch, tmp_path, mode
):
    calls = serve(
        monkeypatch, {"version": "0", "hitCount": 0, "resultList": {"result": []}}
    )
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    with archive.recording(), pytest.raises(RecordNotFoundError) as first:
        lookup()
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        with pytest.raises(RecordNotFoundError) as second:
            lookup()
    a, b = event(first.value), event(second.value)
    assert len(calls) == 1 and b["access"] == mode and b["count"] == 0
    assert b["source_version"] == {"value": "0", "basis": "service_version"}
    assert (
        a["response_identity"] == b["response_identity"]
        and a["retrieved_at"] == b["retrieved_at"]
    )


@pytest.mark.parametrize(
    "mode,outcome",
    [("fixture", "unavailable"), ("offline", "not_queried"), ("simulated", "failed")],
)
def test_missing_fixture_offline_and_actual_failure_remain_distinct(
    tmp_path, mode, outcome
):
    archive = sabueso.RetrievalArchive(tmp_path / "missing.db")
    client = europepmc.FixtureEuropePMCClient(
        tmp_path, failing=[REF] if mode == "simulated" else []
    )
    with archive.replaying() if mode == "offline" else sabueso.attribution():
        with pytest.raises(Exception) as caught:
            lookup(client=None if mode == "offline" else client)
    record = event(caught.value)
    assert record["outcome"] == outcome and record["network_attempts"] == 0
    assert record["provider"]["status"] == "not_attempted"


def test_partial_and_multiple_matching_metadata_are_retained_but_not_bound(monkeypatch):
    body = payload()
    body["hitCount"] = 2
    calls = serve(monkeypatch, body)
    partial = lookup()
    assert event(partial)["outcome"] == "partial" and event(partial)["count"] == 1
    assert partial["truncated"] is True
    with pytest.raises(SchemaError, match="ambiguous"):
        extraction(partial)
    body["resultList"]["result"].append(
        {**body["resultList"]["result"][0], "title": "Alternative source-stated form"}
    )
    multiple = lookup()
    assert event(multiple)["count"] == 2 and len(multiple["record"]["articles"]) == 2
    with pytest.raises(SchemaError, match="ambiguous"):
        extraction(multiple)
    assert len(calls) == 2


@pytest.mark.parametrize("version", [None, "0", "6.9"])
def test_missing_service_version_is_not_article_revision(monkeypatch, version):
    body = payload()
    body["version"] = version
    serve(monkeypatch, body)
    extracted = extraction(lookup())
    assertion = extracted["article_metadata"]["source_assertion"]
    assert "version" not in assertion["source"]
    assert assertion["source_metadata"]["service_version"] == version
    assert (
        assertion["source_metadata"]["version_basis"]
        == "service_version_not_article_revision"
    )


def test_binding_intake_preserves_literal_support_terms_full_authors_and_reuse():
    meta = metadata()
    before = deepcopy(meta)
    with sabueso.attribution() as observed:
        result = extraction(meta)
    assert observed.acquisitions == [] and meta == before
    binding = result["article_metadata"]
    assert binding["original_acquisition_trace"] == meta["acquisition_trace"]
    sa = binding["source_assertion"]
    assert sa["acquisition"] == {"method": "database"} and sa["subject_ref"] == REF
    assert result["source_assertions"][0]["acquisition"]["method"] == "rule_extraction"
    held = card()
    intake = held.add_literature_extraction(result)
    explanation = held.explain_literature(REF)
    assert (
        explanation["status"] == "on_card"
        and explanation["publication"]["curated"] == []
    )
    (row,) = explanation["publication"]["article_metadata"]
    assert (
        row["rule"] == "article_metadata_binding@1"
        and row["article"] == meta["record"]["articles"][0]
    )
    assert row["terms"] == {
        "state": "declared",
        "scope": "source_declared_article_license",
        "value": "cc by",
        "basis": "Europe_PMC_core_license_field",
        "fragment_terms": "unknown",
        "license_version": "not_inferred",
    }
    assert explanation["source_assertions"][0]["source_assertion_ref"].endswith(
        "#" + sa["id"]
    )
    assert held.source_assertion_store.get(sa["id"]) == sa
    assert intake["original_extraction"] == result["extraction_trace"]
    assert "UniProt:P60174" not in json.dumps(
        sa
    )  # bibliography does not claim our synthetic text
    uses = result["extraction_trace"]["provider"]["attribution"]["uses"]
    assert [
        u["context"]["original_use"] for u in uses if u["roles"] == ["reused_reference"]
    ] == event(meta)["provider"]["attribution"]["uses"]
    terms = held.terms("redistribution")
    assert terms["sources"]["Literature"]["verdict"] == "unknown"
    assert terms["declared_article_terms"][0]["article_terms"] == row["terms"]
    previous = deepcopy(held.to_dict())
    held.add_literature_extraction(result)
    assert held.to_dict() == previous


@pytest.mark.parametrize(
    "change",
    [
        lambda envelope: envelope["record"]["articles"][0].update(pmid="7", id="7"),
        lambda envelope: envelope["record"].update(requested_identifier="pubmed:7"),
        lambda envelope: envelope["record"]["articles"][0].update(
            abstractText="not a metadata projection"
        ),
        lambda envelope: envelope["acquisition_trace"]["records"][0]["query"].update(
            identifier="pubmed:7"
        ),
        lambda envelope: envelope.update(retrieved_at="changed time"),
    ],
)
def test_mismatching_support_and_original_receipts_are_refused_before_extraction(
    change,
):
    envelope = metadata()
    change(envelope)
    before = ackredit.get_attribution().to_dict()
    with pytest.raises(SchemaError):
        extraction(envelope)
    assert ackredit.get_attribution().to_dict() == before


def test_metadata_support_tampering_is_refused_before_card_mutation():
    result = extraction()
    result["article_metadata"]["source_assertion"]["asserted_value"]["title"] = (
        "Forged title"
    )
    held = card()
    previous = deepcopy(held.to_dict())
    with pytest.raises(SchemaError):
        held.add_literature_extraction(result)
    assert held.to_dict() == previous


def test_alternatives_and_identifier_aliases_never_replace_prior_metadata(monkeypatch):
    calls = serve(monkeypatch)
    first = extraction(lookup())
    alias = extraction(lookup(DOI), publication=DOI)
    modified = payload()
    modified["version"] = "7.0"
    modified["resultList"]["result"][0]["title"] = "Alternative native title"
    serve(monkeypatch, modified)
    second = extraction(lookup())
    held = card()
    for result in (first, alias, second):
        held.add_literature_extraction(result)
    rows = next(
        p for p in held.literature()["publications"] if p["publication_ref"] == REF
    )["article_metadata"]
    assert {r["article"]["title"] for r in rows} == {
        first["article_metadata"]["source_assertion"]["asserted_value"]["title"],
        "Alternative native title",
    }
    assert len(rows) == 2 and len(calls) == 2
    for result in (first, alias, second):
        original = result["article_metadata"]["source_assertion"]
        assert held.source_assertion_store.get(original["id"]) == original


@pytest.mark.parametrize(
    "license_value,open_access",
    [(None, "Y"), ("", "Y"), ("cc by-nc", "N"), ("cc by", "Y")],
)
def test_literal_license_and_open_access_never_grant_fragment_permission(
    monkeypatch, license_value, open_access
):
    body = payload()
    body["resultList"]["result"][0].update(
        license=license_value, isOpenAccess=open_access
    )
    serve(monkeypatch, body)
    result = extraction(lookup())
    assert result["extraction_trace"]["terms"]["state"] == "unknown"
    held = card(terms="non_commercial")
    previous = deepcopy(held.to_dict())
    with pytest.raises(SchemaError, match="terms-profile"):
        held.add_literature_extraction(result)
    assert held.to_dict() == previous
    plain = card()
    plain.add_literature_extraction(result)
    report = plain.terms("commercial_product")
    declaration = report["declared_article_terms"][0]["article_terms"]
    assert (
        declaration["value"] == license_value
        and declaration["license_version"] == "not_inferred"
    )
    assert report["sources"]["Literature"]["verdict"] == "unknown"


def test_store_replay_card_refresh_and_saved_packet_citations_remain_inert(
    tmp_path, monkeypatch
):
    result = extraction()
    store = sabueso.ExtractionStore(tmp_path / "fragments.jsonl")
    store.save(result)
    knowledge = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    held = card(extractions=store)
    pin = knowledge.save(held)
    packet = compose(held)
    original = result["article_metadata"]["source_assertion"]
    paper = next(
        c for c in packet.attribution["bibliography"] if c.get("doi") == DOI[4:]
    )
    assert len(paper["authors"]) == 6
    assert any(
        "source_publication" in u["roles"]
        for u in packet.attribution["provider"]["attribution"]["uses"]
    )
    monkeypatch.setattr(
        europepmc,
        "get_article",
        lambda *a, **kw: pytest.fail("reader/refresh must not consult metadata"),
    )
    monkeypatch.setattr(
        sabueso,
        "extract_literature_mentions",
        lambda *a, **kw: pytest.fail("reader/refresh must not extract"),
    )
    with ackredit.session("independent saved reader"):
        before = ackredit.get_attribution().to_dict()
        assert store.records() == [result]
        loaded = knowledge.load(pin)
        assert loaded.explain_literature(REF) == held.explain_literature(REF)
        assert loaded.terms("redistribution") == held.terms("redistribution")
        detached = sabueso.KnowledgePacket(packet.to_dict())
        assert detached.attribution is None
        assert detached.terms("redistribution", store=knowledge)[
            "declared_article_terms"
        ]
        assert ackredit.get_attribution().to_dict() == before
    refreshed, _ = sabueso.refresh_card(
        loaded, resolver=EntityResolver(FixtureUniProtClient(DATA)), store=knowledge
    )
    assert refreshed.source_assertion_store.get(original["id"]) == original
    assert (
        refreshed.quality["literature_extractions"]
        == held.quality["literature_extractions"]
    )
    assert refreshed.literature_intake_traces[0]["provider"]["status"] == "not_recorded"
    assert knowledge.load(pin).to_dict() == held.to_dict()


def test_full_and_index_terms_use_same_exact_metadata_support_and_exclude_other_aspects(
    tmp_path,
):
    held = card()
    held.add_literature_extraction(extraction())
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    pin = store.save(held)
    full, index, identity = (
        compose(held),
        compose(held, "index"),
        compose(held, aspects=("identity",)),
    )
    a, b = [p.terms("redistribution", store=store) for p in (full, index)]
    assert (
        a["scope"] == b["scope"]
        and a["declared_article_terms"] == b["declared_article_terms"]
    )
    assert a["declared_article_terms"][0]["source_assertion_ref"].startswith(pin + "#")
    assert not any(
        c.get("doi") == DOI[4:] for c in identity.attribution["bibliography"]
    )
    assert "declared_article_terms" not in identity.terms("redistribution", store=store)


def test_missing_metadata_support_remains_partial_and_cannot_be_refreshed(tmp_path):
    held = card()
    result = extraction()
    held.add_literature_extraction(result)
    identifier = result["article_metadata"]["source_assertion"]["id"]
    del held.source_assertion_store.store[identifier]
    assert held.explain_literature(REF)["status"] == "partial"
    assert (
        held.explain_literature(REF)["publication"]["article_metadata"][0]["found"]
        is False
    )
    with pytest.raises(SchemaError, match="missing or inconsistent original"):
        sabueso.refresh_card(held, resolver=EntityResolver(FixtureUniProtClient(DATA)))
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(held)
    with pytest.warns(AttributionTrackingWarning):
        packet = compose(held)
    with pytest.raises(StorageError, match="missing SourceAssertion"):
        packet.terms("redistribution", store=store)


def test_metadata_without_literal_match_does_not_claim_any_article_mention():
    held = card(terms="non_commercial")
    held.add_literature_extraction(
        extraction(text="No accession in this synthetic fragment")
    )
    assert held.relationships("mentioned_in", REF) == []
    publication = next(
        p for p in held.literature()["publications"] if p["publication_ref"] == REF
    )
    assert publication["mentions"] == [] and publication["article_metadata"]
    assert held.quality["literature_extractions"][0]["source_assertion_ids"] == []


def test_custom_missing_original_credit_and_provider_failure_preserve_science(
    monkeypatch,
):
    class Custom:
        def article(self, identifier):
            from sabueso.core.article_metadata import response

            return {
                "record": response(payload(), identifier),
                "version": "6.9",
                "retrieved_at": "custom declared time",
            }

    envelope = lookup(client=Custom())
    result = extraction(envelope)
    assert (
        "original_metadata_attribution_not_available"
        in result["extraction_trace"]["bibliography_gaps"]
    )
    held = card()
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: (_ for _ in ()).throw(RuntimeError("provider unavailable")),
    )
    with pytest.warns(AttributionTrackingWarning):
        extracted = extraction(metadata())
    assert extracted["extraction_trace"]["provider"]["status"] == "failed"
    with pytest.warns(AttributionTrackingWarning):
        held.add_literature_extraction(result)
    assert held.source_assertion_store.get(
        result["article_metadata"]["source_assertion"]["id"]
    )


@pytest.mark.parametrize(
    "identifier", ["P60174", "40832834", "pubmed:0", "PMC:PMC12400196", "doi:garbage"]
)
def test_invalid_identifier_arguments_are_refused_before_network(
    monkeypatch, identifier
):
    calls = serve(monkeypatch)
    with pytest.raises(ArgumentError):
        lookup(identifier)
    assert calls == []


def test_invalid_metadata_argument_is_refused():
    with pytest.raises(ArgumentError):
        sabueso.extract_literature_mentions(
            "UniProt:P60174", "P60174", REF, "Synthetic", article_metadata=[]
        )


def test_concurrent_explicit_queries_keep_separate_identity_and_original_hash(
    monkeypatch,
):
    serve(monkeypatch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lookup, [REF, DOI]))
    assert [event(r)["query"]["identifier"] for r in results] == [REF, DOI]
    assert len({event(r)["id"] for r in results}) == 2
    assert all(event(r)["count"] == 1 for r in results)


@pytest.mark.parametrize(
    "body,expected",
    [
        ({"version": "6.9", "hitCount": 0, "resultList": {"result": []}}, "empty"),
        ({}, "failed"),
        (b"not JSON", "failed"),
    ],
)
def test_fixture_empty_and_invalid_records_keep_distinct_observation(
    tmp_path, body, expected
):
    directory = tmp_path / "europepmc/articles"
    directory.mkdir(parents=True)
    (directory / "pubmed__40832834.json").write_bytes(
        body if isinstance(body, bytes) else json.dumps(body).encode()
    )
    client = europepmc.FixtureEuropePMCClient(tmp_path)
    if expected == "empty":
        record = event(lookup(client=client))
        assert record["count"] == 0
    else:
        with pytest.raises((ConnectorError, ValueError)) as caught:
            lookup(client=client)
        record = event(caught.value)
    assert record["outcome"] == expected and record["network_attempts"] == 0


def test_incomplete_bibliography_retains_native_author_string_and_explicit_gaps(
    monkeypatch,
):
    body = payload()
    article = body["resultList"]["result"][0]
    del article["authorList"]
    del article["pubYear"]
    calls = serve(monkeypatch, body)
    result = extraction(lookup())
    assert (
        "author_list_not_returned_preserved_native_author_string"
        in result["extraction_trace"]["bibliography_gaps"]
    )
    assert "article_year_not_stated" in result["extraction_trace"]["bibliography_gaps"]
    paper = next(
        i
        for i in result["extraction_trace"]["provider"]["attribution"]["items"]
        if i.get("doi") == DOI[4:]
    )
    assert paper["authors"] == [{"literal": article["authorString"]}]
    assert "year" not in paper and len(calls) == 1
    # A PMID URL cannot be invented from a MED label with no native id.
    for key in ("id", "pmid", "doi"):
        article.pop(key, None)
    serve(monkeypatch, body)
    record = event(lookup(PMC))
    publication = next(
        i
        for i in record["bibliography"]
        if i["id"].startswith("sabueso:article-publication:")
    )
    assert "url" not in publication and "doi" not in publication


def test_received_subset_before_invalid_record_credits_only_received_metadata(
    monkeypatch,
):
    body = payload()
    body["hitCount"] = 2
    body["resultList"]["result"].append(
        {"id": "7", "source": "MED", "doi": "10.1234/unrelated"}
    )
    serve(monkeypatch, body)
    with pytest.raises(ConnectorError) as caught:
        lookup()
    record = event(caught.value)
    assert record["outcome"] == "partial" and record["count"] == 1
    assert [e["outcome"] for e in record["entries"]] == ["received", "unobserved"]
    assert any(c.get("doi") == DOI[4:] for c in record["bibliography"])
    assert not any(c.get("doi") == "10.1234/unrelated" for c in record["bibliography"])


def test_metadata_does_not_overwrite_citations_or_host_bibliography():
    host_item = {
        "id": "host:article",
        "type": "article",
        "doi": DOI[4:],
        "title": "Host fuller form",
        "year": 2025,
    }
    ackredit.register_item(**host_item)
    ackredit.track_item("host:article", roles=["source_publication"])
    held = card()
    result = extraction()
    held.add_literature_extraction(result)
    pub = next(
        p for p in held.literature()["publications"] if p["publication_ref"] == REF
    )
    assert pub["title"] is None and pub["article_metadata"][0]["article"]["title"]
    assert (
        next(
            i
            for i in ackredit.get_attribution().to_dict()["items"]
            if i["id"] == "host:article"
        )
        == host_item
    )


@pytest.mark.parametrize(
    "name",
    ["Synthetic Research Group", "Synthetic A and B, Consortium", "Synthetic Équipe"],
)
def test_collective_authors_keep_native_order_and_indivisible_names(name):
    from sabueso.core.article_metadata import citations

    article = {
        "authorString": "Compact native string must not replace the returned list",
        "authorList": {
            "author": [
                {"fullName": "Person A", "lastName": "Person", "firstName": "A"},
                {"collectiveName": name},
                {"fullName": "Person B", "lastName": "Person", "firstName": "B"},
            ]
        },
    }
    original = deepcopy(article)
    (citation,), gaps = citations([article])
    assert citation["authors"] == [
        {"family": "Person", "given": "A"},
        {"literal": name},
        {"family": "Person", "given": "B"},
    ]
    assert "author_list_not_returned_preserved_native_author_string" not in gaps
    assert article == original
    ackredit.register_item(**citation)
    ackredit.track_item(citation["id"])
    csl = json.loads(ackredit.get_attribution().report(format="csl-json"))
    assert next(item for item in csl if item["id"] == citation["id"])["author"][1] == {
        "literal": name
    }


def test_all_collective_authors_are_preserved_without_a_compact_author_string():
    from sabueso.core.article_metadata import citations

    article = {
        "authorList": {
            "author": [
                {"collectiveName": "Synthetic Group A"},
                {"collectiveName": "Synthetic Group B"},
            ]
        }
    }
    (citation,), gaps = citations([article])
    assert citation["authors"] == [
        {"literal": "Synthetic Group A"},
        {"literal": "Synthetic Group B"},
    ]
    assert "article_authors_not_stated" not in gaps


def test_public_mixed_author_list_preserves_every_person_and_collective_author():
    result = europepmc.get_article(
        "pubmed:26323937", client=europepmc.FixtureEuropePMCClient(DATA)
    )
    article = result["record"]["articles"][0]
    original = json.loads(
        (DATA / "europepmc/articles/pubmed__26323937.json").read_text(encoding="utf-8")
    )["resultList"]["result"][0]
    assert article == original
    record = result["acquisition_trace"]["records"][0]
    bibliography = next(
        item
        for item in record["bibliography"]
        if item.get("doi", "").casefold() == "10.1056/nejmoa1507574"
    )
    assert len(bibliography["authors"]) == len(original["authorList"]["author"]) == 22
    assert bibliography["authors"][-1] == {"literal": "BENEFIT Investigators"}
    assert (
        "author_list_not_returned_preserved_native_author_string"
        not in record["bibliography_gaps"]
    )
