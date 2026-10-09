"""An unanswered native scope is failure, not absent knowledge (#137)."""

import importlib
import io
import json

import pytest

from sabueso.core.errors import ConnectorError, RecordNotFoundError

ROUTES = [
    ("gtex", "tissues", "gtex_v10"),
    ("uniref", "clusters", "P52270"),
    ("uniref", "members", "UniRef90_P52270"),
    ("oma", "xrefs", "P52270"),
    ("oma", "protein", "TRYCC03899"),
    ("oma", "orthologs", "P52270"),
    ("oma", "accessions", ["TPIS_HUMAN"]),
    ("gnomad", "variants", "ENSG00000111669"),
    ("gnomad", "transcript_variants", "ENST00000396705"),
    ("gnomad", "pext", "ENSG00000111669"),
    ("gnomad", "consequences", ["12-6869106-A-G"]),
]
CLIENTS = {
    "gtex": "OnlineGTExClient",
    "uniref": "OnlineUniRefClient",
    "oma": "OnlineOMAClient",
    "gnomad": "OnlineGnomADClient",
}


class Reply(io.BytesIO):
    headers = {}


def ask(monkeypatch, route, response):
    source, method, identifier = route
    module = importlib.import_module("sabueso.tools.db." + source)
    monkeypatch.setattr(
        module,
        "urlopen",
        lambda *args, **kwargs: Reply(json.dumps(response).encode()),
    )
    return getattr(getattr(module, CLIENTS[source])(), method)(identifier)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("response", [None, False, "not an answer", 42])
def test_scalar_answers_are_connector_failures(monkeypatch, route, response):
    with pytest.raises(ConnectorError):
        ask(monkeypatch, route, response)


@pytest.mark.parametrize("route", ROUTES)
def test_wrong_or_missing_envelopes_are_not_absence(monkeypatch, route):
    # OMA protein objects must identify the requested native record; list routes
    # require lists. Other routes require their own explicitly stated envelope.
    with pytest.raises(ConnectorError):
        ask(monkeypatch, route, {})


@pytest.mark.parametrize(
    "route,response",
    [
        (ROUTES[0], {"data": [None]}),
        (ROUTES[0], {"data": {"error": "unavailable"}}),
        (ROUTES[1], {"results": [None]}),
        (ROUTES[2], {"results": {}}),
        (ROUTES[3], [None]),
        (ROUTES[5], ["not an ortholog"]),
        (ROUTES[6], {"results": [None]}),
        (ROUTES[7], {"data": []}),
        (ROUTES[7], {"data": {"gene": {}}}),
        (ROUTES[7], {"data": {"gene": {"variants": [None]}}}),
        (ROUTES[8], {"data": {"transcript": {"variants": "unknown"}}}),
        (ROUTES[9], {"data": {"gene": {}}}),
        (ROUTES[9], {"data": {"gene": {"pext": {}}}}),
        (ROUTES[9], {"data": {"gene": {"pext": {"regions": [None]}}}}),
        (ROUTES[10], {"data": {}}),
        (ROUTES[10], {"data": {"v1": None}}),
        (ROUTES[10], {"data": {"v0": {}}}),
        (ROUTES[10], {"data": {"v0": {"transcript_consequences": [None]}}}),
    ],
)
def test_nested_unanswered_scopes_are_connector_failures(monkeypatch, route, response):
    with pytest.raises(ConnectorError):
        ask(monkeypatch, route, response)


@pytest.mark.parametrize("route", ROUTES[7:])
def test_graphql_errors_cannot_be_silent_success(monkeypatch, route):
    response = {
        "data": {
            "gene": {"variants": [], "pext": None},
            "transcript": {"variants": []},
            "v0": None,
        },
        "errors": [{"message": "backend unavailable"}],
    }
    with pytest.raises(ConnectorError):
        ask(monkeypatch, route, response)


@pytest.mark.parametrize(
    "route,response",
    [
        (ROUTES[0], {"data": []}),
        (ROUTES[7], {"data": {"gene": None}}),
        (ROUTES[8], {"data": {"transcript": None}}),
        (ROUTES[9], {"data": {"gene": {"pext": None}}}),
        (ROUTES[9], {"data": {"gene": {"pext": {"regions": []}}}}),
    ],
)
def test_explicit_native_absence_remains_absence(monkeypatch, route, response):
    with pytest.raises(RecordNotFoundError):
        ask(monkeypatch, route, response)


@pytest.mark.parametrize(
    "route,response,record",
    [
        (ROUTES[1], {"results": []}, []),
        (ROUTES[2], {"results": []}, []),
        (ROUTES[3], [], []),
        (ROUTES[5], [], []),
        (ROUTES[7], {"data": {"gene": {"variants": []}}}, {"gene": {}, "variants": []}),
        (
            ROUTES[8],
            {"data": {"transcript": {"variants": []}}},
            {"transcript": {}, "variants": []},
        ),
    ],
)
def test_explicit_empty_collections_remain_empty(monkeypatch, route, response, record):
    assert ask(monkeypatch, route, response)["record"] == record


def test_missing_native_variants_and_empty_consequences_are_distinct(monkeypatch):
    route = ROUTES[10]
    assert ask(monkeypatch, route, {"data": {"v0": None}})["record"] == {}
    assert ask(monkeypatch, route, {"data": {"v0": {"transcript_consequences": []}}})[
        "record"
    ] == {"12-6869106-A-G": []}


def test_empty_native_entry_name_search_remains_empty(monkeypatch):
    assert ask(monkeypatch, ROUTES[6], {"results": []}) == {}


@pytest.mark.parametrize(
    "source,options,area,scientific_source",
    [
        (
            "gtex",
            {"gtex": True, "exon_usage": True},
            "annotations.tissue_terms",
            "GTEx",
        ),
        ("gnomad", {"gnomad": {}}, "annotations.population_variants", "gnomAD"),
        ("oma", {"oma": {}}, "relationships.ortholog_of", "OMA"),
        ("uniref", {"uniref": True}, "identifiers.uniref", "UniProt"),
    ],
)
def test_malformed_native_answers_leave_knowledge_unavailable(
    monkeypatch, source, options, area, scientific_source
):
    import sabueso
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.gnomad import FixtureGnomADClient

    module = importlib.import_module("sabueso.tools.db." + source)
    monkeypatch.setattr(module, "urlopen", lambda *args, **kwargs: Reply(b"{}"))
    clients = {source + "_client": getattr(module, CLIENTS[source])()}
    if source == "gtex":
        clients["gnomad_client"] = FixtureGnomADClient("temp_data")
    with pytest.warns(EnrichmentFailedWarning):
        card, _ = sabueso.resolve(
            "P60174",
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            **options,
            **clients,
        )
    rows = [
        row
        for row in card.knowledge_state()["rows"]
        if row["source"] == scientific_source and row["area"] == area
    ]
    assert rows and all(row["state"] == "unavailable" for row in rows)
    assert card.get("sequence.primary")["value"]
    assert card.get("sequence.primary")["source_assertion_ids"]


def test_explicit_gnomad_not_found_errors_remain_absence(monkeypatch):
    with pytest.raises(RecordNotFoundError):
        ask(monkeypatch, ROUTES[7], {"errors": [{"message": "Gene not found"}]})


def test_mixed_gnomad_not_found_and_failure_is_not_absence(monkeypatch):
    with pytest.raises(ConnectorError):
        ask(
            monkeypatch,
            ROUTES[7],
            {"errors": [{"message": "Gene not found"}, {"message": "backend failed"}]},
        )
