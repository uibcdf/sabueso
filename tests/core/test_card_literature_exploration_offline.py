"""Shared LIVE literature reads preserve public native context and source gaps."""

import socket
from copy import deepcopy
from pathlib import Path

import pytest
import pyunitwizard as puw

import sabueso
from sabueso._private.smonitor.warnings import (
    EnrichmentFailedWarning,
    EnrichmentTruncatedWarning,
)
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.quantities import seal
from sabueso.core.relationship_store import make_relationship
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.card.disease import resolve_disease_card
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient
from sabueso.tools.db.mondo import FixtureMONDOClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"
if not (DATA / "chembl/CHEMBL5834.json").is_file():
    DATA = Path.cwd() / "temp_data"
TOPIC = "literature"
BENZ_PAPER = "pubmed:20889239"
BTS_PAPER = "pubmed:35189560"
LOCATED_PAPER = "pubmed:40832834"
ARTICLE = "PMC:PMC12400196"


def forbidden(*args, **kwargs):
    pytest.fail("Captured literature exploration must not acquire sources")


def serialized_native(value):
    """Normalize actual quantities without interpreting literal source strings."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, dict):
        return {key: serialized_native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialized_native(item) for item in value]
    assert puw.is_quantity(value)
    number, unit = puw.get_value_and_unit(value)
    return {"value": float(number), "unit": str(unit)}


@pytest.fixture(scope="module")
def public_originals():
    def protein(identifier="P60174", **kwargs):
        return sabueso.resolve(
            identifier, resolver=EntityResolver(FixtureUniProtClient(DATA)), **kwargs
        )[0]

    def located(articles):
        return protein(
            europepmc={"article_ids": articles},
            europepmc_client=FixtureEuropePMCClient(DATA),
        )

    with pytest.MonkeyPatch.context() as guard:
        guard.setattr(socket.socket, "connect", forbidden)
        guard.setattr(socket, "create_connection", forbidden)
        cards = {
            "tctim": protein(
                "P52270", chembl={}, chembl_client=FixtureChEMBLClient(DATA)
            ),
            "bare": protein(),
            "located": located(ARTICLE),
            "empty": located("MED:18562316"),
            "molecule": single_molecule_card(
                chembl=FixtureChEMBLClient(DATA).molecules(["CHEMBL110"])
            ),
            "disease": resolve_disease_card(
                "MONDO:0014221", mondo_client=FixtureMONDOClient(DATA)
            )[0],
        }
        with pytest.warns(EnrichmentFailedWarning):
            cards["failed"] = located("MED:1")
        with pytest.warns(EnrichmentFailedWarning):
            cards["mixed"] = located([ARTICLE, "MED:1"])
        with pytest.warns(EnrichmentTruncatedWarning):
            cards["search"] = protein(
                europepmc={}, europepmc_client=FixtureEuropePMCClient(DATA)
            )
    return {name: card.to_dict() for name, card in cards.items()}


@pytest.fixture(autouse=True)
def retained_only(public_originals, monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    for client in (
        FixtureUniProtClient,
        FixtureChEMBLClient,
        FixtureEuropePMCClient,
        FixtureMONDOClient,
    ):
        monkeypatch.setattr(client, "__init__", forbidden)
    monkeypatch.setattr(sabueso, "resolve", forbidden)
    monkeypatch.setattr(sabueso, "refresh_card", forbidden)


@pytest.fixture
def card(public_originals):
    return Card.from_dict(deepcopy(public_originals["tctim"]))


def restored(public_originals, name):
    return Card.from_dict(deepcopy(public_originals[name]))


def publication(view, ref):
    return next(
        item for item in view.items() if item.cells["publication_ref"].value == ref
    )


def role(links, name):
    return next(item for item in links.items() if item.cells["role"].value == name)


def frames(selection, **kwargs):
    cursor, rows, seen = None, [], set()
    while True:
        page = selection.page(cursor=cursor, **kwargs)
        assert len(canonical_json(page).encode("utf-8")) <= kwargs.get(
            "max_bytes", 65536
        )
        assert page["page"]["blocked"] is None
        rows.extend(page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            return rows
        assert cursor not in seen
        seen.add(cursor)


def explained_native(explorer, item_ref):
    """Inspect original machine explanation locations through public access."""
    return {
        row["key"]: explorer.inspect(locator=row["location"]).native_payload
        for row in frames(explorer.access.explain(item_ref), max_bytes=16384)
    }


def machine_value(explorer, row, column):
    cell = row["cells"][column]
    if cell["value_included"]:
        return cell["value"]
    return explorer.inspect(locator=cell["value_location"]).native_payload


def synthetic_card():
    return Card(
        meta={"card_id": "sabueso:protein:uniprot:P60174", "entity_type": "protein"}
    )


def add_publication(card, ref, title="Synthetic citation control", **fields):
    """Explicit synthetic bibliographic edge; no statement about a real paper."""
    subject = card.id.split(":", 2)[2]
    qualifiers = {"title": title, **fields}
    assertion = make_source_assertion(
        "relationships.described_in",
        qualifiers,
        "Synthetic literature control",
        ref,
        "2026-11-07",
        subject_ref=subject,
    )
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(
        make_relationship(subject, "described_in", ref, qualifiers, [assertion["id"]])
    )
    return assertion


def test_overview_human_question_and_agent_preserve_complete_native_order(card):
    before = card.to_dict()
    expected = serialized_native(card.literature())
    explorer = card.explore()
    human = explorer.view(TOPIC)
    selected = explorer.access.select(TOPIC)
    assert human.result_ref == selected.result_ref
    assert explorer.answer("publications").result_ref == human.result_ref
    assert human.native_payload == expected
    assert selected.count == len(human.items()) == len(expected["publications"]) == 8
    assert [
        machine_value(explorer, row, "publication_ref") for row in frames(selected)
    ] == [row["publication_ref"] for row in expected["publications"]]
    assert sum(row["measurements"] for row in expected["publications"]) == 493
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "query",
    [
        {"options": {"publication_ref": "pubemd:40832834"}},
        {"options": {"limit": 1}},
        {"fields": ["year", "year"]},
        {"fields": ["unknown_column"]},
        {"where": {"year": 2025}},
        {"where": {"measurement_count": False}},
        {"where": {"measurement_count": {"value": 1, "unit": "nanomolar"}}},
        {"where": {"unknown_column": "x"}},
        {"order_by": {"column": "year", "descending": 1}},
        {"item_refs": ["XI_" + "0" * 64]},
    ],
)
def test_invalid_projection_options_operands_and_membership_refuse_before_work(
    card, monkeypatch, query
):
    monkeypatch.setattr(Card, "literature", forbidden)
    monkeypatch.setattr(Card, "explain_literature", forbidden)
    with pytest.raises(ArgumentError):
        card.access().select(TOPIC, skip_digestion=True, **query)


def test_projection_filter_and_exact_membership_keep_whole_native_scope(card):
    explorer = card.explore()
    view = explorer.view(TOPIC)
    original = publication(view, BTS_PAPER)
    selected = explorer.access.select(
        TOPIC,
        fields=["publication_ref", "measurement_count"],
        where={"publication_ref": BTS_PAPER},
        item_refs=[original.item_ref],
        order_by={"column": "publication_ref"},
    )
    row = frames(selected)[0]
    assert set(row["cells"]) == {"publication_ref", "measurement_count"}
    assert row["item_ref"] == original.item_ref and row["support"]
    filtered = view.filter("publication_ref", equals=BTS_PAPER)
    assert selected.result_ref == filtered.result_ref == view.result_ref
    assert [item.item_ref for item in filtered.items()] == [row["item_ref"]]
    assert filtered.native_payload == view.native_payload
    empty = explorer.access.select(
        TOPIC, fields=[], where={"publication_ref": "pubmed:999999999"}
    )
    assert empty.count == 0 and empty.result_ref == view.result_ref
    assert empty.page()["outcome"] == explorer.access.select(TOPIC).page()["outcome"]


def test_bounded_pages_have_stable_order_and_selection_owned_cursors(card):
    explorer = card.explore()
    selected = explorer.access.select(TOPIC, fields=["publication_ref"])
    rows = frames(selected, limit=2, max_bytes=8192)
    assert len(rows) == len({row["item_ref"] for row in rows}) == selected.count
    assert any(not row["value_included"] for row in rows)
    assert [row["item_ref"] for row in rows] == [
        item.item_ref for item in explorer.view(TOPIC).items()
    ]
    assert [machine_value(explorer, row, "publication_ref") for row in rows] == [
        item.cells["publication_ref"].value for item in explorer.view(TOPIC).items()
    ]
    cursor = selected.page(limit=1)["page"]["next_cursor"]
    assert cursor is not None
    with pytest.raises(ArgumentError):
        explorer.access.select(TOPIC, fields=[]).page(cursor=cursor)


def test_text_years_and_numeric_counts_sort_without_losing_nulls(public_originals):
    card = restored(public_originals, "bare")
    native = card.literature()["publications"]
    explorer = card.explore()
    view = explorer.view(TOPIC).sort("year")
    expected = sorted(native, key=lambda row: (row["year"] is None, row["year"] or ""))
    assert [item.cells["publication_ref"].value for item in view.items()] == [
        row["publication_ref"] for row in expected
    ]
    assert any(row["year"] is None for row in native)
    assert all(row["year"] is None or isinstance(row["year"], str) for row in native)
    machine = explorer.access.select(TOPIC, order_by={"column": "year"})
    assert [row["item_ref"] for row in frames(machine)] == [
        item.item_ref for item in view.items()
    ]
    counts = explorer.view(TOPIC).sort("support_count", descending=True)
    values = [item.cells["support_count"].value for item in counts.items()]
    assert all(type(value) is int for value in values)
    assert values == sorted(values, reverse=True)


def test_titles_and_source_text_are_escaped_in_the_visible_focused_html():
    card, ref = synthetic_card(), "pubmed:999000004"
    title = "<script>alert('α & β')</script>"
    add_publication(card, ref, title=title)
    view = card.explore().view(TOPIC, options={"publication_ref": ref})
    html = view._repr_html_()
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "α &amp; β" in html
    assert title in str(view)
    assert view.native_payload["publication"]["title"] == title


def test_missing_publication_is_empty_in_this_card_with_exact_native_reason(card):
    ref = "pubmed:999999999"
    expected = serialized_native(card.explain_literature(ref))
    explorer = card.explore()
    options = {"publication_ref": ref}
    view = explorer.view(TOPIC, options=options)
    selected = explorer.access.select(TOPIC, options=options)
    outcome = selected.page()["outcome"]
    assert not view.items() and view.native_payload == expected
    assert expected["status"] == "not_on_card"
    assert expected["reason"] == "no_stored_publication_link"
    assert view.outcome["status"] == outcome["status"] == "empty"
    assert outcome["native_status"] == "not_on_card"
    assert outcome["native_reason"] == expected["reason"]
    assert selected.count == 0


def test_literature_context_preserves_measurement_quantities_without_reclassification(
    card,
):
    expected = serialized_native(card.explain_literature(BTS_PAPER))
    view = card.explore().view(TOPIC, options={"publication_ref": BTS_PAPER})
    assert view.native_payload == expected and len(expected["links"]) == 9
    activity = next(
        row["relationship"]
        for row in view.native_payload["links"]
        if row["relationship"]["qualifiers"].get("activity_id") == 24815542
    )
    measurement = activity["qualifiers"]["measurement"]
    assert measurement["type"] == "IC50" and measurement["units"] == "nM"
    assert measurement["value"] == 33000
    assert measurement["normalized"] == {"value": 33000.0, "unit": "nanomolar"}
    assert view.items()[0].cells["measurement_count"].value == 9


def test_pinless_card_refuses_native_readers_and_keeps_explicit_prerequisite(
    monkeypatch,
):
    monkeypatch.setattr(Card, "literature", forbidden)
    monkeypatch.setattr(Card, "explain_literature", forbidden)
    card = Card(meta={"entity_type": "protein"})
    view = card.explore().view(TOPIC)
    assert not view.items() and view.outcome["status"] == "missing_prerequisite"


def test_live_literature_advertises_independent_saving_without_changing_wire(card):
    explorer = card.explore()
    view = explorer.view(TOPIC, options={"publication_ref": BTS_PAPER})
    selected = explorer.access.select(TOPIC, options={"publication_ref": BTS_PAPER})
    assert view.capabilities["save"] is True
    assert selected.capabilities["save"] is True
    assert view.items()[0].open().capabilities["save"] is True
    descriptor_row = next(
        row for row in frames(explorer.access.catalog("topics")) if row["key"] == TOPIC
    )
    descriptor = explorer.inspect(locator=descriptor_row["location"]).native_payload
    assert descriptor["save"] is True and "save_reason" not in descriptor
    assert "save" not in selected._scientific.wire["schema"]
    assert "save_reason" not in selected._scientific.wire["schema"]


def test_focus_and_machine_explain_keep_all_459_original_links(card):
    expected = serialized_native(card.explain_literature(BENZ_PAPER))
    explorer = card.explore()
    overview = explorer.view(TOPIC)
    item = publication(overview, BENZ_PAPER)
    detail = item.open()
    selected = explorer.access.select(TOPIC, options={"publication_ref": BENZ_PAPER})
    assert detail.back() is overview
    assert (
        detail.native_payload == expected and detail.result_ref == selected.result_ref
    )
    assert len(detail.native_payload["links"]) == 459
    assert item.cells["measurement_count"].value == 459
    assert item.cells["relationship_count"].value == 459
    focused_row = frames(selected)[0]
    assert detail.items()[0].item_ref == focused_row["item_ref"]
    assert explained_native(explorer, focused_row["item_ref"]) == expected
    assert item.explain().native_payload == expected


@pytest.mark.parametrize("first", ["human", "agent"])
def test_exact_requests_share_detached_originals_and_eager_explanations(
    card, monkeypatch, first
):
    expected = serialized_native(card.literature())
    native, calls = Card.explain_literature, []

    def counted(captured, ref, *args, **kwargs):
        calls.append((captured, ref))
        return native(captured, ref, *args, **kwargs)

    monkeypatch.setattr(Card, "explain_literature", counted)
    explorer = card.explore()
    card.relationship_store.store.clear()
    if first == "human":
        explorer.view(TOPIC)
    else:
        explorer.access.select(TOPIC)
    human = explorer.view(TOPIC, options={"publication_ref": None})
    selected = explorer.access.select(TOPIC)
    assert human.native_payload == expected and human.result_ref == selected.result_ref
    assert {ref for _, ref in calls} == {
        row["publication_ref"] for row in expected["publications"]
    }
    assert len(calls) == len(expected["publications"])
    assert all(captured is not card for captured, _ in calls)
    returned = human.native_payload
    returned["publications"].clear()
    assert human.native_payload == expected
    monkeypatch.setattr(Card, "explain_literature", forbidden)
    for item in human.items():
        ref = item.cells["publication_ref"].value
        assert item.open().native_payload["publication_ref"] == ref
        assert explained_native(explorer, item.item_ref)["publication_ref"] == ref
    assert explorer.access.select(TOPIC).result_ref == selected.result_ref


def test_located_mentions_keep_both_support_legs_original_locations_and_back(
    public_originals,
):
    card = restored(public_originals, "located")
    before = card.to_dict()
    expected = serialized_native(card.explain_literature(LOCATED_PAPER))
    explorer = card.explore()
    focused = explorer.view(TOPIC, options={"publication_ref": LOCATED_PAPER})
    item = focused.items()[0]
    assert item.open().native_payload == expected
    assert {row["relationship"]["predicate"] for row in expected["links"]} == {
        "mentioned_in",
        "structure_mentioned_in",
    }
    structural = next(
        row
        for row in expected["links"]
        if row["relationship"]["predicate"] == "structure_mentioned_in"
    )
    context = structural["structure_contexts"][0]
    assert context["context"]["scope"] == "entry_association"
    assert context["relationships"][0]["relationship"]["object_ref"] == "pdb:2JK2"
    assert len(expected["unlinked_pdb_mentions"]) == 3
    assert {row["structure_ref"] for row in expected["unlinked_pdb_mentions"]} == {
        "pdb:7QON"
    }
    links = item.related()
    source = role(links, "source").open()
    assert source.native_payload == card.source_assertion_store.get(
        source.native_payload["id"]
    )
    assert source.back() is links
    relationship = role(links, "original_relationship").open()
    assert relationship.native_payload == card.relationship_store.get(
        relationship.native_payload["id"]
    )
    assert relationship.back() is links
    assert source.request == relationship.request == focused.request
    assert card.to_dict() == before


@pytest.mark.parametrize("missing", ["assertion", "relationship"])
def test_missing_original_structural_support_stays_partial(public_originals, missing):
    data = deepcopy(public_originals["located"])
    link = next(
        row
        for row in data["relationship_store"]
        if row["predicate"] == "structure_mentioned_in"
    )
    context = link["qualifiers"]["structure_context"]
    key = "source_assertion_store" if missing == "assertion" else "relationship_store"
    identifier = context[
        "source_assertion_ids" if missing == "assertion" else "relationship_ids"
    ][0]
    data[key] = [row for row in data[key] if row["id"] != identifier]
    data["quantities"] = seal(data)
    card = Card.from_dict(data)
    expected = serialized_native(card.explain_literature(LOCATED_PAPER))
    explorer = card.explore()
    options = {"publication_ref": LOCATED_PAPER}
    view = explorer.view(TOPIC, options=options)
    outcome = explorer.access.select(TOPIC, options=options).page()["outcome"]
    assert expected["status"] == view.items()[0].cells["state"].value == "partial"
    assert expected["reason"] == "missing_stored_support"
    assert view.outcome["status"] == outcome["native_status"] == "partial"
    assert outcome["native_reason"] == expected["reason"]
    assert view.native_payload == expected
    assert view.items()[0].explain().native_payload == expected
    links = view.items()[0].related()
    unavailable = next(
        item for item in links.items() if item.cells["target_ref"].value == identifier
    )
    assert unavailable.cells["availability"].value == "missing_prerequisite"
    target = unavailable.open()
    assert target.outcome["status"] == "missing_prerequisite"
    assert target.back() is links


@pytest.mark.parametrize(
    "case,state",
    [
        ("bare", "not_queried"),
        ("empty", "not_stated"),
        ("failed", "unavailable"),
        ("mixed", "partial"),
    ],
)
def test_source_query_gaps_are_separate_from_retained_publications(
    public_originals, case, state
):
    card = restored(public_originals, case)
    expected = card.knowledge_state()
    explorer = card.explore()
    view = explorer.view(TOPIC)
    selected = explorer.access.select(TOPIC)
    coverage = explorer.inspect(
        locator=selected.page()["coverage"]["location"]
    ).native_payload
    assert coverage["rows"] == serialized_native(expected["rows"])
    assert coverage["rule"] == expected["rule"]
    assert coverage["quality_source_original"] == {
        key: card.quality[key]
        for key in ("enrichments", "literature_extractions", "curation")
        if key in card.quality
    }
    rows = [
        row
        for row in coverage["rows"]
        if row["source"] == "Europe PMC"
        and row["area"]
        in ("relationships.mentioned_in", "relationships.structure_mentioned_in")
    ]
    assert len(rows) == 2 and {row["state"] for row in rows} == {state}
    assert len(view.items()) == selected.count >= 48
    assert view.native_payload == serialized_native(card.literature())
    assert view.outcome["status"] not in ("empty", "missing_prerequisite")


@pytest.mark.parametrize("nature", ["molecule", "disease"])
def test_shared_topic_and_question_admit_other_public_card_natures(
    public_originals, nature
):
    card = restored(public_originals, nature)
    assert card.literature() == {"publications": [], "unresolved_eco": []}
    empty = card.explore()
    assert empty.view(TOPIC).native_payload == card.literature()
    assert empty.answer("publications").result_ref == empty.view(TOPIC).result_ref
    # A declared synthetic association tests shared dispatch, not source acquisition.
    ref = "pubmed:999000001"
    add_publication(card, ref, year="2025")
    before = card.to_dict()
    explorer = card.explore()
    view = explorer.answer("publications")
    assert view.native_payload == serialized_native(card.literature())
    assert view.items()[0].cells["publication_ref"].value == ref
    assert view.items()[0].open().native_payload == serialized_native(
        card.explain_literature(ref)
    )
    assert explorer.access.select(TOPIC).result_ref == view.result_ref
    assert card.to_dict() == before


def test_bibliographic_identity_uses_exact_references_not_shared_titles():
    card = synthetic_card()
    refs = ("pubmed:999000002", "doi:10.0000/synthetic-literature-control")
    for ref in refs:
        add_publication(card, ref, title="nanomolar", year="2025")
    explorer = card.explore()
    view = explorer.view(TOPIC)
    assert len(view.items()) == 2
    assert {item.cells["publication_ref"].value for item in view.items()} == set(refs)
    assert all(item.cells["title"].value == "nanomolar" for item in view.items())
    assert len({item.item_ref for item in view.items()}) == 2
    for ref in refs:
        selected = explorer.access.select(TOPIC, options={"publication_ref": ref})
        assert selected.count == 1
        assert publication(view, ref).open().native_payload == serialized_native(
            card.explain_literature(ref)
        )


def test_public_false_open_access_is_a_retained_boolean(public_originals):
    card = restored(public_originals, "search")
    ref = "pubmed:39044810"
    expected = serialized_native(card.explain_literature(ref))
    view = card.explore().view(TOPIC, options={"publication_ref": ref})
    assert any(
        row["open_access"] is False for row in expected["publication"]["mentions"]
    )
    assert view.native_payload == expected
    assert (
        view.items()[0]
        .open()
        .native_payload["publication"]["mentions"][0]["open_access"]
        is False
    )


def test_missing_title_is_typed_unknown_and_known_zero_count_stays_zero(
    public_originals,
):
    card = restored(public_originals, "bare")
    explorer = card.explore()
    view = explorer.view(TOPIC, options={"publication_ref": "pubmed:16502470"})
    item = view.items()[0]
    assert item.cells["title"].value is None and item.cells["title"].state == "unknown"
    assert type(item.cells["measurement_count"].value) is int
    assert item.cells["measurement_count"].value == 0
    selected = explorer.access.select(
        TOPIC, options={"publication_ref": "pubmed:16502470"}, where={"title": None}
    )
    assert selected.count == len(view.filter("title", equals=None).items()) == 1


def test_false_zero_and_null_support_values_remain_typed_and_original():
    card, ref, originals = synthetic_card(), "pubmed:999000003", []
    for index, value in enumerate((False, 0, None)):
        source = make_source_assertion(
            "annotations.synthetic_control",
            {"value": value},
            "Synthetic literature control",
            f"false-zero-null-{index}",
            "2026-11-07",
            subject_ref="uniprot:P60174",
        )
        source["source_metadata"] = {
            "eco": [
                {"source": "PubMed", "id": ref.split(":", 1)[1], "code": "synthetic"}
            ]
        }
        card.source_assertion_store.add(source)
        originals.append(source)
    before = card.to_dict()
    expected = serialized_native(card.explain_literature(ref))
    values = {
        row["source_assertion_id"]: row["value"]
        for row in expected["publication"]["supports"]
    }
    view = card.explore().view(TOPIC, options={"publication_ref": ref})
    assert view.native_payload == expected
    links = view.items()[0].related()
    for source, value in zip(originals, (False, 0, None)):
        assert type(values[source["id"]]) is type(value)
        assert values[source["id"]] == value
        link = next(
            item
            for item in links.items()
            if item.cells["role"].value == "source"
            and item.cells["target_ref"].value == source["id"]
        )
        actual = link.open().native_payload["asserted_value"]["value"]
        assert type(actual) is type(value) and actual == value
    assert card.to_dict() == before
