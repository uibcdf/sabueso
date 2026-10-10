"""Source-local prerequisites are unasked; actual answers and old pins stay distinct."""

import json
from copy import deepcopy

import ackredit
import pytest

import sabueso
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.knowledge_state import _enrichment_row
from sabueso.core.snapshot import canonical_json
from sabueso.enrichers import (
    ENRICHERS,
    Context,
    NothingToAsk,
    RequestPrerequisiteMissing,
    run,
)
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http

SOURCES = [
    e
    for e in ENRICHERS
    if e.option
    in {"diseases", "clinvar", "skempi", "sabdab", "medgen", "disease_identity"}
]


def forbidden(*args, **kwargs):
    pytest.fail("Unasked sources and saved readers must not acquire or credit data")


class ForbiddenClient:
    def __getattr__(self, name):
        return forbidden


class MissingInputs(FixtureUniProtClient):
    """Public entry with synthetic missing inputs; the frozen file stays untouched."""

    def __init__(self, keep_other_ensembl=False):
        super().__init__("temp_data")
        self.keep_other_ensembl = keep_other_ensembl

    def fetch_entry(self, accession):
        entry, when = super().fetch_entry(accession)
        entry["comments"] = [
            c for c in entry.get("comments", []) if c.get("commentType") != "DISEASE"
        ]
        entry["uniProtKBCrossReferences"] = [
            x
            for x in entry.get("uniProtKBCrossReferences", [])
            if x.get("database") not in {"GeneID", "PDB"}
            and (self.keep_other_ensembl or x.get("database") != "Ensembl")
        ]
        if self.keep_other_ensembl:
            for x in entry["uniProtKBCrossReferences"]:
                if x.get("database") == "Ensembl":
                    x["properties"] = [
                        p for p in x.get("properties", []) if p["key"] != "ProteinId"
                    ]
        return entry, when


@pytest.fixture(autouse=True)
def offline_session(monkeypatch):
    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with ackredit.session("public source prerequisite regressions"):
        yield


def options(enricher):
    if enricher.option == "diseases":
        return {"channels": ["knowledge"]}
    if enricher.option == "clinvar":
        return {"limit": 2}
    return True


def quality(card, enricher):
    return next(
        e for e in card.quality["enrichments"] if e["source"] == enricher.source
    )


def states(card, enricher):
    return [r for r in card.knowledge_state()["rows"] if r["source"] == enricher.source]


@pytest.mark.parametrize("enricher", SOURCES, ids=lambda e: e.option)
@pytest.mark.parametrize("supplied", [False, True])
def test_missing_input_card_never_constructs_calls_or_credits_source(
    monkeypatch, enricher, supplied
):
    monkeypatch.setattr(type(enricher), "client", forbidden)
    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(MissingInputs()),
        **{
            enricher.option: options(enricher),
            enricher.client_argument: ForbiddenClient() if supplied else None,
        },
    )
    record = quality(card, enricher)
    assert record["status"] == "not_queried" and record["detail"]
    assert record["request_options"] == options(enricher)
    assert len(states(card, enricher)) == len(enricher.areas)
    for row in states(card, enricher):
        assert (row["state"], row["count"]) == ("not_queried", None)
        assert row["basis"] == {"detail": record["detail"]}
    assert not any(
        r["source"] == enricher.source for r in card.acquisition_trace["records"]
    )
    # Only the public primary source ran: no dependent-source resource use exists.
    assert {r["source"] for r in card.acquisition_trace["records"]} == {"UniProt"}
    assert card.source_assertion_store.to_list()


def test_diseases_gene_and_transcript_are_not_a_protein_prerequisite(monkeypatch):
    enricher = next(e for e in SOURCES if e.option == "diseases")
    monkeypatch.setattr(type(enricher), "client", forbidden)
    client = MissingInputs(keep_other_ensembl=True)
    entry, _ = client.fetch_entry("P60174")
    context = Context("P60174", entry)
    assert context.xref_properties("Ensembl", "GeneId")
    assert not context.xref_properties("Ensembl", "ProteinId")
    card, _ = sabueso.resolve(
        "P60174", resolver=EntityResolver(client), diseases=options(enricher)
    )
    assert quality(card, enricher)["status"] == "not_queried"
    assert "no Ensembl protein" in quality(card, enricher)["detail"]


@pytest.mark.parametrize("enricher", SOURCES, ids=lambda e: e.option)
def test_refresh_keeps_historical_classification_and_both_pins(
    monkeypatch, tmp_path, enricher
):
    from sabueso.core import attribution, source_acquisition

    original_requests = type(enricher).requests

    def historical_requests(self, context, requested):
        try:
            return original_requests(self, context, requested)
        except RequestPrerequisiteMissing as exc:
            raise NothingToAsk(str(exc)) from exc

    monkeypatch.setattr(type(enricher), "client", forbidden)
    resolver = EntityResolver(MissingInputs())
    with monkeypatch.context() as old:
        old.setattr(type(enricher), "requests", historical_requests)
        historical, _ = sabueso.resolve(
            "P60174", resolver=resolver, **{enricher.option: options(enricher)}
        )
    before = deepcopy(historical.to_dict())
    assert quality(historical, enricher)["status"] == "not_found"
    assert all(r["state"] == "not_stated" for r in states(historical, enricher))
    store = sabueso.KnowledgeStore(tmp_path / "cards.db")
    old_pin = store.save(historical)
    refreshed, _ = sabueso.refresh_card(historical, resolver=resolver, store=store)
    assert quality(refreshed, enricher)["status"] == "not_queried"
    assert quality(refreshed, enricher)["request_options"] == options(enricher)
    assert all(
        (r["state"], r["count"]) == ("not_queried", None)
        for r in states(refreshed, enricher)
    )
    assert historical.to_dict() == before
    assert (
        refreshed.source_assertion_store.to_list()
        == historical.source_assertion_store.to_list()
    )
    assert refreshed.pinned_ref() != old_pin
    monkeypatch.setattr(sabueso, "resolve", forbidden)
    monkeypatch.setattr(attribution, "_credit", forbidden)
    monkeypatch.setattr(source_acquisition, "_credit", forbidden)
    credit_before = ackredit.get_attribution().to_dict()
    with sabueso.attribution() as trace:
        loaded = store.load(old_pin)
        assert canonical_json(loaded.to_dict()) == canonical_json(before)
        assert loaded.pinned_ref() == old_pin
        assert canonical_json(
            store.load(refreshed.pinned_ref()).to_dict()
        ) == canonical_json(refreshed.to_dict())
    assert not trace.acquisitions and not trace.records
    assert ackredit.get_attribution().to_dict() == credit_before


def requestable_context():
    entry, _ = FixtureUniProtClient("temp_data").fetch_entry("P60174")
    # Synthetic upstream identity statements; no private or new provider response.
    return Context(
        "P60174",
        entry,
        mappings=[
            {
                "fields": {
                    "annotations.clinical_variants": [
                        {"conditions": [{"xrefs": ["MEDGEN:C123", "omim:123"]}]}
                    ]
                }
            }
        ],
    )


@pytest.mark.parametrize("refs", [[], ["HP:123"], ["MEDGEN:C123"], ["MEDGEN:C3661900"]])
@pytest.mark.parametrize("supplied", [False, True])
def test_mondo_named_condition_without_queryable_identity_is_unasked(
    monkeypatch, refs, supplied
):
    enricher = next(e for e in SOURCES if e.option == "disease_identity")
    monkeypatch.setattr(type(enricher), "client", forbidden)
    context = Context(
        "P60174",
        {"organism": {"taxonId": 9606}},
        mappings=[
            {
                "fields": {
                    "annotations.clinical_variants": [
                        {"conditions": [{"name": "synthetic condition", "xrefs": refs}]}
                    ]
                }
            }
        ],
    )
    mapped, records = [], []
    credit_before = ackredit.get_attribution().to_dict()
    with sabueso.attribution() as trace:
        run(
            enricher,
            context,
            True,
            ForbiddenClient() if supplied else None,
            mapped,
            records,
        )
    assert not mapped
    assert records[0]["status"] == "not_queried"
    assert "no queryable disease id" in records[0]["detail"]
    for area in enricher.areas:
        row = _enrichment_row(area, enricher.source, records)
        assert (row["state"], row["count"]) == ("not_queried", None)
    assert not trace.acquisitions and not trace.records
    assert ackredit.get_attribution().to_dict() == credit_before


@pytest.mark.parametrize("enricher", SOURCES, ids=lambda e: e.option)
@pytest.mark.parametrize("outcome", ["empty", "not_found", "failed"])
def test_requestable_source_preserves_empty_missing_and_failed_outcomes(
    enricher, outcome
):
    calls = []

    class Client:
        def __getattr__(self, name):
            def answer(*args):
                calls.append((name, args))
                if outcome == "not_found":
                    raise RecordNotFoundError(
                        "synthetic native missing", version="native"
                    )
                if outcome == "failed":
                    raise ConnectorError("synthetic source failure")
                if name == "equivalent":
                    return {"mondo": None, "version": "native"}
                if name == "associations":
                    return {"record": {}, "version": {"knowledge": "native"}}
                return {"record": {}, "version": "native"}

            return answer

    context = requestable_context()
    mapped, records = [], []
    with sabueso.attribution() as trace:
        run(
            enricher,
            context,
            options(enricher),
            Client(),
            mapped,
            records,
        )
    assert calls
    (record,) = records
    assert record["status"] == ("error" if outcome == "failed" else "not_found")
    assert record["request_options"] == options(enricher)
    if outcome == "not_found":
        assert record["version"] == "native"
    for area in enricher.areas:
        row = _enrichment_row(area, enricher.source, records)
        assert row["state"] == ("unavailable" if outcome == "failed" else "not_stated")
    # Supplied unobserved clients must not invent an acquisition or resource credit.
    assert not trace.acquisitions and not trace.records


@pytest.mark.parametrize(
    "enricher", [e for e in SOURCES if e.organisms], ids=lambda e: e.option
)
def test_unsupported_taxon_stays_not_applicable_before_prerequisites(
    monkeypatch, enricher
):
    monkeypatch.setattr(type(enricher), "client", forbidden)
    mapped, records = [], []
    run(
        enricher,
        Context("synthetic", {"organism": {"taxonId": 5693}}),
        options(enricher),
        None,
        mapped,
        records,
    )
    assert not mapped and records[0]["status"] == "not_applicable"


@pytest.mark.parametrize(
    "enricher",
    [
        e
        for e in SOURCES
        if e.option in {"diseases", "clinvar", "medgen", "disease_identity"}
    ],
    ids=lambda e: e.option,
)
def test_observed_empty_answer_keeps_actual_source_operation_and_credit(
    tmp_path, enricher
):
    from sabueso.tools.db import clinvar, diseases, medgen, mondo

    context = requestable_context()
    if enricher.option == "diseases":
        directory = tmp_path / "diseases"
        directory.mkdir()
        (directory / "versions.json").write_text(json.dumps({"knowledge": "synthetic"}))
        (directory / "knowledge.tsv").write_text("")
        client = diseases.FixtureDISEASESClient(tmp_path)
    elif enricher.option == "clinvar":
        directory = tmp_path / "clinvar"
        directory.mkdir()
        for gene in context.xrefs("GeneID"):
            (directory / f"{gene['id']}.json").write_text(
                json.dumps({"record": [], "total_count": 0, "version": "synthetic"})
            )
        client = clinvar.FixtureClinVarClient(tmp_path)
    elif enricher.option == "medgen":
        directory = tmp_path / "medgen"
        directory.mkdir()
        (directory / "concepts.json").write_text(
            json.dumps({"record": {}, "version": "synthetic"})
        )
        client = medgen.FixtureMedGenClient(tmp_path)
    else:
        directory = tmp_path / "mondo"
        directory.mkdir()
        (directory / "mondo.obo").write_text(
            "format-version: 1.2\ndata-version: synthetic\n\n"
            "[Term]\nid: MONDO:0000001\nname: synthetic unrelated disease\n"
        )
        client = mondo.FixtureMONDOClient(tmp_path)
    mapped, records = [], []
    with sabueso.attribution() as trace:
        run(enricher, context, options(enricher), client, mapped, records)
    assert records[0]["status"] == "not_found"
    assert trace.acquisitions
    assert {r["source"] for r in trace.acquisitions} == {enricher.source}
    for acquired in trace.acquisitions:
        assert acquired["outcome"] == "empty"
        assert acquired["provider"]["status"] == "available"
        assert acquired["provider"]["attribution"]
        assert acquired["network_attempts"] == 0
