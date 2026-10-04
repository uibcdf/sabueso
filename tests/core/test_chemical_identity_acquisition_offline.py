"""CCD/UniChem identity access retains original traces, scope and attribution."""

import io
import json
from datetime import timedelta
from email.message import Message
from urllib.error import HTTPError, URLError

import ackredit
import pytest

import sabueso
from sabueso.core import attribution as adapter
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db import _http, pdb_ccd, unichem
from sabueso.tools.db.chembl import FixtureChEMBLClient

KEY = "XBNHRNFODJOFRU-UHFFFAOYSA-N"
COMPONENT = {
    "chem_comp": {
        "id": "BTS",
        "name": "Synthetic component",
        "pdbx_release_status": "REL",
    },
    "rcsb_chem_comp_descriptor": {"InChIKey": KEY},
}
COMPOUND = {
    "uci": 1,
    "standardInchiKey": KEY,
    "sources": [
        {
            "id": 31,
            "shortName": "bindingdb",
            "compoundId": "11",
            "date": "original-source-date",
        }
    ],
    "inchi": {"inchi": "InChI=1S/synthetic"},
}
KINDS = ("ccd", "inchikey", "source")


@pytest.fixture(autouse=True)
def independent_workflow():
    with ackredit.session("chemical identity observation"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload, *, raw=False):
        super().__init__(payload if raw else json.dumps(payload).encode())
        self.headers = Message()


def serve(monkeypatch, kind, *, empty=False, error=None, payload=None):
    calls = []
    monkeypatch.setattr(_http, "_wait", lambda *a: 0)

    def response(request, timeout):
        calls.append(request)
        if error == "timeout":
            raise URLError(TimeoutError("synthetic timeout"))
        if error == "malformed":
            return Response(b"not JSON", raw=True)
        if error:
            raise HTTPError(request.full_url, error, "synthetic", Message(), None)
        answer = (
            {"data": {"chem_comps": [] if empty else [COMPONENT]}}
            if kind == "ccd"
            else {"compounds": [] if empty else [COMPOUND]}
        )
        return Response(answer if payload is None else payload)

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def lookup(kind, client=None):
    if kind == "ccd":
        return pdb_ccd.get_components(["bts", "BTS", "UNK"], client=client)
    if kind == "inchikey":
        return unichem.get_compound(KEY, client=client)
    return (client or unichem.OnlineUniChemClient()).compound_by_source(31, "11")


def observed_lookup(kind, client=None):
    with sabueso.attribution() as run:
        result = lookup(kind, client)
    (observed,) = run.acquisitions
    if kind != "source":
        assert result["acquisition_trace"]["records"] == [observed]
    return result, observed


@pytest.mark.parametrize("kind", KINDS)
def test_queries_raw_returns_original_identifiers_versions_and_resource_roles(
    monkeypatch, kind
):
    calls = serve(monkeypatch, kind)
    result, observed = observed_lookup(kind)
    assert observed["source"] == ("PDB CCD" if kind == "ccd" else "UniChem")
    assert (
        observed["operation"]
        == {
            "ccd": "components",
            "inchikey": "compound",
            "source": "compound_by_source",
        }[kind]
    )
    assert (
        observed["query"]
        == {
            "ccd": {"comp_ids": ["BTS", "UNK"]},
            "inchikey": {"inchikey": KEY},
            "source": {"source_id": 31, "compound_id": "11"},
        }[kind]
    )
    assert observed["source_version"] == {"value": None, "basis": "not_stated"}
    request = observed["requests"][0]
    assert (
        request["method"] == "POST"
        and request["request_sha256"]
        and request["response_sha256"]
    )
    assert observed["network_attempts"] == 1 and len(calls) == 1
    assert observed["count"] == 1
    if kind == "ccd":
        assert result["record"] == {
            "components": {"BTS": COMPONENT},
            "missing": ["UNK"],
        }
        assert observed["outcome"] == "partial"
        assert [e["outcome"] for e in observed["entries"]] == ["received", "empty"]
        assert observed["completed_ids"] == ["BTS", "UNK"]
        assert observed["entries"][0]["revision_metadata"] == {
            "pdbx_release_status": "REL"
        }
        assert observed["entries"][0]["source_version"]["value"] is None
        titles = [b["title"] for b in observed["bibliography"]]
        assert any("chemical component dictionary" in t for t in titles)
        assert any("RCSB" in t for t in titles)
    else:
        assert observed["outcome"] == "received"
        assert observed["identity_lookup"]["source_records"] == COMPOUND["sources"]
        assert observed["identity_lookup"]["uci"] == 1
        assert "not consulted" in observed["identity_lookup"]["source_records_basis"]
        assert not any(
            b.get("doi") == "10.1093/nar/gkae1075" for b in observed["bibliography"]
        )
        assert "date" not in (result.get("record") or result["compound"])["sources"][0]
    assert observed["provider"]["status"] == "available"
    attribution = ackredit.Attribution.from_dict(observed["provider"]["attribution"])
    roles = {role for use in attribution.to_dict()["uses"] for role in use["roles"]}
    assert {"resource_access", "resource_description", "executed_software"} <= roles
    assert "measurement_primary_citation" not in roles
    assert attribution.report(format="bibtex")


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_reuse_preserves_original_wire_decoded_query_and_retrieval_identities(
    monkeypatch, tmp_path, kind, mode
):
    calls = serve(monkeypatch, kind)
    archive = sabueso.RetrievalArchive(tmp_path / "identity.db")
    with archive.recording():
        _, original = observed_lookup(kind)
    context = (
        archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying()
    )
    with context:
        _, reused = observed_lookup(kind)
    assert len(calls) == 1
    assert reused["access"] == mode and reused["network_attempts"] == 0
    assert reused["retrieved_at"] == original["retrieved_at"]
    assert reused["source_version"] == original["source_version"]
    assert reused["response_identity"] == original["response_identity"]
    assert reused["pages"] == original["pages"]
    assert (
        reused["requests"][0]["response_sha256"]
        == original["requests"][0]["response_sha256"]
    )
    assert (
        reused["requests"][0]["retrieval_ref"]
        == original["requests"][0]["retrieval_ref"]
    )
    assert reused["provider"]["status"] == "available"
    assert reused["id"] != original["id"]


@pytest.mark.parametrize("kind", KINDS)
def test_evaluated_empty_is_credited_without_missing_fixture_or_absence_inference(
    monkeypatch, kind
):
    serve(monkeypatch, kind, empty=True)
    with sabueso.attribution() as run:
        if kind == "ccd":
            result = lookup(kind)
            assert result["record"]["components"] == {}
        else:
            with pytest.raises(RecordNotFoundError) as caught:
                lookup(kind)
            if kind == "inchikey":
                assert caught.value.acquisition_trace["records"] == run.acquisitions
    (observed,) = run.acquisitions
    assert observed["outcome"] == "empty" and observed["count"] == 0
    assert observed["provider"]["status"] == "available"


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("error", [404, 500, "timeout", "malformed"])
def test_original_failures_and_retry_facts_survive_without_success_credit(
    monkeypatch, kind, error
):
    calls = serve(monkeypatch, kind, error=error)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        lookup(kind)
    (observed,) = run.acquisitions
    assert (
        observed["outcome"] == "failed"
        and observed["provider"]["status"] == "not_attempted"
    )
    attempts = _http.RETRIES + 1 if error in (500, "malformed") else 1
    assert len(calls) == observed["network_attempts"] == attempts
    if attempts > 1:
        assert any(r["retries"] for r in observed["requests"])


@pytest.mark.parametrize("kind", KINDS)
def test_offline_unqueried_and_unavailable_fixtures_are_distinct(
    monkeypatch, tmp_path, kind
):
    calls = serve(monkeypatch, kind)
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    with (
        sabueso.attribution() as run,
        archive.replaying(),
        pytest.raises(ConnectorError),
    ):
        lookup(kind)
    assert run.acquisitions[0]["outcome"] == "not_queried" and not calls
    fixture = (
        pdb_ccd.FixtureCCDClient(tmp_path)
        if kind == "ccd"
        else unichem.FixtureUniChemClient(tmp_path)
    )
    with sabueso.attribution() as run:
        if kind == "ccd":
            lookup(kind, fixture)
        else:
            with pytest.raises(RecordNotFoundError):
                lookup(kind, fixture)
    observed = run.acquisitions[0]
    assert observed["outcome"] == "unavailable" and observed["access"] == "fixture"
    assert (
        observed["network_attempts"] == 0
        and observed["provider"]["status"] == "not_attempted"
    )


def test_fixture_mixed_batch_and_native_generator_query_remain_bounded():
    with sabueso.attribution() as run:
        result = pdb_ccd.FixtureCCDClient("temp_data").components(
            c for c in ("bts", "UNKNOWN", "BTS")
        )
    observed = run.acquisitions[0]
    assert observed["query"] == {"comp_ids": ["BTS", "UNKNOWN"]}
    assert list(result["components"]) == ["BTS"] and result["missing"] == ["UNKNOWN"]
    assert observed["outcome"] == "partial" and observed["completed_ids"] == ["BTS"]
    assert [e["outcome"] for e in observed["entries"]] == ["received", "unavailable"]
    assert observed["provider"]["status"] == "available"


def test_empty_batch_is_unqueried_without_transport_or_credit(monkeypatch):
    calls = serve(monkeypatch, "ccd")
    result = pdb_ccd.get_components([], skip_digestion=True)
    (observed,) = result["acquisition_trace"]["records"]
    assert observed["outcome"] == "not_queried" and not calls
    assert observed["count"] == 0 and observed["provider"]["status"] == "not_attempted"


def test_fixture_declared_empty_source_lookup_is_not_unavailable(tmp_path):
    path = tmp_path / "unichem"
    path.mkdir()
    (path / "source31__11.json").write_text(json.dumps({"not_found": True}))
    with sabueso.attribution() as run, pytest.raises(RecordNotFoundError):
        lookup(
            "source",
            unichem.FixtureUniChemClient(tmp_path, retrieved_at="original saved time"),
        )
    observed = run.acquisitions[0]
    assert (
        observed["outcome"] == "empty"
        and observed["retrieved_at"] == "original saved time"
    )
    assert observed["provider"]["status"] == "available"


def test_ccd_partial_graphql_failure_retains_received_component_subset(monkeypatch):
    serve(
        monkeypatch,
        "ccd",
        payload={
            "data": {"chem_comps": [COMPONENT]},
            "errors": [{"message": "synthetic incomplete graph"}],
        },
    )
    with pytest.raises(ConnectorError) as caught:
        lookup("ccd")
    (observed,) = caught.value.acquisition_trace["records"]
    assert observed["outcome"] == "partial" and observed["terminal_outcome"] == "failed"
    assert observed["completed_ids"] == ["BTS"] and observed["count"] == 1
    assert observed["entries"][1]["outcome"] == "failed"
    assert observed["provider"]["status"] == "available"


def test_unichem_received_data_survives_processing_failure_with_explicit_selection(
    monkeypatch,
):
    serve(
        monkeypatch,
        "source",
        payload={
            "compounds": [{**COMPOUND, "sources": [None]}, {**COMPOUND, "uci": 2}]
        },
    )
    with sabueso.attribution() as run, pytest.raises(AttributeError):
        lookup("source")
    observed = run.acquisitions[0]
    assert observed["outcome"] == "partial" and observed["terminal_outcome"] == "failed"
    assert observed["identity_lookup"]["returned_compound_count"] == 2
    assert observed["identity_lookup"]["uci"] == 1
    assert observed["provider"]["status"] == "available"


def test_threaded_source_lookup_retains_shared_capture_context(monkeypatch):
    serve(monkeypatch, "source")
    client = unichem.OnlineUniChemClient()
    with ackredit.capture("parallel identity") as capture, sabueso.attribution() as run:
        responses = _http.gather(
            lambda value: client.compound_by_source(31, value), ["11", "12"], workers=2
        )
    assert len(responses) == len(run.acquisitions) == 2
    assert {r["query"]["compound_id"] for r in run.acquisitions} == {"11", "12"}
    assert all(r["provider"]["status"] == "available" for r in run.acquisitions)
    assert {
        use["context"]["query"]["compound_id"]
        for use in capture.attribution.to_dict()["uses"]
        if "query" in use["context"]
    } == {"11", "12"}


def test_fixture_read_failure_retains_completed_components_without_hiding_the_error(
    tmp_path,
):
    directory = tmp_path / "pdb_ccd"
    directory.mkdir()
    (directory / "BTS.json").write_text(json.dumps(COMPONENT))
    (directory / "UNK.json").write_text("not JSON")
    with pytest.raises(json.JSONDecodeError) as caught:
        lookup(
            "ccd",
            pdb_ccd.FixtureCCDClient(tmp_path, retrieved_at="original saved time"),
        )
    (observed,) = caught.value.acquisition_trace["records"]
    assert observed["outcome"] == "partial" and observed["terminal_outcome"] == "failed"
    assert observed["completed_ids"] == ["BTS"]
    assert observed["retrieved_at"] == "original saved time"
    assert observed["entries"][1]["outcome"] == "failed"
    assert observed["provider"]["status"] == "available"


def test_molecule_and_ligand_deck_capture_exact_pins_without_serialization_changes(
    tmp_path,
):
    clients = {
        "chembl_client": FixtureChEMBLClient("temp_data"),
        "ccd_client": pdb_ccd.FixtureCCDClient("temp_data"),
        "unichem_client": unichem.FixtureUniChemClient("temp_data"),
    }
    card, resolution = sabueso.resolve_molecule_card("pdb.ligand:BTS", **clients)
    assert card.acquisition_trace == resolution.acquisition_trace
    trace = card.acquisition_trace
    assert trace["card_ref"] == card.pinned_ref()
    assert {r["source"] for r in trace["records"]} >= {"PDB CCD", "UniChem"}
    assert all(r["provider"]["status"] == "available" for r in trace["records"])
    protein = sabueso.resolve_protein_card(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        structures=["1SUX"],
    )[0]
    deck = sabueso.ligand_deck(protein, unichem=True, **clients)
    deck_trace = deck.acquisition_trace
    assert deck_trace["deck_snapshot_id"] == deck.snapshot_id()
    assert deck_trace["input_card_refs"] == [protein.pinned_ref()]
    assert deck_trace["card_refs"] == [c.pinned_ref() for c in deck.cards]
    assert {r["source"] for r in deck_trace["records"]} == {"PDB CCD", "UniChem"}
    assert "recording_error" not in deck_trace
    assert (
        "acquisition_trace" not in card.to_dict()
        and "acquisition_trace" not in deck.meta
    )
    trace["records"].clear()
    deck_trace["card_refs"].clear()
    assert card.acquisition_trace["records"] and deck.acquisition_trace["card_refs"]
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    pin = store.save(card)
    deck_pin = store.save_deck(deck, "ligands")
    before = ackredit.get_attribution().to_dict()
    loaded = store.load(pin)
    saved_deck = store.load_deck(deck_pin)
    assert loaded.acquisition_trace is saved_deck.acquisition_trace is None
    assert (
        loaded.snapshot_id() == card.snapshot_id()
        and saved_deck.snapshot_id() == deck.snapshot_id()
    )
    for observed in card.acquisition_trace["records"]:
        ackredit.Attribution.from_dict(
            json.loads(json.dumps(observed))["provider"]["attribution"]
        ).report(format="bibtex")
    assert ackredit.get_attribution().to_dict() == before
    assert deck.filter(lambda c: True).acquisition_trace is None


def test_failed_molecule_resolution_and_empty_deck_retain_honest_runtime_outcomes(
    tmp_path,
):
    card, resolution = sabueso.resolve_molecule_card(
        "pdb.ligand:BTS", ccd_client=pdb_ccd.FixtureCCDClient(tmp_path), unichem=False
    )
    assert (
        card is None
        and resolution.acquisition_trace["records"][0]["outcome"] == "unavailable"
    )
    protein = Card(
        meta={"card_id": "sabueso:protein:uniprot:P52270", "entity_type": "protein"}
    )
    deck = sabueso.ligand_deck(protein)
    assert not deck.cards and deck.acquisition_trace["records"] == []
    assert deck.acquisition_trace["deck_snapshot_id"] == deck.snapshot_id()


def test_nested_collectors_custom_client_and_provider_failure_preserve_boundaries(
    monkeypatch,
):
    serve(monkeypatch, "ccd")
    with sabueso.attribution() as outer:
        with sabueso.attribution() as inner:
            answer = lookup("ccd")
    assert (
        outer.acquisitions
        == inner.acquisitions
        == answer["acquisition_trace"]["records"]
    )

    class Custom:
        def components(self, comp_ids):
            return {
                "components": {"BTS": COMPONENT},
                "missing": [],
                "retrieved_at": "custom",
            }

    custom = lookup("ccd", Custom())
    assert not custom["acquisition_trace"]["records"]
    assert (
        custom["acquisition_trace"]["coverage"]["other_sources_and_custom_clients"]
        == "not_observed"
    )
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic provider failure")),
    )
    with pytest.warns(Warning, match="Attribution failed"):
        result = lookup("ccd")
    observed = result["acquisition_trace"]["records"][0]
    assert observed["provider"]["status"] == "failed" and result["record"]["components"]


def test_pin_recording_failure_keeps_deck_and_reports_a_gap(monkeypatch):
    monkeypatch.setattr(
        Deck,
        "snapshot_id",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic pin failure")),
    )
    protein = Card(
        meta={"card_id": "sabueso:protein:uniprot:P52270", "entity_type": "protein"}
    )
    with pytest.warns(Warning, match="Attribution failed"):
        deck = sabueso.ligand_deck(protein)
    assert (
        not deck.cards
        and "synthetic pin failure" in deck.acquisition_trace["recording_error"]
    )
