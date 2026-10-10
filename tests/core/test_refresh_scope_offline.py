"""Requested scope survives refresh, including failures and incomplete old records."""

import copy
import json
from types import SimpleNamespace

import pytest

import sabueso
from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.migration import rebuild_options
from sabueso.core.refresh_scope import restoration_plan
from sabueso.enrichers import ENRICHERS
from sabueso.resolver import EntityResolver, FixtureUniProtClient


def _scope(*records):
    return SimpleNamespace(quality={"enrichments": list(records)})


@pytest.fixture
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data"))


SELECTORS = [(e, kind) for e in ENRICHERS for kind in e.record_kinds]


@pytest.mark.parametrize(
    "enricher,kind", SELECTORS, ids=[f"{e.option}:{k}" for e, k in SELECTORS]
)
def test_every_declared_selector_restores_a_failed_record(enricher, kind):
    value = (
        {"article_ids": ["MED:18562316"]}
        if kind == "located_accession_annotations"
        else enricher.default_request
    )
    record = {
        "source": enricher.source,
        "data": kind,
        "status": "error",
        "request_options": value,
    }
    options, report = restoration_plan(_scope(record))
    assert options == {enricher.option: value}
    assert report[0]["basis"] == "recorded_request_options"
    assert report[0]["original_statuses"] == ["error"]


@pytest.mark.parametrize(
    "status",
    ["added", "partial", "not_found", "error", "not_queried", "not_applicable"],
)
def test_status_and_absent_selected_fields_never_remove_a_request(status):
    card = _scope(
        {
            "source": "OMA",
            "status": status,
            "request_options": {"limit": 2, "rel_type": "1:1", "taxa": [9606]},
        }
    )
    assert rebuild_options(card) == {
        "oma": {"limit": 2, "rel_type": "1:1", "taxa": [9606]}
    }


@pytest.mark.parametrize("enricher", ENRICHERS, ids=lambda e: e.option)
def test_historical_declared_requests_report_missing_parameters(enricher):
    options, report = restoration_plan(
        _scope(
            {
                "source": enricher.source,
                "data": enricher.match.get("data"),
                "status": "error",
            }
        )
    )
    assert options == {enricher.option: enricher.default_request}
    assert report[0]["unrecorded_parameters"] == sorted(enricher.historical_parameters)
    assert report[0]["basis"] != "recorded_request_options"


def test_historical_filters_limits_zero_score_and_article_union_are_preserved():
    options, report = restoration_plan(
        _scope(
            {
                "source": "OMA",
                "filters": {"rel_type": "1:1", "taxa": [9606]},
                "limit": 3,
            },
            {"source": "STRING", "required_score": 0, "limit": 7},
            {"source": "DISEASES", "channels": ("knowledge", "experiments")},
            {"source": "BindingDB", "cutoff": 125.5, "limit": 3},
            {"source": "PubChem BioAssay", "limit": 5},
            {
                "source": "Europe PMC",
                "data": "located_accession_annotations",
                "article_ids": ["MED:18562316"],
            },
            {
                "source": "Europe PMC",
                "data": "located_accession_annotations",
                "article_ids": ["MED:18562316", "PMC:PMC12400196"],
            },
        )
    )
    assert options == {
        "oma": {"rel_type": "1:1", "taxa": [9606], "limit": 3},
        "string": {"required_score": 0, "limit": 7},
        "diseases": {"channels": ["knowledge", "experiments"]},
        "bindingdb": {"cutoff": 125.5, "limit": 3},
        "pubchem_bioassay": {"limit": 5},
        "europepmc": {"article_ids": ["MED:18562316", "PMC:PMC12400196"]},
    }
    assert not any(row["unrecorded_parameters"] for row in report)


@pytest.mark.parametrize(
    "records",
    [
        [
            {"source": "OMA", "request_options": {"limit": 1}},
            {"source": "OMA", "request_options": {"limit": 2}},
        ],
        [{"source": "OMA", "limit": 1}, {"source": "OMA", "limit": 2}],
        [
            {"source": "OMA", "request_options": {"limit": 1}},
            {"source": "OMA", "limit": 2},
        ],
        [
            {
                "source": "Europe PMC",
                "data": "located_accession_annotations",
                "status": "error",
            }
        ],
        [
            {"source": "Europe PMC", "limit": 1},
            {
                "source": "Europe PMC",
                "data": "located_accession_annotations",
                "article_ids": ["MED:1"],
            },
        ],
        [
            {
                "source": "Europe PMC",
                "data": "located_accession_annotations",
                "request_options": {"limit": 2},
            }
        ],
        [{"source": "STRING", "request_options": {"required_score": 1001}}],
    ],
)
def test_unrestorable_known_scope_requires_an_override_before_resolution(
    records, resolver, monkeypatch
):
    card, _ = sabueso.resolve("P52270", resolver=resolver)
    card.quality["enrichments"] = records
    monkeypatch.setattr(
        sabueso,
        "resolve",
        lambda *a, **k: pytest.fail("Must refuse before acquisition"),
    )
    with pytest.raises(StorageError, match="Pass .* explicitly"):
        sabueso.refresh_card(card, resolver=resolver)
    with pytest.raises(StorageError):
        rebuild_options(card)


def test_explicit_disabled_override_resolves_a_conflict(resolver):
    card, _ = sabueso.resolve("P52270", resolver=resolver)
    card.quality["enrichments"] = [
        {"source": "OMA", "limit": 1},
        {"source": "OMA", "limit": 2},
    ]
    refreshed, _ = sabueso.refresh_card(card, resolver=resolver, oma=None)
    assert not refreshed.quality.get("enrichments")
    (row,) = refreshed.quality["migration"][-1]["request_restoration"]["requests"]
    assert (row["status"], row["basis"]) == ("overridden", "unrestorable_request")


def test_partial_records_do_not_claim_all_parameters_were_saved():
    card = _scope(
        {"source": "OMA", "request_options": {"limit": 2}},
        {"source": "OMA", "status": "error"},
    )
    options, report = restoration_plan(card)
    assert options == {"oma": {"limit": 2}}
    assert report[0]["basis"] == "partially_recorded_request"
    assert report[0]["unrecorded_parameters"] == ["limit", "rel_type", "taxa"]


def test_tuple_and_serialized_list_options_restore_identically_without_aliasing():
    original = {"source": "OMA", "request_options": {"taxa": (9606, 353153)}}
    options, _ = restoration_plan(_scope(original, json.loads(json.dumps(original))))
    options["oma"]["taxa"].append(1)
    assert original["request_options"]["taxa"] == (9606, 353153)


def test_unsupported_and_indirect_requests_are_inspectable_without_guessing(resolver):
    card, _ = sabueso.resolve("P52270", resolver=resolver)
    card.quality["enrichments"] = [
        {"source": "Historical provider", "data": "unknown", "status": "error"},
        {
            "source": "ChEMBL",
            "data": "assays named by PubChem copies",
            "status": "added",
        },
    ]
    before = copy.deepcopy(card.to_dict())
    refreshed, _ = sabueso.refresh_card(card, resolver=resolver)
    rows = refreshed.quality["migration"][-1]["request_restoration"]["requests"]
    assert [row["status"] for row in rows] == ["unsupported", "dependent_request"]
    assert rows[0]["record_indices"] == [0]
    assert rows[0]["original_statuses"] == ["error"]
    assert card.to_dict() == before


def test_public_uniref_refresh_retains_source_assertions_and_historical_pin(
    resolver, tmp_path, monkeypatch
):
    from sabueso.tools.db.uniref import FixtureUniRefClient

    clients = {"resolver": resolver, "uniref_client": FixtureUniRefClient("temp_data")}
    card, _ = sabueso.resolve("P52270", uniref=True, **clients)
    before = copy.deepcopy(card.to_dict())
    store = sabueso.KnowledgeStore(tmp_path / "cards.db")
    refreshed, _ = sabueso.refresh_card(card, store=store, **clients)
    assert refreshed.relationships("clustered_with") == card.relationships(
        "clustered_with"
    )
    assert (
        refreshed.source_assertion_store.to_list()
        == card.source_assertion_store.to_list()
    )
    assert store.load(card.pinned_ref()).to_dict() == before
    assert card.to_dict() == before
    monkeypatch.setattr(
        sabueso, "resolve", lambda *a, **k: pytest.fail("Saved readers cannot acquire")
    )
    assert store.load(refreshed.pinned_ref()).to_dict() == refreshed.to_dict()
    assert store.load(card.pinned_ref()).to_dict() == before


def test_public_oma_refresh_preserves_nondefault_filters_and_limit(resolver):
    from sabueso.tools.db.oma import FixtureOMAClient

    options = {"limit": 2, "rel_type": "1:1", "taxa": [353153, 9606]}
    clients = {"resolver": resolver, "oma_client": FixtureOMAClient("temp_data")}
    card, _ = sabueso.resolve("P60174", oma=options, **clients)
    refreshed, _ = sabueso.refresh_card(card, **clients)
    assert refreshed.relationships("ortholog_of") == card.relationships("ortholog_of")
    assert refreshed.quality["enrichments"][0]["request_options"] == options
    assert len(refreshed.relationships("ortholog_of")) <= 2


def test_failed_oma_request_retains_parameters_and_can_be_retried_or_disabled(resolver):
    class FailingOMA:
        calls = 0

        def xrefs(self, accession):
            self.calls += 1
            raise ConnectorError("Synthetic source failure")

    client = FailingOMA()
    with pytest.warns(sabueso._private.smonitor.warnings.EnrichmentFailedWarning):
        card, _ = sabueso.resolve(
            "P60174",
            resolver=resolver,
            oma={"limit": 2, "rel_type": "1:1"},
            oma_client=client,
        )
    with pytest.warns(sabueso._private.smonitor.warnings.EnrichmentFailedWarning):
        refreshed, _ = sabueso.refresh_card(card, resolver=resolver, oma_client=client)
    assert client.calls == 2
    assert refreshed.quality["enrichments"][0]["status"] == "error"
    assert refreshed.quality["enrichments"][0]["request_options"] == {
        "limit": 2,
        "rel_type": "1:1",
    }
    disabled, _ = sabueso.refresh_card(
        card, resolver=resolver, oma=None, oma_client=client
    )
    assert client.calls == 2
    assert not disabled.quality.get("enrichments")


def test_public_gnomad_pext_and_gtex_refresh_keeps_dependent_scope(resolver):
    from sabueso.tools.db.gnomad import FixtureGnomADClient
    from sabueso.tools.db.gtex import FixtureGTExClient

    clients = {
        "resolver": resolver,
        "gnomad_client": FixtureGnomADClient("temp_data"),
        "gtex_client": FixtureGTExClient("temp_data"),
    }
    card, _ = sabueso.resolve("P60174", exon_usage=True, gtex=True, **clients)
    refreshed, _ = sabueso.refresh_card(card, **clients)
    assert {r["source"] for r in refreshed.quality["enrichments"]} == {"gnomAD", "GTEx"}
    assert refreshed.to_dict()["sections"] == card.to_dict()["sections"]
    assert (
        refreshed.source_assertion_store.to_list()
        == card.source_assertion_store.to_list()
    )


def test_blocked_gtex_remains_requested_without_constructing_a_client(
    resolver, monkeypatch
):
    from sabueso.enrichers.gtex import ENRICHER

    monkeypatch.setattr(
        ENRICHER, "client", lambda: pytest.fail("Missing pext must block the client")
    )
    card, _ = sabueso.resolve("P60174", resolver=resolver, gtex=True)
    refreshed, _ = sabueso.refresh_card(card, resolver=resolver)
    assert refreshed.quality["enrichments"][0]["status"] == "not_queried"
    assert refreshed.quality["enrichments"][0]["request_options"] is True


def test_terms_excluded_request_keeps_nondefault_options(resolver):
    from sabueso.tools.db.europepmc import FixtureEuropePMCClient

    value = {"article_ids": ["PMC:PMC12400196"]}
    card, _ = sabueso.resolve(
        "P52270", resolver=resolver, terms="commercial", europepmc=value
    )
    assert card.quality["enrichments"][0]["status"] == "not_queried"
    assert rebuild_options(card)["europepmc"] == value
    refreshed, _ = sabueso.refresh_card(
        card, resolver=resolver, europepmc_client=FixtureEuropePMCClient("temp_data")
    )
    assert refreshed.quality["enrichments"][0]["status"] == "not_queried"
    assert refreshed.quality["enrichments"][0]["request_options"] == value
    assert refreshed.quality["terms_profile"]["profile"] == "commercial"


def test_original_all_structure_scope_is_distinct_from_old_explicit_ids():
    assert rebuild_options(
        _scope({"source": "RCSB PDB", "structure": "1TCD", "request_options": "all"})
    ) == {"structures": "all"}
    assert rebuild_options(_scope({"source": "RCSB PDB", "structure": "1TCD"})) == {
        "structures": ["1TCD"]
    }


def test_partial_structure_requests_cannot_drop_a_recorded_structure():
    card = _scope(
        {"source": "RCSB PDB", "structure": "1TCD", "request_options": ["1TCD"]},
        {"source": "RCSB PDB", "structure": "1SUX"},
    )
    with pytest.raises(StorageError, match="Structure ids contradict"):
        rebuild_options(card)


def test_disabled_recorded_bioassay_scope_is_not_called_restored():
    with pytest.raises(StorageError, match="does not request"):
        rebuild_options(
            _scope({"source": "PubChem BioAssay", "request_options": False})
        )
