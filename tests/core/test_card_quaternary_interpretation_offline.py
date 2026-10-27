"""Human/agent quaternary interpretation shares native science and exact input scope."""

import importlib
import json
import socket
from copy import deepcopy

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion

TOPIC = "quaternary_interpretation"
SUBJECT = "uniprot:P52270"
FAMILY = "features_positional.family_site"


def forbidden(*a, **k):
    raise AssertionError("No source requests, repeated science or caller recapture")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def assertion(
    card, path, value, *, subject=SUBJECT, source="synthetic", record="SYNTHETIC"
):
    row = make_source_assertion(
        path, deepcopy(value), source, record, "synthetic", subject_ref=subject
    )
    if source == "UniProt":
        row["source_metadata"] = {"sequence_version": 7}
    card.source_assertion_store.add(row)
    return row["id"]


def field(card, path, value, source="UniProt"):
    refs = (
        [assertion(card, path, v, source=source, record="P52270") for v in value]
        if isinstance(value, list)
        else [assertion(card, path, value, source=source, record="P52270")]
    )
    card.set(path, value, refs)


def relation(card, predicate, obj, q, *, subject=SUBJECT, suffix=""):
    ref = assertion(
        card,
        "relationships." + predicate,
        {"subject_ref": subject, "object_ref": obj, "qualifiers": q},
        subject=subject,
    )
    row = make_relationship(subject, predicate, obj, deepcopy(q), [ref])
    if suffix:
        row["id"] += "_" + suffix
    card.relationship_store.add(row)
    return card.relationship_store.get(row["id"])


def sample(*, partner=SUBJECT, coverage=1.0, modifier=None, numbering="uniprot"):
    card = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:" + SUBJECT}
    )
    for path, value in [
        ("identifiers.uniprot", "P52270"),
        ("sequence.primary", "M" * 100),
        ("sequence.length", 100),
        ("annotations.subunit", ["Explicit synthetic homodimer"]),
    ]:
        field(card, path, value)
    span = {"start": 12, "end": 14}
    if modifier is not None:
        span["start_modifier"] = modifier
    value = {
        "description": "Synthetic dimer interface",
        "location": {
            "kind": "sequence",
            "sequence": {
                "sequence_id": "UniProt:P52270",
                "indexing": "1-based",
                "fragments": [span],
            },
        },
    }
    field(card, FAMILY, [value], "InterPro")
    q = {"chimeric_with": [], "assemblies": []}
    if coverage is not None:
        q["coverage"] = coverage
    relation(card, "has_structure", "pdb:SYNTHETIC", q)
    relation(
        card,
        "has_interface_with",
        partner,
        {
            "numbering": numbering,
            "structures": ["pdb:SYNTHETIC"],
            "residues": [{"start": 13, "end": 15}],
        },
    )
    return card


@pytest.mark.parametrize("first", ["human", "agent"])
def test_one_capture_and_one_native_evaluation_shared_by_both_entry_orders(
    monkeypatch, first
):
    card = sample()
    expected = card.oligomer()
    explorer = card.explore()
    calls = {"view": 0, "explanation": 0}
    for module_name, name, key in [
        ("oligomer", "oligomer_view", "view"),
        ("oligomer_explanation", "_explain_oligomer", "explanation"),
    ]:
        module = importlib.import_module("sabueso.core." + module_name)
        original = getattr(module, name)

        def spy(*a, _key=key, _original=original, **k):
            calls[_key] += 1
            return _original(*a, **k)

        monkeypatch.setattr(module, name, spy)
    monkeypatch.setattr(card, "to_dict", forbidden)
    card.relationships("has_interface_with")[0]["qualifiers"]["numbering"] = "author"
    if first == "agent":
        selection = explorer.access.select(TOPIC)
        human = explorer.answer(TOPIC)
    else:
        human = explorer.answer(TOPIC)
        selection = explorer.access.select(TOPIC)
    assert human.native_payload == expected
    assert human.result_ref == selection.result_ref == explorer.view(TOPIC).result_ref
    assert calls == {"view": 1, "explanation": 1}
    for item in human.items():
        assert item.open().native_payload == item._entry.value["item"]
        assert item.open().back() is human
        assert item.explain().native_payload["original_interpretation"]
        assert item.related().items()
        assert explorer.access.explain(item.item_ref).count
    assert calls == {"view": 1, "explanation": 1}
    assert "Source-declared self-interface" in str(human.table())
    assert "shared positions" in str(human.table())
    assert "not established" in str(human.table())
    assert "not a validated biological assembly" in str(human.summary())


@pytest.mark.parametrize("accession", ["P52270", "P60174"])
def test_public_current_source_journey_matches_every_native_finding(accession):
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
    from sabueso.tools.db.interpro import FixtureInterProClient
    from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient

    card, _ = sabueso.resolve_protein_card(
        accession,
        EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        structures=["1SUX"] if accession == "P52270" else ["1KLG"],
        interfaces=True,
        family_sites=True,
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        interpro_client=FixtureInterProClient("temp_data"),
    )
    before = card.to_dict()
    native = card.oligomer()
    explorer = card.explore()
    view = explorer.answer(TOPIC)
    assert view.native_payload == native
    assert len(view.items()) == len(native["interfaces"]) + len(native["agreement"])
    assert any(
        i.kind == "interface_classification" and i.cells["status"].value == "computed"
        for i in view.items()
    )
    assert view.filter("kind", equals="interface_family_comparison").rows()
    for item in view.items():
        assert item.open().native_payload in native["interfaces"] + native["agreement"]
        for source in item.support[0]["source_assertions"]:
            if source["state"] == "present":
                assert explorer.access._resolve(source["location"])[
                    0
                ] == card.source_assertion_store.get(source["id"])
    assert card.to_dict() == before


def test_all_original_declarations_and_pairs_remain_distinct():
    card = sample()
    original = card.relationships("has_interface_with")[0]
    relation(
        card, "has_interface_with", SUBJECT, original["qualifiers"], suffix="SECOND"
    )
    relation(
        card,
        "has_structure",
        "pdb:SYNTHETIC",
        {"coverage": 0.1, "chimeric_with": [], "assemblies": []},
        suffix="SECOND",
    )
    annotation = deepcopy(card.get(FAMILY)["value"][0])
    field(card, FAMILY, [annotation, annotation], "InterPro")
    view = card.explore().answer(TOPIC)
    assert len(view.items()) == 6
    assert len({item.item_ref for item in view.items()}) == 6
    assert {
        item.open().native_payload["family_site_index"]
        for item in view.filter("kind", equals="interface_family_comparison").items()
    } == {0, 1}
    for item in view.filter("kind", equals="interface_classification").items():
        links = item.related().filter("role", equals="structure_context")
        assert len(links.items()) == 2
        assert len({link.open().native_payload["id"] for link in links.items()}) == 2


@pytest.mark.parametrize("name", [None, True, 42])
def test_non_text_names_never_change_identity_or_break_textual_selection(name):
    card = sample()
    original = card.relationships("has_interface_with")[0]
    q = deepcopy(original["qualifiers"])
    q["partner_name"] = name
    card.relationship_store.store.pop(original["id"])
    relation(card, "has_interface_with", SUBJECT, q)
    explorer = card.explore()
    item = explorer.answer(TOPIC).items()[0]
    assert item.label == SUBJECT
    assert item.open().native_payload["partner_name"] == name
    selected = explorer.access.select(TOPIC, where={"label": SUBJECT})
    assert selected.count == 1


def test_partial_positive_pairs_do_not_hide_uncomputed_pair_members():
    card = sample()
    q = deepcopy(card.relationships("has_interface_with")[0]["qualifiers"])
    q["numbering"] = "author"
    relation(card, "has_interface_with", SUBJECT, q, suffix="UNCERTAIN")
    explorer = card.explore()
    view = explorer.answer(TOPIC)
    assert view.native_payload["agreement_state"]["status"] == "partial"
    pairs = view.filter("kind", equals="interface_family_comparison")
    assert {i.cells["status"].value for i in pairs.items()} == {
        "computed",
        "not_computed",
    }
    frames = pages(
        explorer.access.select(TOPIC, where={"kind": "interface_family_comparison"})
    )
    assert len(frames) == 2
    assert any(
        "interface_numbering_not_comparable" in frame["interpretation"]["reason_codes"]
        for frame in frames
    )


@pytest.mark.parametrize(
    "kind", ["numbering", "uncertain_family", "foreign", "missing_source", "coverage"]
)
def test_uncertain_foreign_and_missing_inputs_keep_native_scope_and_sources(kind):
    card = sample(
        partner="uniprot:P60174" if kind == "coverage" else SUBJECT,
        coverage=None if kind == "coverage" else 1,
        modifier="LESS_THAN" if kind == "uncertain_family" else None,
        numbering="author" if kind == "numbering" else "uniprot",
    )
    row = card.relationships("has_interface_with")[0]
    if kind == "foreign":
        card.relationship_store.store.pop(row["id"])
        relation(
            card,
            "has_interface_with",
            SUBJECT,
            row["qualifiers"],
            subject="uniprot:P60174",
        )
    missing = None
    if kind == "missing_source":
        missing = row["source_assertion_ids"][0]
        card.source_assertion_store.store.pop(missing)
    native = card.oligomer()
    explorer = card.explore()
    view = explorer.answer(TOPIC)
    assert view.native_payload == native
    assert any(
        item.cells["status"].value == "not_computed"
        or item.cells["coordinate_status"].value == "not_computed"
        for item in view.items()
    )
    if kind == "foreign":
        assert (
            len(view.items()) == 1
            and view.items()[0].open().native_payload["class"] == "undetermined"
        )
        frame = pages(explorer.access.select(TOPIC))[0]
        assert frame["subject_ref"] == "uniprot:P60174"
        assert frame["cells"]["partner_ref"]["value"] == SUBJECT
    if kind in ("numbering", "uncertain_family", "missing_source"):
        pair = view.filter("kind", equals="interface_family_comparison").items()[0]
        assert pair.open().native_payload["both"] is None
        assert "Position comparison not computed" in str(pair.open().table())
    if missing:
        assert any(
            s["id"] == missing and s["state"] == "not_retained"
            for i in view.items()
            for s in i.support[0]["source_assertions"]
        )
        links = view.items()[0].related()
        assert any(
            i.cells["availability"].value == "missing_prerequisite"
            for i in links.items()
        )


def test_original_source_and_family_navigation_never_changes_identity_or_inputs():
    card = sample()
    explorer = card.explore()
    human = explorer.answer(TOPIC)
    pair = human.filter("kind", equals="interface_family_comparison").items()[0]
    links = pair.related()
    selected_links = links.filter("role", equals="family_annotation")
    annotation = selected_links.items()[0]
    assert annotation.open().native_payload == card.get(FAMILY)["value"][0]
    assert annotation.open().back() is selected_links
    assert selected_links.back() is links
    for item in human.items():
        detail = item.explain()
        for key in (
            "reference_inputs_location",
            "source_request_context_location",
            "full_explanation_location",
        ):
            assert explorer.access.read(detail.native_payload[key]).count
    assert explorer.view("quaternary_structure").items()


def pages(selection, budget=8192):
    cursor = None
    out = []
    while True:
        page = selection.page(max_bytes=budget, cursor=cursor)
        assert len(canonical_json(page).encode("utf-8")) <= budget
        out.extend(page["items"])
        if page["page"]["complete"]:
            return out
        cursor = page["page"]["next_cursor"]
        assert cursor is not None


def test_compact_pages_have_complete_scope_source_membership_and_stable_shared_ids():
    explorer = sample().explore()
    view = explorer.answer(TOPIC)
    selection = explorer.access.select(TOPIC)
    frames = pages(selection)
    assert {frame["item_ref"] for frame in frames} == {
        item.item_ref for item in view.items()
    }
    for frame in frames:
        assert frame["value_included"]
        assert frame["subject_ref"] == SUBJECT
        assert frame["interpretation"]["rule_names"] == [
            *[rule["rule"] for rule in view.native_payload["rules"]],
            view.native_payload["canonical_reference"]["rule"],
        ]
        assert "revision_agreement" in frame["interpretation"]
        original = next(
            item for item in view.items() if item.item_ref == frame["item_ref"]
        )
        assert frame["support"]["source_assertions"] == [
            {"id": row["id"], "state": row["state"]}
            for row in original.support[0]["source_assertions"]
        ]
        for source in frame["support"]["source_assertions"]:
            location = deepcopy(frame["support"]["source_store_location"])
            location["segments"].append({"type": "Record", "value": source["id"]})
            assert explorer.access.read(location).count
        for column, cell in frame["cells"].items():
            assert cell["value"] == original.cells[column].value
            assert explorer.access._resolve(cell["value_location"])[0] == cell["value"]


def test_exact_selection_keeps_underlying_science_support_and_cursor_isolation():
    explorer = sample().explore()
    view = explorer.answer(TOPIC)
    pair = view.filter("kind", equals="interface_family_comparison").items()[0]
    selected = explorer.access.select(
        TOPIC,
        fields=["finding"],
        where={"kind": "interface_family_comparison"},
        item_refs=[pair.item_ref],
        order_by={"column": "label", "descending": True},
    )
    assert selected.count == 1 and selected.result_ref == view.result_ref
    frame = pages(selected)[0]
    assert frame["item_ref"] == pair.item_ref and list(frame["cells"]) == ["finding"]
    assert frame["support"]["source_assertions"] and frame["interpretation"]
    all_items = explorer.access.select(TOPIC).page(limit=1)
    with pytest.raises(ArgumentError):
        selected.page(cursor=all_items["page"]["next_cursor"])
    with pytest.raises(ArgumentError):
        explorer.access.select(
            TOPIC, item_refs=[explorer.view("quaternary_structure").items()[0].item_ref]
        )
    assert explorer.access.select(TOPIC, where={"status": "invented"}).count == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"where": {"status": True}},
        {"where": {"status": None}},
        {"where": {"unknown": "x"}},
        {"fields": ["status", "status"]},
        {"options": {"sequence_ref": SUBJECT}},
        {"order_by": {"column": "status", "unit": "nanomolar"}},
    ],
)
def test_invalid_display_requests_are_refused_before_calculation(monkeypatch, kwargs):
    explorer = sample().explore()
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.oligomer"), "oligomer_view", forbidden
    )
    with pytest.raises(ArgumentError):
        explorer.access.select(TOPIC, **kwargs)


def test_long_labels_escape_html_and_defer_values_scope_and_support_atomically():
    card = sample()
    annotation = deepcopy(card.get(FAMILY)["value"][0])
    annotation["description"] = "<script>alert('x')</script> interface " * 2000
    field(card, FAMILY, [annotation], "InterPro")
    explorer = card.explore()
    view = explorer.answer(TOPIC)
    rendered = view._repr_html_()
    assert "<script>" not in rendered and "&lt;script&gt;" in rendered
    frames = pages(explorer.access.select(TOPIC))
    deferred = next(
        frame for frame in frames if frame["kind"] == "interface_family_comparison"
    )
    assert not deferred["value_included"] and deferred["inspection_required"]
    assert "support" not in deferred and "interpretation" not in deferred
    assert all(
        not cell["value_included"] and "value" not in cell
        for cell in deferred["cells"].values()
    )
    assert explorer.access.read(deferred["interpretation_location"]).count
    assert explorer.access.read(deferred["support_location"]).count


def test_empty_other_natures_and_live_history_capabilities_are_explicit(
    tmp_path, monkeypatch
):
    card = sample()
    card.relationship_store.store.clear()
    empty = card.explore().answer(TOPIC)
    assert empty.outcome["status"] == "empty" and not empty.items()
    assert "not evidence" in empty.outcome["reason"]
    other = Card(
        meta={
            "entity_type": "small_molecule",
            "card_id": "sabueso:small_molecule:chembl:CHEMBL1",
        }
    )
    assert other.explore().view(TOPIC).outcome["status"] == "not_applicable"
    explorer = sample().explore()
    source = explorer.view("quaternary_structure")
    new = explorer.answer(TOPIC)
    selection = explorer.access.select(TOPIC)
    assert new.capabilities["save"] and selection.capabilities["save"]
    new.save(tmp_path / "human.json")
    selection.save(tmp_path / "agent.json")
    source.save(tmp_path / "source.json")
    retained = json.loads((tmp_path / "source.json").read_text(encoding="utf-8"))
    assert retained["format"] == "sabueso.card_exploration@4"
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.oligomer"), "oligomer_view", forbidden
    )
    saved = sabueso.read_exploration(tmp_path / "source.json")
    assert saved.explorer.answer(TOPIC).native_payload == new.native_payload
    assert saved.explorer.access.select(TOPIC).page()["outcome"]["status"] == "ok"
