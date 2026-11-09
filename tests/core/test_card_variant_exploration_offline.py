"""Native variant/isoform tissue context, human/agent parity and exact source scope."""

import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.core.tissue_usage import EXONS, ISOFORMS, REGIONS, TRANSCRIPTS, VARIANTS
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http
from sabueso.tools.db.gnomad import FixtureGnomADClient
from sabueso.tools.db.gtex import FixtureGTExClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"
if not (DATA / "P60174.json").is_file():
    DATA = Path.cwd() / "temp_data"


def forbidden(*args, **kwargs):
    pytest.fail("Captured variant exploration must not acquire source data")


@pytest.fixture(scope="module")
def originals():
    with pytest.MonkeyPatch.context() as guard:
        guard.setattr(socket.socket, "connect", forbidden)
        guard.setattr(socket, "create_connection", forbidden)
        card = sabueso.resolve(
            "P60174",
            resolver=EntityResolver(FixtureUniProtClient(DATA)),
            gnomad={},
            exon_usage=True,
            gtex=True,
            gnomad_client=FixtureGnomADClient(DATA),
            gtex_client=FixtureGTExClient(DATA),
        )[0]
    return card.to_dict()


@pytest.fixture(autouse=True)
def offline(originals, monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(_http, "_urlopen", forbidden)
    for client in (FixtureUniProtClient, FixtureGnomADClient, FixtureGTExClient):
        monkeypatch.setattr(client, "__init__", forbidden)


def public(originals):
    return Card.from_dict(deepcopy(originals))


def frames(selection, **options):
    cursor, result, seen = None, [], set()
    while True:
        page = selection.page(cursor=cursor, **options)
        assert len(canonical_json(page).encode("utf-8")) <= options.get(
            "max_bytes", 65536
        )
        assert page["page"]["blocked"] is None
        result.extend(page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            return result
        assert cursor not in seen
        seen.add(cursor)


def put(card, path, values):
    refs = []
    for index, value in enumerate(values):
        assertion = make_source_assertion(
            path,
            value,
            "synthetic",
            str(index),
            "synthetic control",
            subject_ref="uniprot:P60174",
        )
        refs.append(card.source_assertion_store.add(assertion))
    card.set(path, values, refs)
    return refs


def synthetic():
    card = Card(
        meta={"card_id": "sabueso:protein:uniprot:P60174", "entity_type": "protein"}
    )
    put(
        card,
        VARIANTS,
        [
            {
                "variant_id": "12-15-A-G",
                "assembly": "GRCh38",
                "transcript": "T1.2",
                "location": {"start": 999, "end": 999},
            }
        ],
    )
    put(
        card,
        ISOFORMS,
        [{"isoform_id": "SYN-1", "name": "1"}, {"isoform_id": "SYN-2", "name": "2"}],
    )
    put(
        card,
        TRANSCRIPTS,
        [
            {"isoform": "SYN-1", "transcript": "T1.2"},
            {"isoform": "SYN-2", "transcript": "T2.1"},
        ],
    )
    put(
        card,
        EXONS,
        [
            {
                "isoform": "SYN-1",
                "transcript": "T1",
                "transcript_version": "2",
                "assembly": "GRCh38",
                "chromosome": "12",
                "cds": [[10, 19]],
            },
            {
                "isoform": "SYN-2",
                "transcript": "T2",
                "transcript_version": "1",
                "assembly": "GRCh38",
                "chromosome": "12",
                "cds": [[20, 29]],
            },
        ],
    )
    put(
        card,
        REGIONS,
        [
            {
                "assembly": "GRCh38",
                "chromosome": "12",
                "start": 10,
                "end": 29,
                "tissues": [
                    {"tissue": "liver", "value": 0.0},
                    {"tissue": "brain", "value": None},
                ],
            }
        ],
    )
    return card


@pytest.mark.parametrize("mode,count", [("variants", 15), ("isoforms", 3)])
def test_public_human_and_agent_share_unchanged_native_context(originals, mode, count):
    card = public(originals)
    before = card.to_dict()
    native = getattr(
        card, "variant_tissue_usage" if mode == "variants" else "isoform_tissue_usage"
    )()
    explorer = card.explore()
    view = explorer.view("variants", options={"mode": mode})
    machine = explorer.access.select("variants", options={"mode": mode})
    answer = explorer.answer(
        "variant_tissue_context" if mode == "variants" else "isoform_tissue_context"
    )
    assert view.native_payload == answer.native_payload == native
    assert view.result_ref == machine.result_ref == answer.result_ref
    assert len(view.items()) == machine.count == count
    assert [item.open().native_payload for item in view.items()] == native["items"]
    assert len(frames(machine)) == count
    assert card.to_dict() == before
    assert "variants" in explorer.capabilities["scientific_topics"]
    assert "variant_tissue_context" in explorer.capabilities["question_keys"]
    assert "isoform_tissue_context" in explorer.capabilities["question_keys"]
    assert answer.request["options"] == {"mode": mode, "threshold": 0.1}
    assert "zero expression" in repr(view)
    assert "tissue" in view._repr_html_().lower()


@pytest.mark.parametrize("mode", ["variants", "isoforms"])
def test_native_once_per_effective_request_and_captured_revision(
    originals, monkeypatch, mode
):
    from sabueso.core import scoped_tissue_usage

    name = "variant_view" if mode == "variants" else "isoform_view"
    native = getattr(scoped_tissue_usage, name)
    calls = []

    def observed(*args, **kwargs):
        calls.append(True)
        return native(*args, **kwargs)

    monkeypatch.setattr(scoped_tissue_usage, name, observed)
    card = public(originals)
    explorer = card.explore()
    view = explorer.view("variants", options={"mode": mode})
    explorer.access.select("variants", fields=["label"], options={"mode": mode})
    explorer.answer(
        "variant_tissue_context" if mode == "variants" else "isoform_tissue_context"
    )
    view.items()[0].open()
    view.items()[0].explain()
    view.items()[0].related()
    assert len(calls) == 1
    card.set("names.canonical_name", "changed caller state", [])
    assert (
        explorer.view("variants", options={"mode": mode}).result_ref == view.result_ref
    )
    explorer.view("variants", options={"mode": mode, "threshold": 0.2})
    assert len(calls) == 2


@pytest.mark.parametrize("mode", ["variants", "isoforms"])
def test_every_original_input_and_source_link_returns_to_exact_question(
    originals, mode
):
    explorer = public(originals).explore()
    question = explorer.answer(
        "variant_tissue_context" if mode == "variants" else "isoform_tissue_context",
        options={"threshold": 0.2},
    )
    selected = question.sort("label", descending=True).filter(
        "label", equals=question.items()[0].label
    )
    item = selected.items()[0]
    explanation = item.explain()
    assert explanation.back() is selected and explanation.request == question.request
    assert (
        explanation.native_payload["native_explanation"]["item"]
        == item.open().native_payload
    )
    links = item.related()
    assert links.back() is selected and links.request == question.request
    roles = set()
    for link in links.items():
        roles.add(link._entry.value["role"])
        opened = link.open()
        assert opened.back() is links and opened.request == question.request
        location = link._entry.value["candidates"][0]["location"]
        assert opened.native_payload == explorer.access._resolve(location)[0]
    assert {
        "source",
        "original_input",
        "original_explanation",
        "original_quality",
        "whole_card_context",
    } <= roles


@pytest.mark.parametrize("mode", ["variants", "isoforms"])
def test_machine_projection_membership_order_and_human_cells_agree(originals, mode):
    explorer = public(originals).explore()
    human = explorer.view("variants", options={"mode": mode}).sort(
        "label", descending=True
    )
    members = [item.item_ref for item in list(human.items())[:2]]
    selected = explorer.access.select(
        "variants",
        options={"mode": mode},
        fields=["label", "pext_basis", "support_state"],
        item_refs=members,
        order_by={"column": "label", "descending": True},
    )
    output = frames(selected, limit=1)
    assert [row["item_ref"] for row in output] == members
    for row in output:
        assert set(row["cells"]) == {"label", "pext_basis", "support_state"}
        assert row["adapter"] == "variant_tissue_context_exploration@1"
        assert row["interpretation"]["native_rule"] == human.native_payload["rule"]
        for column, cell in row["cells"].items():
            assert cell["value"] == human.item(row["item_ref"]).cells[column].value
        assert explorer.access.explain(row["item_ref"]).count > 0


def test_zero_missing_tissues_and_genomic_not_protein_positions_are_distinct():
    view = synthetic().explore().view("variants")
    row = view.items()[0]
    assert row.cells["genomic_position"].value == 15
    assert row.open().native_payload["location"]["start"] == 999
    pext = row.open().native_payload["pext"]
    assert pext["by_tissue"]["liver"] == 0.0
    assert pext["by_tissue"]["brain"] is None
    assert pext["coverage_by_tissue"]["brain"]["complete"] is False
    assert row.cells["tissue_count"].value == 1


@pytest.mark.parametrize("mode", ["variants", "isoforms"])
@pytest.mark.parametrize(
    "defect",
    [
        "foreign_assembly",
        "foreign_chromosome",
        "missing_assembly",
        "conflicting_tissue",
    ],
)
def test_scoped_native_uncertainties_are_preserved(mode, defect):
    card = synthetic()
    rows = deepcopy(card.get(REGIONS)["value"])
    if defect == "foreign_assembly":
        rows[0]["assembly"] = "GRCh37"
    elif defect == "foreign_chromosome":
        rows[0]["chromosome"] = "1"
    elif defect == "missing_assembly":
        rows[0].pop("assembly")
    else:
        rows.append(
            {**deepcopy(rows[0]), "tissues": [{"tissue": "liver", "value": 0.8}]}
        )
    put(card, REGIONS, rows)
    native = getattr(
        card, "variant_tissue_usage" if mode == "variants" else "isoform_tissue_usage"
    )()
    view = card.explore().view("variants", options={"mode": mode})
    assert view.native_payload == native
    if defect != "conflicting_tissue":
        assert all(not row["pext"].get("by_tissue") for row in native["items"])
    else:
        assert all(row["pext"]["by_tissue"]["liver"] is None for row in native["items"])
    assert view.outcome["status"] == "partial"
    assert view.coverage["gaps"]


@pytest.mark.parametrize("defect", ["subject", "field", "missing"])
def test_misbound_and_missing_source_membership_stays_inspectable(defect):
    card = synthetic()
    ref = card.get(VARIANTS)["source_assertion_ids"][0]
    if defect == "missing":
        card.source_assertion_store.store.pop(ref)
    else:
        card.source_assertion_store.get(ref)[
            "subject_ref" if defect == "subject" else "field_path"
        ] = "foreign"
    view = card.explore().answer("variant_tissue_context")
    item = view.items()[0]
    assert item.cells["support_state"].value == "partial"
    assert view.outcome["status"] == "partial"
    assert any(
        r["id"] == ref and r["state"] != "present"
        for r in item.support[0]["source_assertions"]
    )
    links = item.related()
    matching = [
        r
        for r in links.items()
        if r._entry.value.get("target_ref") == ref or ref in r.label
    ]
    assert matching
    if defect == "missing":
        assert matching[0].open().outcome["status"] == "missing_prerequisite"


def test_repeated_identical_variant_occurrences_never_merge():
    card = synthetic()
    value = card.get(VARIANTS)["value"][0]
    put(card, VARIANTS, [value, deepcopy(value)])
    view = card.explore().view("variants")
    assert len(view.items()) == 2
    first, second = list(view.items())
    assert first.item_ref != second.item_ref
    assert first.open().native_payload == second.open().native_payload


@pytest.mark.parametrize(
    "kwargs",
    [
        {"options": {"mode": "other"}},
        {"options": {"threshold": True}},
        {"options": {"threshold": float("nan")}},
        {"options": {"threshold": -0.1}},
        {"options": {"fetch": True}},
        {"fields": ["label", "label"]},
        {"where": {"own_coding_bases": 1.0}},
        {"where": {"own_bases_complete": 1}},
        {"where": {"genomic_position": True}},
        {"where": {"variant_ref": 1}},
        {"where": {"other": None}},
        {"order_by": {"column": "label", "unit": "nm"}},
    ],
)
def test_invalid_requests_refuse_before_native_work(originals, monkeypatch, kwargs):
    from sabueso.core import comparative_explanation

    explorer = public(originals).explore()
    monkeypatch.setattr(
        comparative_explanation, "explain_variant_tissue_usage", forbidden
    )
    monkeypatch.setattr(
        comparative_explanation, "explain_isoform_tissue_usage", forbidden
    )
    with pytest.raises(ArgumentError):
        explorer.access.select("variants", **kwargs)


def test_other_modes_foreign_members_and_cursors_are_refused(originals):
    explorer = public(originals).explore()
    variants = explorer.access.select("variants")
    isoforms = explorer.access.select("variants", options={"mode": "isoforms"})
    first = frames(variants)[0]
    with pytest.raises(ArgumentError):
        explorer.access.select(
            "variants", options={"mode": "isoforms"}, item_refs=[first["item_ref"]]
        )
    cursor = variants.page(limit=1)["page"]["next_cursor"]
    with pytest.raises(ArgumentError):
        isoforms.page(cursor=cursor)
    with pytest.raises(ArgumentError):
        explorer.answer("isoform_tissue_context", options={"mode": "variants"})


@pytest.mark.parametrize("mode", ["variants", "isoforms"])
def test_live_human_machine_and_detail_saving_keep_original_context(
    originals, tmp_path, mode
):
    explorer = public(originals).explore()
    view = explorer.answer(
        "variant_tissue_context" if mode == "variants" else "isoform_tissue_context"
    )
    selection = explorer.access.select("variants", options={"mode": mode})
    assert view.capabilities["save"]
    for index, target in enumerate(
        [
            view,
            view.items()[0].open(),
            view.items()[0].explain(),
            view.items()[0].related(),
            selection,
        ]
    ):
        path = tmp_path / f"retained-{index}.json.gz"
        target.save(path, compression="gzip")
        saved = sabueso.read_exploration(path)
        assert (
            saved.validation["verifier"]
            == "variant_tissue_context_exploration_binding@1"
        )
        assert canonical_json(saved.native_payload) == canonical_json(
            view.native_payload if target is selection else target.native_payload
        )
        assert (
            saved.explorer.access.select(
                "variants", options={"mode": mode}
            ).selection_ref
            == selection.selection_ref
        )


def test_bare_and_nonprotein_profiles_do_not_invent_rows():
    card = Card(
        meta={"card_id": "sabueso:protein:uniprot:P60174", "entity_type": "protein"}
    )
    view = card.explore().view("variants")
    assert len(view.items()) == 0 and view.outcome["status"] == "missing_prerequisite"
    other = Card(
        meta={
            "card_id": "sabueso:small_molecule:CHEMBL1",
            "entity_type": "small_molecule",
        }
    )
    assert "variants" not in other.explore().capabilities["scientific_topics"]
    with pytest.raises(ArgumentError):
        other.access().select("variants")


def test_source_conflicts_and_unselected_alternatives_remain_explicit():
    card = synthetic()
    native = card.variant_tissue_usage()
    card.quality["conflicts"] = [
        {
            "field": VARIANTS,
            "values": ["selected", "alternative"],
            "source_assertion_ids": card.get(VARIANTS)["source_assertion_ids"],
        }
    ]
    card.quality["alternatives"] = [
        {"field": VARIANTS, "value": "retained alternative", "source_assertion_ids": []}
    ]
    view = card.explore().view("variants")
    assert view.native_payload == native
    assert view.outcome["status"] == "partial"
    assert view.coverage["field_conflicts"][0]["conflicts"] == card.quality["conflicts"]
    row = frames(view.explorer.access.select("variants"))[0]
    assert row["interpretation"]["source_conflicts"] == view.coverage["field_conflicts"]
    assert (
        row["interpretation"]["source_alternatives"][0]["alternatives"]
        == card.quality["alternatives"]
    )


@pytest.mark.parametrize(
    "defect", ["missing_cds", "foreign_transcript", "foreign_version"]
)
def test_isoform_transcript_and_cds_gaps_never_imply_unique_tissue_expression(defect):
    card = synthetic()
    exons = deepcopy(card.get(EXONS)["value"])
    if defect == "missing_cds":
        exons = exons[:1]
    elif defect == "foreign_transcript":
        exons[1]["transcript"] = "FOREIGN"
    else:
        exons[1]["transcript_version"] = "999"
    put(card, EXONS, exons)
    native = card.isoform_tissue_usage()
    view = card.explore().answer("isoform_tissue_context")
    assert view.native_payload == native
    assert not native["variable_regions_complete"]
    assert view.outcome["status"] == "partial" and view.coverage["gaps"]
    assert not view.items()[0].cells["own_bases_complete"].value


def test_budget_deferral_keeps_values_and_scientific_interpretation_atomic():
    card = synthetic()
    value = deepcopy(card.get(VARIANTS)["value"][0])
    value["variant_id"] = "12-15-A-" + "G" * 20000
    put(card, VARIANTS, [value])
    explorer = card.explore()
    selected = explorer.access.select("variants")
    (row,) = frames(selected, limit=1, max_bytes=16384)
    assert row["value_included"] is False and row["inspection_required"] is True
    assert "interpretation" not in row and "label" not in row
    assert all(
        not cell["value_included"] and "value" not in cell
        for cell in row["cells"].values()
    )
    location = row["payload_location"]
    assert (
        explorer.inspect(locator=location).native_payload["variant_id"]
        == value["variant_id"]
    )
    assert explorer.access.explain(row["item_ref"]).count > 0


def test_source_text_is_escaped_in_bounded_html_and_complete_in_native_items():
    card = synthetic()
    value = deepcopy(card.get(VARIANTS)["value"][0])
    value["variant_id"] = "12-15-A-<script>alert(1)</script>"
    put(card, VARIANTS, [value])
    view = card.explore().view("variants")
    html = view._repr_html_()
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert view.items()[0].open().native_payload["variant_id"] == value["variant_id"]


@pytest.mark.parametrize("visited", [False, True])
def test_literal_saving_retains_only_observed_variant_context(
    originals, tmp_path, visited
):
    explorer = public(originals).explore()
    original = explorer.view("variants") if visited else None
    literal = explorer.inspect("names.canonical_name")
    path = tmp_path / "literal.json"
    literal.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == literal.native_payload
    assert ("variants" in saved.explorer.capabilities["scientific_topics"]) == visited
    assert ("variants" in saved.explorer._topics) == visited
    assert ("variant_tissue_context" in saved.explorer._questions) == visited
    if visited:
        assert saved.explorer.view("variants").native_payload == original.native_payload
        assert (
            saved.explorer.answer("variant_tissue_context").outcome["status"]
            == "not_saved"
        )
        assert (
            saved.explorer.access.select("variants").page()["outcome"]["status"]
            == "not_saved"
        )
