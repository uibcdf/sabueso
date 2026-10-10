"""Variant/tissue acquisition scope survives failure, reuse and inert reading."""

import io
import json
import os
import subprocess
import sys
from datetime import timedelta
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import ackredit
import pytest

import sabueso
from sabueso.core.errors import ConnectorError, NotArchivedError, RecordNotFoundError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, gnomad

GENE = "ENSG00000111669"
TRANSCRIPT = "ENST00000396705"


@pytest.fixture(autouse=True)
def independent():
    with ackredit.session("public gnomAD observation"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()
        self.headers["X-UniProt-Release"] = "unrelated"


def serve(monkeypatch, answers):
    calls = []
    iterator = iter(answers)

    def respond(request, timeout):
        calls.append(json.loads(request.data))
        answer = next(iterator)
        if isinstance(answer, Exception):
            raise answer
        return Response(answer)

    monkeypatch.setattr(_http, "_urlopen", respond)
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)
    return calls


def gene_payload(kind="gene", rows=None):
    entity = {"gene_id": GENE, "variants": [] if rows is None else rows}
    if kind == "transcript":
        entity.update(transcript_id=TRANSCRIPT, transcript_version="10")
    return {"data": {kind: entity}}


def pext_payload():
    return {
        "data": {
            "gene": {
                "gene_id": GENE,
                "chrom": "12",
                "strand": "+",
                "pext": {
                    "regions": [
                        {
                            "start": 1,
                            "stop": 3,
                            "tissues": [{"tissue": "testis", "value": 0.5}],
                        }
                    ]
                },
            }
        }
    }


def build(client, accession="P60174", **options):
    return sabueso.resolve(
        accession,
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        gnomad_client=client,
        **options,
    )[0]


def own(card):
    return [r for r in card.acquisition_trace["records"] if r["source"] == "gnomAD"]


@pytest.mark.parametrize(
    "getter,kind,identifier,payload,label",
    [
        (
            gnomad.get_variants,
            "gene",
            GENE,
            gene_payload(rows=[{"variant_id": "v1"}]),
            gnomad.DATASET,
        ),
        (
            gnomad.get_transcript_variants,
            "transcript",
            TRANSCRIPT,
            gene_payload("transcript", [{"variant_id": "v1"}]),
            gnomad.DATASET,
        ),
        (gnomad.get_pext, "pext", GENE, pext_payload(), gnomad.PEXT_VERSION),
    ],
)
def test_public_getters_keep_native_scope_separate_from_client_version(
    monkeypatch, getter, kind, identifier, payload, label
):
    calls = serve(monkeypatch, [payload])
    with ackredit.capture("host") as host:
        result = getter(identifier)
    (record,) = result["acquisition_trace"]["records"]
    assert result["version"] == label
    assert (
        record["source"] == "gnomAD"
        and record["outcome"] == "received"
        and record["count"] == 1
    )
    assert record["source_version"] == {"value": None, "basis": "not_stated"}
    context = record["variation_context"]
    assert context["rule"] == "gnomad_operation_observation@1"
    assert context["requested_reference_genome"] == "GRCh38"
    assert context["client_version_label"] == label
    assert context["requested_dataset"] == (None if kind == "pext" else gnomad.DATASET)
    assert record["pages"][0]["query"] == calls[0]
    if kind == "transcript":
        assert record["pages"][0]["native_entity"]["transcript_version"] == "10"
    if kind == "pext":
        assert context["native_GTEx_revision"]["value"] is None
    assert record["bibliography"][-1]["url"] == gnomad.API
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    assert "gnomAD GraphQL API" in portable.report(format="bibtex")
    assert "gnomad_operation_observation@1" in json.dumps(portable.to_dict())
    assert {i["id"] for i in portable.to_dict()["items"]} <= {
        i["id"] for i in host.attribution.to_dict()["items"]
    }


def test_consequence_batches_preserve_alias_absence_and_empty_list_distinction(
    monkeypatch,
):
    monkeypatch.setattr(gnomad, "CONSEQUENCES_PER_REQUEST", 2)
    calls = serve(
        monkeypatch,
        [
            {
                "data": {
                    "v0": {"variant_id": "A", "transcript_consequences": []},
                    "v1": None,
                }
            },
            {
                "data": {
                    "v0": {
                        "variant_id": "C",
                        "transcript_consequences": [
                            {"transcript_id": "T1", "transcript_version": "7"}
                        ],
                    }
                }
            },
        ],
    )
    with sabueso.attribution() as run:
        result = gnomad.OnlineGnomADClient().consequences(
            v for v in ["C", "A", "B", "A", ""]
        )
    assert result["record"] == {
        "A": [],
        "C": [{"transcript_id": "T1", "transcript_version": "7"}],
    }
    (record,) = run.acquisitions
    assert len(calls) == 2 and record["count"] == 2
    context = record["variation_context"]
    assert context["requested_variant_ids"] == ["A", "B", "C"]
    assert (
        context["absent_variant_ids"] == ["B"]
        and context["transcript_consequence_count"] == 1
    )
    assert context["requested_reference_genome"] is None
    assert record["pages"][0]["received_variant_ids"] == ["A"]
    assert record["pages"][0]["absent_variant_ids"] == ["B"]
    assert record["pages"][1]["query"]["variant_ids"] == ["C"]
    assert record["pages"][1]["native_variant_ids"] == {"C": "C"}
    assert record["pages"][1]["native_transcript_bindings"] == {
        "C": [{"transcript_id": "T1", "transcript_version": "7"}]
    }
    assert "not_transcript_consequence_rows" in record["count_basis"]


def test_empty_online_consequence_request_does_not_access_or_credit(monkeypatch):
    calls = serve(monkeypatch, [])
    with sabueso.attribution() as run:
        assert gnomad.OnlineGnomADClient().consequences(iter([]))["record"] == {}
    (record,) = run.acquisitions
    assert not calls and record["outcome"] == "not_queried" and record["count"] is None
    assert (
        not record["completed_pages"]
        and record["provider"]["status"] == "not_attempted"
    )


@pytest.mark.parametrize(
    "method,argument,payload,basis",
    [
        ("variants", GENE, {"data": {"gene": None}}, "explicit_null_GraphQL_entity"),
        (
            "variants",
            GENE,
            {"errors": [{"message": "Gene not found"}], "data": None},
            "explicit_GraphQL_not_found_error; existing_client_message_policy",
        ),
        ("pext", GENE, {"data": {"gene": {"pext": None}}}, "explicit_null_pext"),
        (
            "pext",
            GENE,
            {"data": {"gene": {"pext": {"regions": []}}}},
            "explicit_empty_pext_regions",
        ),
    ],
)
def test_explicit_native_absence_retains_received_receipt_and_scope(
    monkeypatch, method, argument, payload, basis
):
    serve(monkeypatch, [payload])
    with sabueso.attribution() as run, pytest.raises(RecordNotFoundError):
        getattr(gnomad.OnlineGnomADClient(), method)(argument)
    (record,) = run.acquisitions
    assert record["outcome"] == "empty" and record["count"] == 0
    assert record["pages"][0]["absence_basis"] == basis
    assert record["provider"]["status"] == "available"
    assert record["variation_context"]["completeness"] == "not_established"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "data": {"gene": {"variants": []}},
            "errors": [{"message": "upstream failure"}],
        },
        {
            "errors": [{"message": "not found"}, {"message": "upstream failure"}],
            "data": None,
        },
        {"data": {}},
        {"data": {"gene": {"variants": None}}},
    ],
)
def test_failed_graphql_response_never_becomes_absence_or_completed_credit(
    monkeypatch, payload
):
    serve(monkeypatch, [payload])
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        gnomad.OnlineGnomADClient().variants(GENE)
    (record,) = run.acquisitions
    assert record["outcome"] == "failed" and record["count"] is None
    assert record["pages"][0]["outcome"] == "failed" and not record["completed_pages"]
    assert record["provider"]["status"] == "not_attempted"
    assert record["requests"][0]["response_sha256"]


@pytest.mark.parametrize("first_empty", [True, False])
@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("test"),
        {"data": {}},
        {"data": {"v0": None}, "errors": [{"message": "partial failure"}]},
    ],
)
def test_later_batch_failure_preserves_completed_subset_without_scientific_return(
    monkeypatch, first_empty, failure
):
    monkeypatch.setattr(gnomad, "CONSEQUENCES_PER_REQUEST", 1)
    first = {"data": {"v0": None if first_empty else {"transcript_consequences": []}}}
    serve(monkeypatch, [first, failure])
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        gnomad.OnlineGnomADClient().consequences(["A", "B"])
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["count"] == (
        0 if first_empty else 1
    )
    assert record["terminal_outcome"] == "failed" and record["incomplete"]
    assert (
        len(record["completed_pages"]) == 1
        and record["provider"]["status"] == "available"
    )
    assert record["variation_context"]["returned_items"] is None
    assert record["variation_context"]["completeness"] == "not_established"


@pytest.mark.parametrize(
    "method,argument,name",
    [
        ("variants", GENE, GENE),
        ("transcript_variants", TRANSCRIPT, TRANSCRIPT),
        ("pext", GENE, "pext_" + GENE),
        ("consequences", ["A"], "consequences"),
    ],
)
@pytest.mark.parametrize("failure", ["missing", "malformed", "unreadable"])
def test_local_files_are_unavailable_or_failed_never_source_absence(
    tmp_path, monkeypatch, method, argument, name, failure
):
    directory = tmp_path / "gnomad"
    directory.mkdir()
    path = directory / (name + ".json")
    if failure != "missing":
        path.write_text("null" if failure == "malformed" else "{}")
    if failure == "unreadable":
        original = Path.read_text

        def broken(self, *args, **kwargs):
            if self == path:
                raise OSError("test unreadable")
            return original(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", broken)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        getattr(gnomad.FixtureGnomADClient(tmp_path), method)(argument)
    (record,) = run.acquisitions
    assert record["outcome"] == ("unavailable" if failure == "missing" else "failed")
    assert record["count"] is None and record["network_attempts"] == 0
    assert record["provider"]["status"] == "not_attempted"


def test_fixture_subset_and_declared_version_do_not_establish_native_release(tmp_path):
    directory = tmp_path / "gnomad"
    directory.mkdir()
    (directory / (GENE + ".json")).write_text(
        json.dumps({"version": "fixture label", "record": {"gene": {}, "variants": []}})
    )
    (directory / "consequences.json").write_text(
        json.dumps({"A": [], "B": [{"transcript_id": "T"}]})
    )
    with sabueso.attribution() as run:
        assert (
            gnomad.FixtureGnomADClient(tmp_path).variants(GENE)["version"]
            == "fixture label"
        )
        assert gnomad.FixtureGnomADClient(tmp_path).consequences(iter(["A"]))[
            "record"
        ] == {"A": []}
    gene, consequences = run.acquisitions
    assert gene["source_version"]["value"] is None
    assert gene["pages"][0]["fixture_version_label"] == "fixture label"
    assert (
        consequences["count"] == 1
        and consequences["variation_context"]["received_items"] == 2
    )
    assert consequences["variation_context"]["returned_items"] == 1
    assert all(
        r["variation_context"]["scope"] == "fixture_subset" for r in run.acquisitions
    )


def test_transport_retries_are_not_duplicate_completed_graphql_batches(monkeypatch):
    calls = serve(
        monkeypatch,
        [
            HTTPError(gnomad.API, 429, "rate limit", {}, None),
            HTTPError(gnomad.API, 429, "rate limit", {}, None),
            gene_payload(),
        ],
    )
    with sabueso.attribution() as run:
        assert gnomad.OnlineGnomADClient().variants(GENE)["record"]["variants"] == []
    (record,) = run.acquisitions
    assert len(calls) == record["network_attempts"] == 3
    assert len(record["requests"]) == len(record["completed_pages"]) == 1
    assert record["outcome"] == "empty" and record["count"] == 0


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archive_reuses_original_post_body_hashes_times_and_credit(
    monkeypatch, tmp_path, mode
):
    calls = serve(monkeypatch, [pext_payload()])
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with archive.recording(), sabueso.attribution() as first:
        original = gnomad.OnlineGnomADClient().pext(GENE)
    context = (
        archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying()
    )
    with context, sabueso.attribution() as second:
        restored = gnomad.OnlineGnomADClient().pext(GENE)
    (before,), (after,) = first.acquisitions, second.acquisitions
    assert original == restored and len(calls) == 1
    assert after["network_attempts"] == 0 and after["access"] == mode
    assert (
        before["pages"] == after["pages"]
        and before["retrieved_at"] == after["retrieved_at"]
    )
    for field in ("request_sha256", "response_sha256", "retrieval_ref", "retrieved_at"):
        assert before["requests"][0][field] == after["requests"][0][field]
    portable = ackredit.Attribution.from_dict(after["provider"]["attribution"])
    assert "gnomAD GraphQL API" in portable.report(format="bibtex")


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archived_failed_alias_batch_remains_partial_not_complete_absence(
    monkeypatch, tmp_path, mode
):
    monkeypatch.setattr(gnomad, "CONSEQUENCES_PER_REQUEST", 1)
    calls = serve(monkeypatch, [{"data": {"v0": None}}, {"data": {}}])
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with (
        archive.recording(),
        sabueso.attribution() as first,
        pytest.raises(ConnectorError),
    ):
        gnomad.OnlineGnomADClient().consequences(["A", "B"])
    context = (
        archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying()
    )
    with context, sabueso.attribution() as second, pytest.raises(ConnectorError):
        gnomad.OnlineGnomADClient().consequences(["A", "B"])
    (before,), (after,) = first.acquisitions, second.acquisitions
    assert (
        len(calls) == 2 and after["network_attempts"] == 0 and after["access"] == mode
    )
    assert (
        before["pages"] == after["pages"]
        and after["outcome"] == "partial"
        and after["count"] == 0
    )
    assert after["variation_context"]["returned_items"] is None


def test_unarchived_public_getter_is_not_queried(tmp_path):
    with (
        sabueso.RetrievalArchive(tmp_path / "archive.db").replaying(),
        pytest.raises(NotArchivedError) as caught,
    ):
        gnomad.get_variants(GENE)
    (record,) = caught.value.acquisition_trace["records"]
    assert record["outcome"] == "not_queried" and record["count"] is None
    assert record["provider"]["status"] == "not_attempted"


def test_received_variants_precede_protein_placement_and_card_limit():
    from sabueso._private.smonitor.warnings import EnrichmentTruncatedWarning

    with pytest.warns(EnrichmentTruncatedWarning):
        card = build(gnomad.FixtureGnomADClient("temp_data"), gnomad={"limit": 1})
    (gene, transcript, consequences) = own(card)
    assert (
        gene["count"] == 18 and transcript["count"] == 9 and consequences["count"] == 6
    )
    (quality,) = [r for r in card.quality["enrichments"] if r["source"] == "gnomAD"]
    assert (
        quality["count"] == 1 and quality["total_count"] == 15 and quality["truncated"]
    )
    assert len(card.get("annotations.population_variants")["value"]) == 1
    assert "not_card_selected" in gene["count_basis"]


def test_observation_preserves_exact_scientific_card_assertions_and_pin():
    class Unobserved(gnomad.FixtureGnomADClient):
        variants = gnomad.FixtureGnomADClient.variants.__wrapped__
        transcript_variants = gnomad.FixtureGnomADClient.transcript_variants.__wrapped__
        consequences = gnomad.FixtureGnomADClient.consequences.__wrapped__
        pext = gnomad.FixtureGnomADClient.pext.__wrapped__

    card = build(
        gnomad.FixtureGnomADClient("temp_data", retrieved_at="original"),
        gnomad={},
        exon_usage=True,
    )
    custom = build(
        Unobserved("temp_data", retrieved_at="original"), gnomad={}, exon_usage=True
    )
    assert (
        card.to_dict() == custom.to_dict() and card.pinned_ref() == custom.pinned_ref()
    )
    assert {r["operation"] for r in own(card)} == {
        "gnomad_variants",
        "gnomad_transcript_variants",
        "gnomad_consequences",
        "gnomad_pext",
    }
    assert not own(custom)


def test_missing_consequence_archive_installs_no_partial_variant_assertions(tmp_path):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    directory = tmp_path / "gnomad"
    directory.mkdir()
    for name in (GENE + ".json", TRANSCRIPT + ".json"):
        (directory / name).write_bytes((Path("temp_data/gnomad") / name).read_bytes())
    with pytest.warns(EnrichmentFailedWarning):
        card = build(gnomad.FixtureGnomADClient(tmp_path), gnomad={})
    assert [r["outcome"] for r in own(card)] == ["received", "received", "unavailable"]
    assert card.get("annotations.population_variants") is None
    rows = [
        r
        for r in card.knowledge_state()["rows"]
        if r["area"] == "annotations.population_variants"
    ]
    assert rows and all(
        r["state"] == "unavailable" and r["count"] is None for r in rows
    )


@pytest.mark.parametrize(
    "accession,options",
    [("P52270", {"gnomad": {}, "exon_usage": True}), ("P60174", {})],
)
def test_unasked_gnomad_routes_receive_no_native_resource_credit(accession, options):
    card = build(
        gnomad.FixtureGnomADClient("temp_data"), accession=accession, **options
    )
    assert not own(card)
    assert "url:" + gnomad.API not in {
        i["id"] for i in ackredit.get_attribution().to_dict()["items"]
    }


def test_independent_saved_reader_preserves_pin_and_credit_without_new_operations(
    tmp_path,
):
    card = build(
        gnomad.FixtureGnomADClient("temp_data", retrieved_at="original"),
        gnomad={},
        exon_usage=True,
    )
    pin = sabueso.KnowledgeStore(tmp_path / "knowledge.db").save(card)
    saved = {"pin": pin, "card": card.to_dict(), "trace": card.acquisition_trace}
    sidecar = tmp_path / "original.json"
    sidecar.write_text(json.dumps(saved))
    command = """
import json,sys
from pathlib import Path
import ackredit,sabueso
from sabueso.core import attribution,source_acquisition
from sabueso.core.card import Card
from sabueso.tools.db import _http,gnomad
def forbidden(*args,**kwargs):raise RuntimeError('Saved reader must not acquire, derive or credit')
sabueso.resolve=sabueso.refresh_card=_http._urlopen=forbidden
attribution._credit=source_acquisition._credit=forbidden
for cls in (gnomad.FixtureGnomADClient,gnomad.OnlineGnomADClient):
 cls.variants=cls.transcript_variants=cls.consequences=cls.pext=forbidden
Card.variant_tissue_usage=Card.isoform_tissue_usage=Card.knowledge_state=forbidden
sabueso.__version__='999.reader'
path=Path(sys.argv[1]);saved=json.loads(path.read_text())
with ackredit.session('independent reader'),sabueso.attribution() as run:
 before=ackredit.get_attribution().to_dict()
 card=sabueso.KnowledgeStore(path.parent/'knowledge.db').load(saved['pin'])
 assert card.to_dict()==saved['card'] and card.pinned_ref()==saved['pin']
 records=[r for r in saved['trace']['records'] if r['source']=='gnomAD']
 assert len(records)==4 and card.acquisition_trace is None
 for r in records:
  assert r['producer']['version']!='999.reader'
  portable=ackredit.Attribution.from_dict(r['provider']['attribution'])
  assert 'gnomad_operation_observation@1' in json.dumps(portable.to_dict())
  assert 'gnomAD GraphQL API' in portable.report(format='bibtex')
 assert ackredit.get_attribution().to_dict()==before and not run.acquisitions and not run.records
"""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", command, str(sidecar)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(sidecar.read_text()) == saved


@pytest.mark.parametrize(
    "method,argument,name,saved",
    [
        ("variants", GENE, GENE, {"record": {"gene": {}, "variants": [None]}}),
        ("variants", GENE, GENE, {"record": {"gene": [], "variants": []}}),
        (
            "transcript_variants",
            TRANSCRIPT,
            TRANSCRIPT,
            {"record": {"transcript": {}, "variants": None}},
        ),
        (
            "pext",
            GENE,
            "pext_" + GENE,
            {"record": {"gene": {}, "pext": {"regions": [None]}}},
        ),
        ("pext", GENE, "pext_" + GENE, {"record": {"gene": {}, "pext": None}}),
        ("consequences", ["A"], "consequences", {"A": [None]}),
    ],
)
def test_malformed_local_consumed_containers_fail_before_mapping(
    tmp_path, method, argument, name, saved
):
    directory = tmp_path / "gnomad"
    directory.mkdir()
    (directory / (name + ".json")).write_text(json.dumps(saved))
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        getattr(gnomad.FixtureGnomADClient(tmp_path), method)(argument)
    (record,) = run.acquisitions
    assert record["outcome"] == "failed" and record["count"] is None
    assert record["pages"][0]["outcome"] == "failed" and not record["completed_pages"]


@pytest.mark.parametrize(
    "options",
    [{"gnomad": {}}, {"exon_usage": True}, {"gnomad": {}, "exon_usage": True}],
)
def test_no_gene_identity_prerequisite_creates_no_gnomad_operation(
    monkeypatch, options
):
    class WithoutGenes(FixtureUniProtClient):
        def fetch_entry(self, accession):
            entry, when = super().fetch_entry(accession)
            entry["uniProtKBCrossReferences"] = [
                x
                for x in entry.get("uniProtKBCrossReferences", [])
                if x.get("database") != "Ensembl"
            ]
            return entry, when

    def forbidden(*args, **kwargs):
        raise AssertionError("An unqueried gnomAD client must not be constructed")

    monkeypatch.setattr(gnomad, "OnlineGnomADClient", forbidden)
    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(WithoutGenes("temp_data")),
        **options,
    )
    assert not own(card)
    states = [r for r in card.knowledge_state()["rows"] if r["source"] == "gnomAD"]
    assert states and all(r["state"] == "not_queried" for r in states)
    assert all(r["count"] is None for r in states)
    records = [r for r in card.quality["enrichments"] if r["source"] == "gnomAD"]
    requested = [r for r in records if "detail" in r]
    assert requested and all(
        r["status"] == "not_queried" and "no Ensembl gene" in r["detail"]
        for r in requested
    )
    assert "url:" + gnomad.API not in {
        i["id"] for i in ackredit.get_attribution().to_dict()["items"]
    }


def test_empty_local_consequence_subset_does_not_establish_native_absence(tmp_path):
    directory = tmp_path / "gnomad"
    directory.mkdir()
    (directory / "consequences.json").write_text("{}")
    with sabueso.attribution() as run:
        assert gnomad.FixtureGnomADClient(tmp_path).consequences(["A"])["record"] == {}
    (record,) = run.acquisitions
    assert record["outcome"] == "empty" and record["count"] == 0
    assert record["variation_context"]["scope"] == "fixture_subset"
    assert record["variation_context"]["completeness"] == "not_established"
