"""Declared enrichers (#86): every one is wired everywhere it must be, and the runner
treats every source the same way."""

import inspect
from pathlib import Path

import pytest
import yaml

from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.enrichers import (
    ENRICHERS,
    Context,
    Enricher,
    NothingToAsk,
    knowledge_areas,
    options_by_source,
    run,
)
from sabueso.tools.card.protein import resolve_protein_card

ARGUMENTS = Path("sabueso/_private/argdigest/argument")


@pytest.mark.parametrize("enricher", ENRICHERS, ids=lambda e: e.option)
def test_every_enricher_is_wired_everywhere(enricher):
    parameters = inspect.signature(inspect.unwrap(resolve_protein_card)).parameters
    assert {enricher.option, enricher.client_argument} <= set(parameters)
    for name in (enricher.option, enricher.client_argument):
        assert (ARGUMENTS / f"{name}.py").is_file(), name
    registry = yaml.safe_load(Path("devguide/sources/registry.yaml").read_text())
    (entry,) = [r for r in registry["resources"] if r["id"] == enricher.registry_id]
    assert entry["status"] == "in_use"
    assert enricher.areas
    rows = {(a, s) for a, s, _ in knowledge_areas(enricher.entity_type)}
    assert {(a, enricher.source) for a in enricher.areas} <= rows
    assert (
        enricher.option
        in options_by_source()[(enricher.source, enricher.match.get("data"))]
    )
    # A fixture client beside the online one, and a card in the card-shape builder that
    # uses it, so the recorded shape covers what the enricher adds.
    module = inspect.getmodule(type(enricher.client()))
    assert any(name.startswith("Fixture") for name in vars(module)), module.__name__
    assert f"{enricher.client_argument}=" in Path("tools/card_shape.py").read_text()


class _Toy(Enricher):
    option, source, registry_id = "toy", "Toy", "toy"
    areas = ("annotations.toy",)
    organisms = (9606,)
    coverage_detail = "Toy covers human genes only"

    def requests(self, context, options):
        genes = context.entry.get("genes") or []
        if not genes:
            raise NothingToAsk("no gene")
        from sabueso.enrichers import Request

        return [Request(g, {"source": "Toy", "identifier": g}) for g in genes]

    def fetch(self, client, request, options):
        return client(request.identifier)

    def map(self, context, request, response, options):
        return {"fields": {"annotations.toy": response}}, {"status": "added"}


def _run(entry, client):
    mappings, records = [], []
    run(_Toy(), Context("P1", entry), True, client, mappings, records)
    return mappings, records


def _client(gene):
    if gene == "missing":
        raise RecordNotFoundError("no such gene")
    if gene == "broken":
        raise ConnectorError("down")
    return [gene]


def test_the_runner_isolates_each_request_and_keeps_the_order():
    mappings, records = _run(
        {"organism": {"taxonId": 9606}, "genes": ["g1", "missing", "broken", "g2"]},
        _client,
    )
    assert [r["status"] for r in records] == ["added", "not_found", "error", "added"]
    assert [m["fields"]["annotations.toy"] for m in mappings] == [["g1"], ["g2"]]
    assert mappings[0]["relationships"] == []  # completed to a full mapping


def test_coverage_and_nothing_to_ask_are_not_errors():
    _, records = _run({"organism": {"taxonId": 5693}, "genes": ["g1"]}, _client)
    assert records == [
        {
            "source": "Toy",
            "identifier": "P1",
            "status": "not_applicable",
            "detail": "Toy covers human genes only",
        }
    ]
    _, records = _run({"organism": {"taxonId": 9606}}, _client)
    assert records[0]["status"] == "not_found" and records[0]["detail"] == "no gene"


def test_a_missing_key_is_not_queried_never_an_error():
    from sabueso.core.errors import MissingKeyError
    from sabueso.core.knowledge_state import _enrichment_row

    def keyless(gene):
        raise MissingKeyError("Toy answers only with a personal key")

    _, records = _run({"organism": {"taxonId": 9606}, "genes": ["g1"]}, keyless)
    assert records == [
        {
            "source": "Toy",
            "identifier": "g1",
            "status": "not_queried",
            "detail": "Toy answers only with a personal key",
        }
    ]
    row = _enrichment_row("annotations.toy", "Toy", records)
    assert row["state"] == "not_queried"
    assert row["basis"]["detail"] == "Toy answers only with a personal key"
