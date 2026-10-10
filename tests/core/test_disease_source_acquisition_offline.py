"""Native association acquisition scopes; synthetic wire answers and public fixtures."""

import io
import json
from contextlib import nullcontext
from copy import deepcopy
from datetime import timedelta
from email.message import Message
from hashlib import sha256
from urllib.error import HTTPError, URLError

import ackredit
import pytest

import sabueso
from sabueso.core import attribution as adapter
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import (
    _http,
    _mirror,
    _release,
)
from sabueso.tools.db import (
    open_targets as ot,
)
from sabueso.tools.db import (
    orphadata as orpha,
)

XML = b"""<?xml version="1.0"?><JDBOR date="2026-06-23 07:00:00"><DisorderList count="1">
<Disorder><OrphaCode>868</OrphaCode><Name>synthetic</Name><DisorderGeneAssociationList>
<DisorderGeneAssociation><Gene><Symbol>TPI1</Symbol><ExternalReferenceList>
<ExternalReference><Source>SwissProt</Source><Reference>P60174</Reference></ExternalReference>
</ExternalReferenceList></Gene><SourceOfValidation>1234[PMID]_5678[PMID]</SourceOfValidation>
</DisorderGeneAssociation></DisorderGeneAssociationList></Disorder></DisorderList></JDBOR>"""


@pytest.fixture(autouse=True)
def independent_run():
    _release.forget("Orphanet")
    with ackredit.session("disease source observation"):
        yield
    _release.forget("Orphanet")


class Response(io.BytesIO):
    def __init__(self, payload):
        super().__init__(payload)
        self.status = 200
        self.headers = Message()


def serve(monkeypatch, answer):
    calls = []
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)

    def respond(request, timeout):
        calls.append(request)
        value = answer(request, len(calls)) if callable(answer) else answer
        if isinstance(value, Exception):
            raise value
        return Response(
            value if isinstance(value, bytes) else json.dumps(value).encode()
        )

    monkeypatch.setattr(_http, "_urlopen", respond)
    return calls


def page(direction="targets", rows=None, count=0, version=True):
    if direction == "targets":
        entity, collection = "disease", "associatedTargets"
        native = {"id": "MONDO_0014221", "name": "synthetic"}
    else:
        entity, collection = "target", "associatedDiseases"
        native = {"id": "ENSG00000111669", "approvedSymbol": "TPI1", "proteinIds": []}
    native[collection] = {"count": count, "rows": rows or []}
    return {
        "data": {
            entity: native,
            "meta": {"dataVersion": {"year": 2026, "month": 9, "iteration": 1}}
            if version
            else {},
        }
    }


def target_row(identifier="ENSG1"):
    return {
        "score": 0.8,
        "datatypeScores": [{"id": "genetic_association", "score": 0.7}],
        "target": {
            "id": identifier,
            "approvedSymbol": "x",
            "proteinIds": [{"id": "P60174", "source": "uniprot_swissprot"}],
        },
    }


def only(run):
    (record,) = run.acquisitions
    assert "recording_error" not in record
    return record


def test_open_targets_pages_original_order_limit_version_and_host_bibliography(
    monkeypatch,
):
    monkeypatch.setattr(ot, "PAGE_SIZE", 2)
    pages = [
        page(rows=[target_row("ENSG1"), target_row("ENSG2")], count=4),
        page(rows=[target_row("ENSG3"), target_row("ENSG4")], count=4),
    ]
    calls = serve(monkeypatch, lambda request, n: pages[n - 1])
    with sabueso.attribution() as run, ackredit.capture("host") as host:
        result = ot.OnlineOpenTargetsClient().targets("MONDO:0014221", limit=3)
    record = only(run)
    assert record["query"] == {"disease": "MONDO:0014221", "limit": 3}
    assert record["normalized_query"]["disease"] == "MONDO_0014221"
    assert [json.loads(c.data)["variables"]["index"] for c in calls] == [0, 1]
    assert record["row_order"] == ["ENSG1", "ENSG2", "ENSG3"]
    assert record["count"] == 3 and record["total_count"] == 4 and record["truncated"]
    assert [p["count"] for p in record["completed_pages"]] == [2, 2]
    assert record["source_version"] == {
        "value": "2026.9.1",
        "basis": "graphql_meta_data_version",
    }
    assert record["response_identity"]["hash"] == digest(
        canonical_json(result["record"])
    )
    paper = next(
        b for b in record["bibliography"] if b.get("doi") == "10.1093/nar/gkae1128"
    )
    assert len(paper["authors"]) == 32 and paper["year"] == 2025
    assert any(
        u["context"].get("association_context") == record["association_context"]
        for u in host.attribution.to_dict()["uses"]
    )
    assert "gkae1128" in ackredit.Attribution.from_dict(
        record["provider"]["attribution"]
    ).report(format="bibtex")


@pytest.mark.parametrize("direction", ["targets", "associations"])
@pytest.mark.parametrize("absence", ["empty", "unknown", "unstated_version"])
def test_open_targets_evaluated_empty_is_distinct_from_unknown_version(
    monkeypatch, direction, absence
):
    answer = page(direction, version=absence != "unstated_version")
    if absence == "unknown":
        answer["data"]["disease" if direction == "targets" else "target"] = None
    serve(monkeypatch, answer)
    with sabueso.attribution() as run:
        if absence == "unknown":
            with pytest.raises(RecordNotFoundError):
                getattr(ot.OnlineOpenTargetsClient(), direction)("query")
        else:
            result = getattr(ot.OnlineOpenTargetsClient(), direction)("query")
            assert result["record"]["rows"] == []
    record = only(run)
    assert record["outcome"] == "empty" and record["count"] == 0
    assert record["provider"]["status"] == "available"
    if absence == "unstated_version":
        assert record["source_version"] == {"value": None, "basis": "not_stated"}


@pytest.mark.parametrize(
    "error",
    ["graphql", "missing_entity", "missing_collection", "invalid_json", "timeout"],
)
def test_open_targets_invalid_or_unanswered_queries_never_become_absence(
    monkeypatch, error
):
    answer = (
        {"errors": [{"message": "synthetic"}]}
        if error == "graphql"
        else {"data": {}}
        if error == "missing_entity"
        else b"{bad"
        if error == "invalid_json"
        else URLError(TimeoutError("synthetic"))
        if error == "timeout"
        else {"data": {"disease": {"id": "x", "name": "x"}}}
    )
    calls = serve(monkeypatch, answer)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ot.OnlineOpenTargetsClient().targets("MONDO:0014221")
    record = only(run)
    assert (
        record["outcome"] == "failed"
        and record["provider"]["status"] == "not_attempted"
    )
    assert record["network_attempts"] == len(calls)


def test_open_targets_failed_later_page_preserves_only_completed_intake(monkeypatch):
    monkeypatch.setattr(ot, "PAGE_SIZE", 1)
    serve(
        monkeypatch,
        lambda request, n: (
            page(rows=[target_row()], count=2)
            if n == 1
            else {"errors": [{"message": "second page failed"}]}
        ),
    )
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ot.OnlineOpenTargetsClient().targets("MONDO:0014221")
    record = only(run)
    assert record["outcome"] == "partial" and record["terminal_outcome"] == "failed"
    assert record["count"] == 1 and len(record["completed_pages"]) == 1
    assert len(record["pages"]) == 2 and record["provider"]["status"] == "available"


@pytest.mark.parametrize("mode", ["reuse", "replay"])
@pytest.mark.parametrize("source", ["open_targets", "orphadata"])
def test_archive_keeps_original_query_hashes_times_and_versions(
    monkeypatch, tmp_path, mode, source
):
    calls = serve(
        monkeypatch, page("associations") if source == "open_targets" else XML
    )
    getter = ot.get_associations if source == "open_targets" else orpha.get_associations
    identifier = "ENSG00000111669" if source == "open_targets" else "P60174"
    archive = sabueso.RetrievalArchive(tmp_path / "source.db")
    with archive.recording():
        a = getter(identifier)
    _release.forget("Orphanet")
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        b = getter(identifier)
    assert len(calls) == 1
    assert a["record"] == b["record"] and a["retrieved_at"] == b["retrieved_at"]
    old, new = (
        a["acquisition_trace"]["records"][0],
        b["acquisition_trace"]["records"][0],
    )
    assert new["access"] == mode and new["network_attempts"] == 0
    for key in ("source_version", "retrieved_at", "response_identity"):
        assert old[key] == new[key]
    for key in ("retrieval_ref", "retrieved_at", "response_sha256"):
        assert old["requests"][0][key] == new["requests"][0][key]


def test_orphanet_memory_lookup_keeps_original_xml_time_validation_and_scope(
    monkeypatch,
):
    calls = serve(monkeypatch, XML)
    first = orpha.get_associations("P60174")
    with sabueso.attribution() as run:
        second = orpha.OnlineOrphadataClient().genes("ORPHA:868")
    a = first["acquisition_trace"]["records"][0]
    b = only(run)
    assert len(calls) == 1 and b["access"] == "memory" and b["network_attempts"] == 0
    assert (
        first["retrieved_at"]
        == second["retrieved_at"]
        == b["retrieved_at"]
        == a["retrieved_at"]
    )
    assert b["source_version"] == {"value": "2026-06-23", "basis": "xml_header_date"}
    assert (
        b["association_context"]["index_origin"]
        == a["association_context"]["index_origin"]
    )
    assert (
        b["association_context"]["index_origin"]["response_identity"]["hash"]
        == sha256(XML).hexdigest()
    )
    assert b["association_context"]["validation_references"] == ["1234", "5678"]
    assert b["normalized_query"] == {"orpha_code": "868"}
    assert any("Orphadata Science" in item["title"] for item in b["bibliography"])
    assert b["bibliography_gaps"] == [
        "underlying_association_validation_publications_not_fetched"
    ]
    again = orpha.OnlineOrphadataClient().associations("P60174")
    assert {k: first[k] for k in ("record", "retrieved_at", "version")} == again
    portable = ackredit.Attribution.from_dict(b["provider"]["attribution"])
    assert any(
        item.get("version") == "2026-06-23" for item in portable.to_dict()["items"]
    )


@pytest.mark.parametrize("fixture", [False, True])
def test_orphanet_missing_rows_are_scoped_absence_or_fixture_unavailability(
    monkeypatch, tmp_path, fixture
):
    if fixture:
        directory = tmp_path / "orphadata"
        directory.mkdir()
        (directory / "en_product6.xml").write_bytes(XML)
        client = orpha.FixtureOrphadataClient(tmp_path)
    else:
        serve(monkeypatch, XML)
        client = orpha.OnlineOrphadataClient()
    with sabueso.attribution() as run, pytest.raises(RecordNotFoundError):
        client.genes("999")
    record = only(run)
    assert record["outcome"] == ("unavailable" if fixture else "empty")
    assert record["provider"]["status"] == ("not_attempted" if fixture else "available")
    assert record["count"] == 0


@pytest.mark.parametrize("source", ["open_targets", "orphadata"])
@pytest.mark.parametrize("mode", ["missing_fixture", "offline", "bad_document"])
def test_source_unavailability_unasked_and_invalid_answers_remain_distinct(
    monkeypatch, tmp_path, source, mode
):
    module = ot if source == "open_targets" else orpha
    client = (
        (
            ot.FixtureOpenTargetsClient(tmp_path)
            if source == "open_targets"
            else orpha.FixtureOrphadataClient(tmp_path)
        )
        if mode == "missing_fixture"
        else None
    )
    if mode == "bad_document":
        serve(monkeypatch, b"<html>wrong document</html>")
    with (
        _mirror.using(tmp_path, mode="offline") if mode == "offline" else nullcontext(),
        sabueso.attribution() as run,
        pytest.raises(ConnectorError) as caught,
    ):
        module.get_associations(
            "ENSG1" if source == "open_targets" else "P60174", client=client
        )
    record = only(run)
    assert (
        record["outcome"]
        == {
            "missing_fixture": "unavailable",
            "offline": "not_queried",
            "bad_document": "failed",
        }[mode]
    )
    assert record["provider"]["status"] == "not_attempted"
    assert caught.value.acquisition_trace["records"] == [record]
    assert _release.recall("Orphanet", "en_product6") is None


def test_unknown_cached_orphanet_origin_remains_unknown(monkeypatch):
    _release.keep("Orphanet", "en_product6", orpha.parse_release(XML))
    monkeypatch.setattr(
        _http, "_urlopen", lambda *args, **kwargs: pytest.fail("cache downloaded")
    )
    record = orpha.get_associations("P60174")["acquisition_trace"]["records"][0]
    assert record["access"] == "memory" and record["retrieved_at"] is None
    assert record["source_version"]["basis"] == "cached_index_declared_version"
    assert record["association_context"]["index_origin"] is None


def test_provider_failure_preserves_valid_source_results(monkeypatch):
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic provider error")),
    )
    with pytest.warns(Warning):
        result = ot.get_associations(
            "ENSG00000111669", client=ot.FixtureOpenTargetsClient("temp_data")
        )
    assert result["record"]["rows"]
    assert result["acquisition_trace"]["records"][0]["provider"]["status"] == "failed"


@pytest.mark.parametrize("changed", ["count", "version", "entity_disappeared"])
def test_open_targets_cannot_merge_pages_from_different_source_states(
    monkeypatch, changed
):
    monkeypatch.setattr(ot, "PAGE_SIZE", 1)
    answers = [
        page(rows=[target_row("ENSG1")], count=2),
        page(rows=[target_row("ENSG2")], count=2),
    ]
    if changed == "count":
        answers[1]["data"]["disease"]["associatedTargets"]["count"] = 3
    elif changed == "version":
        answers[1]["data"]["meta"]["dataVersion"]["month"] = 10
    else:
        answers[1]["data"]["disease"] = None
    serve(monkeypatch, lambda request, n: answers[n - 1])
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ot.OnlineOpenTargetsClient().targets("MONDO:0014221")
    record = only(run)
    assert record["outcome"] == "partial" and record["terminal_outcome"] == "failed"
    if changed == "version":
        assert record["source_version"]["value"] is None
        assert not record["association_context"]["versions_consistent"]
        assert record["association_context"]["page_versions"] == [
            "2026.9.1",
            "2026.10.1",
        ]


@pytest.mark.parametrize("source", ["open_targets", "orphadata"])
@pytest.mark.parametrize("bad", ["syntax", "shape"])
def test_malformed_local_documents_are_connector_failures(tmp_path, source, bad):
    directory = tmp_path / source
    directory.mkdir()
    if source == "open_targets":
        (directory / "ENSG1.json").write_bytes(
            b"{bad" if bad == "syntax" else b'{"record": {}}'
        )
        client, getter, identifier = (
            ot.FixtureOpenTargetsClient(tmp_path),
            ot.get_associations,
            "ENSG1",
        )
    else:
        (directory / "en_product6.xml").write_bytes(
            b"<bad" if bad == "syntax" else b"<html>synthetic</html>"
        )
        client, getter, identifier = (
            orpha.FixtureOrphadataClient(tmp_path),
            orpha.get_associations,
            "P60174",
        )
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        getter(identifier, client=client)
    record = only(run)
    assert (
        record["outcome"] == "failed"
        and record["provider"]["status"] == "not_attempted"
    )


@pytest.fixture(scope="module")
def disease_decks():
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.chembl import FixtureChEMBLClient
    from sabueso.tools.db.mondo import FixtureMONDOClient
    from sabueso.tools.db.pdb_ccd import FixtureCCDClient
    from sabueso.tools.db.unichem import FixtureUniChemClient

    mondo = FixtureMONDOClient("temp_data")
    disease, _ = sabueso.resolve("ORPHA:868", mondo_client=mondo)
    before = disease.to_dict()
    with pytest.warns(Warning):
        targets = sabueso.disease_targets(
            disease,
            limit=3,
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            open_targets_client=ot.FixtureOpenTargetsClient("temp_data"),
            orphadata_client=orpha.FixtureOrphadataClient("temp_data"),
        )
    drugs = sabueso.disease_drugs(
        "mesh:D014355",
        limit=3,
        mondo_client=mondo,
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
    )
    assert disease.to_dict() == before
    return targets, drugs


@pytest.mark.parametrize("kind", [0, 1])
def test_disease_build_trace_pins_exact_input_support_result_and_native_access(
    disease_decks, kind
):
    deck = disease_decks[kind]
    trace = deck.acquisition_trace
    assert trace["deck_snapshot_id"] == deck.snapshot_id()
    assert trace["input_card_refs"] == [deck.meta["support"]["input"]["card_ref"]]
    assert trace["card_refs"] == [card.pinned_ref() for card in deck.cards]
    assert trace["operation"]["rule"] == deck.meta["rule"]
    assert (
        trace["operation"]["support_card_ref"]
        == deck.meta["support"]["assertions"]["card_ref"]
    )
    assert trace["operation"]["sources"] == deck.meta["sources"]
    assert trace["operation"]["built_count"] == len(deck.cards)
    assert trace["operation"]["excluded_count"] == len(deck.meta["excluded"])
    sources = {r["source"] for r in trace["records"]}
    assert (
        {"Open Targets", "Orphanet", "UniProt"} <= sources
        if kind == 0
        else {"MONDO", "ChEMBL", "UniChem"} <= sources
    )
    if kind == 0:
        assert "MONDO" not in sources  # Existing input identity is not fresh access.
    trace["records"].clear()
    assert deck.acquisition_trace["records"]  # Detached mutation.


@pytest.mark.parametrize("kind", [0, 1])
def test_saved_deck_read_and_portable_receipts_add_no_runtime_credit(
    tmp_path, disease_decks, kind
):
    deck = disease_decks[kind]
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    ref = store.save_deck(deck, f"disease_{kind}")
    original = deepcopy((deck.to_list(), deck.meta, deck.snapshot_id()))
    portable = json.loads(json.dumps(deck.acquisition_trace))
    before = ackredit.get_attribution().to_dict()
    with sabueso.attribution() as run:
        loaded = store.load_deck(ref)
        loaded.explain(loaded.cards[0].id)
        loaded.terms("redistribution")
        for record in portable["records"]:
            if record["provider"].get("attribution"):
                ackredit.Attribution.from_dict(
                    record["provider"]["attribution"]
                ).report(format="bibtex")
    assert (loaded.to_list(), loaded.meta, loaded.snapshot_id()) == original
    assert loaded.acquisition_trace is None
    assert not run.acquisitions and ackredit.get_attribution().to_dict() == before


def test_custom_disease_sources_produce_no_invented_source_access():
    from sabueso.tools.db.mondo import FixtureMONDOClient

    disease, _ = sabueso.resolve(
        "ORPHA:868", mondo_client=FixtureMONDOClient("temp_data")
    )

    class EmptyTargets:
        def targets(self, disease, limit=ot.DEFAULT_LIMIT):
            return {
                "version": "supplied",
                "retrieved_at": "supplied",
                "record": {
                    "disease": {"id": disease, "name": "x"},
                    "count": 0,
                    "rows": [],
                },
            }

    class EmptyGenes:
        def genes(self, code):
            return {"version": "supplied", "retrieved_at": "supplied", "record": []}

    deck = sabueso.disease_targets(
        disease, open_targets_client=EmptyTargets(), orphadata_client=EmptyGenes()
    )
    assert deck.acquisition_trace["records"] == []
    assert deck.acquisition_trace["input_card_refs"] == [disease.pinned_ref()]
    assert deck.acquisition_trace["operation"]["built_count"] == 0


def test_failed_disease_resolution_retains_exception_trace():
    from sabueso.core.errors import ResolverError
    from sabueso.tools.db.mondo import FixtureMONDOClient

    with pytest.raises(ResolverError) as caught:
        sabueso.disease_targets(
            "EFO:0001360", mondo_client=FixtureMONDOClient("temp_data")
        )
    trace = caught.value.acquisition_trace
    assert trace["result_status"] == "failed"
    assert trace["records"][0]["source"] == "MONDO"
    assert trace["records"][0]["outcome"] == "empty"


@pytest.mark.parametrize("source", ["open_targets", "orphadata"])
@pytest.mark.parametrize("failure", [404, 500, "timeout"])
def test_failed_transport_preserves_actual_attempts_and_no_completed_credit(
    monkeypatch, source, failure
):
    calls = serve(
        monkeypatch,
        URLError(TimeoutError("synthetic"))
        if failure == "timeout"
        else HTTPError(
            "https://synthetic.invalid", failure, "synthetic", Message(), None
        ),
    )
    getter = ot.get_associations if source == "open_targets" else orpha.get_associations
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        getter("ENSG1" if source == "open_targets" else "P60174")
    record = only(run)
    assert (
        record["outcome"] == "failed"
        and record["provider"]["status"] == "not_attempted"
    )
    assert record["network_attempts"] == len(calls) == (3 if failure == 500 else 1)


class WithoutGeneIds(FixtureUniProtClient):
    def __init__(self, keep_protein_ids=False):
        super().__init__("temp_data")
        self.keep_protein_ids = keep_protein_ids

    def fetch_entry(self, accession):
        entry, when = super().fetch_entry(accession)
        if self.keep_protein_ids:
            for xref in entry.get("uniProtKBCrossReferences", []):
                if xref.get("database") == "Ensembl":
                    xref["properties"] = [
                        p for p in xref.get("properties", []) if p["key"] != "GeneId"
                    ]
        else:
            entry["uniProtKBCrossReferences"] = [
                x
                for x in entry.get("uniProtKBCrossReferences", [])
                if x.get("database") != "Ensembl"
            ]
        return entry, when


def open_targets_state(card):
    return next(r for r in card.knowledge_state()["rows"] if r["source"] == ot.SOURCE)


def open_targets_record(card):
    return next(r for r in card.quality["enrichments"] if r["source"] == ot.SOURCE)


@pytest.mark.parametrize("keep_protein_ids", [False, True])
@pytest.mark.parametrize("supplied_client", [False, True])
def test_open_targets_missing_gene_is_unqueried_without_operation_or_credit(
    monkeypatch, keep_protein_ids, supplied_client
):
    def forbidden(*args, **kwargs):
        pytest.fail("A missing upstream gene must not construct or call Open Targets")

    class Client:
        associations = forbidden

    monkeypatch.setattr(ot, "OnlineOpenTargetsClient", forbidden)
    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(WithoutGeneIds(keep_protein_ids)),
        open_targets={"limit": 2},
        open_targets_client=Client() if supplied_client else None,
    )
    record = open_targets_record(card)
    assert record["status"] == "not_queried"
    assert record["request_options"] == {"limit": 2}
    assert "no Ensembl gene" in record["detail"]
    row = open_targets_state(card)
    assert row["state"] == "not_queried" and row["count"] is None
    assert row["basis"] == {"detail": record["detail"]}
    assert not card.relationships("associated_with")
    assert not any(r["source"] == ot.SOURCE for r in card.acquisition_trace["records"])
    assert "doi:10.1093/nar/gkae1128" not in {
        item["id"] for item in ackredit.get_attribution().to_dict()["items"]
    }
    assert card.source_assertion_store.to_list()


def test_open_targets_queried_target_omitting_protein_retains_native_access(
    monkeypatch,
):
    payload = page("associations")
    payload["data"]["target"]["proteinIds"] = [{"id": "Q00000", "source": "uniprot"}]
    calls = serve(monkeypatch, payload)
    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        open_targets={},
        open_targets_client=ot.OnlineOpenTargetsClient(),
    )
    assert len(calls) == 1
    assert open_targets_record(card)["status"] == "not_found"
    assert "does not list P60174" in open_targets_record(card)["detail"]
    assert open_targets_state(card)["state"] == "not_stated"
    assert not card.relationships("associated_with")
    (record,) = [
        r for r in card.acquisition_trace["records"] if r["source"] == ot.SOURCE
    ]
    assert record["outcome"] == "empty" and record["completed_pages"]
    assert "doi:10.1093/nar/gkae1128" in {
        item["id"] for item in ackredit.get_attribution().to_dict()["items"]
    }


def test_open_targets_valid_gene_retains_exact_unobserved_science_and_pin():
    class Unobserved(ot.FixtureOpenTargetsClient):
        associations = ot.FixtureOpenTargetsClient.associations.__wrapped__

    def build(client):
        return sabueso.resolve(
            "P60174",
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            open_targets={"limit": 2},
            open_targets_client=client,
        )[0]

    with pytest.warns(Warning):
        current = build(
            ot.FixtureOpenTargetsClient("temp_data", retrieved_at="original")
        )
    with pytest.warns(Warning):
        unobserved = build(Unobserved("temp_data", retrieved_at="original"))
    assert current.to_dict() == unobserved.to_dict()
    assert current.pinned_ref() == unobserved.pinned_ref()
    assert current.relationships("associated_with")
    assert any(r["source"] == ot.SOURCE for r in current.acquisition_trace["records"])
    assert not any(
        r["source"] == ot.SOURCE for r in unobserved.acquisition_trace["records"]
    )


def test_open_targets_refresh_preserves_historical_unasked_pin(monkeypatch, tmp_path):
    from sabueso.core import attribution, source_acquisition
    from sabueso.enrichers import NothingToAsk
    from sabueso.enrichers.open_targets import OpenTargets

    def legacy_missing_gene(*args, **kwargs):
        raise NothingToAsk("the entry cross-references no Ensembl gene")

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Neither prerequisite gates nor saved reads may access Open Targets"
        )

    monkeypatch.setattr(ot, "OnlineOpenTargetsClient", forbidden)
    resolver = EntityResolver(WithoutGeneIds())
    with monkeypatch.context() as old:
        old.setattr(OpenTargets, "requests", legacy_missing_gene)
        historical, _ = sabueso.resolve(
            "P60174", resolver=resolver, open_targets={"limit": 2}
        )
    before = deepcopy(historical.to_dict())
    store = sabueso.KnowledgeStore(tmp_path / "cards.db")
    original_pin = store.save(historical)
    assert open_targets_state(historical)["state"] == "not_stated"
    refreshed, _ = sabueso.refresh_card(historical, store=store, resolver=resolver)
    assert open_targets_state(refreshed)["state"] == "not_queried"
    assert open_targets_state(refreshed)["count"] is None
    assert open_targets_record(refreshed)["request_options"] == {"limit": 2}
    assert (
        refreshed.source_assertion_store.to_list()
        == historical.source_assertion_store.to_list()
    )
    assert historical.to_dict() == before
    assert original_pin != refreshed.pinned_ref()
    monkeypatch.setattr(sabueso, "resolve", forbidden)
    monkeypatch.setattr(attribution, "_credit", forbidden)
    monkeypatch.setattr(source_acquisition, "_credit", forbidden)
    with sabueso.attribution() as run:
        credit_before = ackredit.get_attribution().to_dict()
        loaded = store.load(original_pin)
        assert loaded.to_dict() == before and loaded.pinned_ref() == original_pin
        assert store.load(refreshed.pinned_ref()).to_dict() == refreshed.to_dict()
        assert ackredit.get_attribution().to_dict() == credit_before
        assert not run.acquisitions and not run.records
